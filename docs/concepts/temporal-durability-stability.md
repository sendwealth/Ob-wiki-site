---
title: Temporal 稳定性与持久性实现机制分析
created: 2026-05-15
updated: 2026-05-15
type: concept
tags: [temporal, durability, stability, distributed-systems, event-sourcing, go]
sources:
  - https://github.com/temporalio/temporal
  - ~/Projects/temporal
confidence: high
related:
  - "[[temporal]]"
  - "[[opensource-project-practices-from-temporal]]"
---

# Temporal 稳定性与持久性实现机制分析

> 从代码层面分析 Temporal 如何保证 Workflow 状态永不丢失（持久性）和系统持续可靠运行（稳定性）。分析基于 `temporalio/temporal` 仓库源码。

---

## 整体架构：持久性与稳定性的协同

```
用户请求
    │
    ▼
Frontend (限流、认证)
    │
    ▼
History Service
    │
    ├─ ShardController ──── ownership (验证归属)
    │       │                    │
    │       ▼                    ▼
    │   ShardContext ──── RangeID (防脑裂)
    │       │
    │       ▼
    │   加载 MutableState (从事件历史重建)
    │       │
    │       ▼
    │   执行状态变更
    │       │
    │       ▼
    │   PersistenceRetryableClient (自动重试)
    │       │
    │       ▼
    │   原子写入: 事件 + MutableState + Queue Tasks
    │
    ├─ Queue Processor (Transfer/Timer/Replication)
    │       │
    │       ▼
    │   异步处理内部任务
    │
    └─ Rate Limiter (多层限流保护)
```

---

## 一、持久性（Durability）：状态永不丢失

### 1.1 Event Sourcing — 事件溯源

核心思路：**不保存状态，只保存事件**。所有 Workflow 状态变更以不可变事件序列追加到数据库。

```
WorkflowExecutionStarted → WorkflowTaskScheduled → WorkflowTaskCompleted
→ ActivityTaskScheduled → ActivityTaskCompleted → WorkflowExecutionCompleted
```

**实现位置**：`common/persistence/execution_manager.go` → `ExecutionManager` 接口

**关键设计**：

| 机制 | 说明 |
|------|------|
| 追加写入 | 事件只追加（append-only），不修改，不删除 |
| 树状分支 | `tree_id + branch_id + node_id` 结构，支持 Fork/Reset |
| 完整性校验 | `errNonContiguousEventID`、`errWrongVersion` 保证事件序列连续 |
| 历史分支 | `ForkHistoryBranch` 支持从任意节点分叉（用于 Reset 和 Continue-As-New） |

**事件分支结构**：

```go
// ForkHistoryBranch forks a new branch from an old branch
func (m *executionManagerImpl) ForkHistoryBranch(
    request *ForkHistoryBranchRequest,
) (*ForkHistoryBranchResponse, error) {
    newAncestors := make([]*persistencespb.HistoryBranchRange, 0)
    // 新分支继承旧分支的祖先范围
    // 新写入的事件只属于新分支
}
```

**数据模型**：

```
History Tree
├── Branch A (原始执行)
│   ├── Node 1: WorkflowExecutionStarted
│   ├── Node 2: WorkflowTaskCompleted
│   └── Node 3: ActivityTaskCompleted
└── Branch B (Reset 后的新执行，从 Node 2 分叉)
    ├── Ancestor: Branch A [Node 1, Node 2]
    ├── Node 4: WorkflowTaskCompleted (新的)
    └── Node 5: ActivityTaskScheduled (不同的路径)
```

### 1.2 Mutable State — 可变状态

每个 Workflow 在内存中维护一份**状态摘要**，包含：
- 进行中的 Activity 列表
- 待触发的 Timer
- 子 Workflow 状态
- 下一个 Event ID

**更新规则**：每次操作 → 追加事件 → 更新 MutableState → **一起持久化**（原子操作）

```
操作请求
    │
    ▼
生成新 History Events
    │
    ▼
更新 MutableState（内存）
    │
    ▼
原子写入数据库：
  ├── 事件历史（追加）
  ├── MutableState（覆盖更新）
  └── Queue Tasks（新任务）
    │
    ▼
全部成功 or 全部失败
```

### 1.3 Persistence Retryable Client — 持久化层自动重试

`common/persistence/persistence_retryable_clients.go` 为每个 Persistence Manager 包装了重试层：

```go
type executionRetryablePersistenceClient struct {
    persistence ExecutionManager
    policy      backoff.RetryPolicy    // 指数退避策略
    isRetryable backoff.IsRetryable    // 判断哪些错误可重试
}
```

**覆盖范围**：所有 7 个存储接口

| 接口 | 职责 |
|------|------|
| `ShardManager` | 分片元数据 |
| `ExecutionManager` | 工作流执行数据 |
| `TaskManager` | 内部任务 |
| `MetadataManager` | 命名空间等元数据 |
| `ClusterMetadataManager` | 集群配置 |
| `Queue` | 队列存储 |
| `NexusEndpointManager` | Nexus 端点 |

**重试策略**（`common/backoff/retry.go`）：

```go
// ThrottleRetry: 区分普通错误和资源耗尽错误
func ThrottleRetryContext(...) error {
    // 普通错误 → 按配置策略重试
    // 资源耗尽（ResourceExhausted）→ 独立 throttle 策略
    //   初始间隔: 1s, 最大间隔: 10s, 无过期时间
    // Context 取消 → 永不重试
}
```

### 1.4 Continue-As-New — 历史截断

长时间运行的 Workflow 事件历史会膨胀。

**解决方案**：
- Workflow 代码调用 `Continue-As-New`，以当前输入启动**全新 Run**
- 新 Run 拥有干净的事件历史
- 旧 Run 保留用于审计，但不再增长
- `service/history/ndc/workflow_resetter.go` 处理跨 Run 的事件重放

**典型场景**：
```
Run 1: 100,000 个事件（接近上限）
    │
    ▼ Continue-As-New
Run 2: 从 0 开始计数
    │     └── 继承 Run 1 的最终状态
    ▼
Run 3: ...
```

### 1.5 Workflow Reset — 状态回滚

`service/history/handler.go` → `ResetWorkflowExecution`

- 从某个历史事件点 fork 出新分支
- 支持重新执行某个时间点之后的逻辑
- 用于修复 bug 后恢复 Workflow
- `workflow_rebuilder.go` → `replayResetWorkflow` 负责重建

---

## 二、稳定性（Stability）：系统持续可靠运行

### 2.1 Shard 分片 + RangeID 防脑裂

**核心代码**：`service/history/shard/`

#### ShardController

管理本节点拥有的所有 Shard：

```go
type ControllerImpl struct {
    sync.RWMutex
    historyShards map[int32]historyi.ControllableContext  // 持有的分片
    ownership     *ownership                              // 所有权验证
    lingerState   struct {
        shards map[historyi.ControllableContext]struct{}  // 延迟关闭的分片
    }
}
```

#### Ownership 监听成员变更

```go
func (o *ownership) eventLoop(ctx context.Context) {
    acquireTicker := time.NewTicker(o.config.AcquireShardInterval())
    for {
        select {
        case <-acquireTicker.C:              // 定时检查
            o.scheduleAcquire()
        case changedEvent := <-o.membershipUpdateCh:  // 成员变更
            o.scheduleAcquire()              // 触发分片重新分配
        }
    }
}
```

#### Fencing 机制

每个 Shard 有一个 **RangeID**（单调递增代数）：

```
节点 A 拥有 Shard 5 (RangeID=100)
    │
    ├── 节点 A 宕机
    │
    ▼
节点 B 接管 Shard 5 → RangeID 递增到 101
    │
    ├── 节点 A 恢复，尝试写入 Shard 5
    │   └── RangeID=100 < 101 → 写入被拒绝 ✗
    │
    └── 节点 B 正常写入
        └── RangeID=101 匹配 → 写入成功 ✓
```

#### verifyOwnership 验证归属

```go
func (o *ownership) verifyOwnership(shardID int32) error {
    ownerInfo, err := o.historyServiceResolver.Lookup(convert.Int32ToString(shardID))
    hostInfo := o.hostInfoProvider.HostInfo()
    if ownerInfo.Identity() != hostInfo.Identity() {
        return serviceerrors.NewShardOwnershipLost(ownerInfo.Identity(), hostInfo.GetAddress())
    }
    return nil
}
```

### 2.2 多层 Rate Limiting

`common/dynamicconfig/constants.go` 定义了细粒度的限流配置：

#### 限流层级

| 层级 | 配置项 | 说明 |
|------|--------|------|
| 全局 | `FrontendGlobalRPS` | 整个集群总 RPS |
| 实例 | `FrontendRPS` | 单节点 RPS |
| 命名空间 | `FrontendMaxNamespaceRPSPerInstance` | 租户级 RPS |
| 突发 | `FrontendMaxNamespaceBurstRatioPerInstance` | 突发流量比例 |
| 运维 | `OperatorRPSRatio` | 运维操作占总 RPS 比例 |
| Scavenger | `BuildIdScavengerVisibilityRPS` | 后台清理任务 RPS |

#### 限流实现

```go
// 使用 golang.org/x/time/rate 实现令牌桶限流
// 使用 golang.org/x/sync/semaphore 控制并发数
```

所有参数通过 **Dynamic Config** 管理，运行时修改，无需重启。

### 2.3 Queue Processor — 任务队列处理框架

`service/history/queues/queue_base.go` 实现了通用任务处理器：

#### 四大内部队列

| 队列 | 职责 |
|------|------|
| Transfer Queue | Workflow Task 分发、Activity Task 分发 |
| Timer Queue | 定时器触发 |
| Replication Queue | 跨集群复制 |
| Visibility Queue | 可见性索引更新 |

#### 稳定性设计

```go
const (
    DefaultReaderId        = common.DefaultQueueReaderID
    maxPendingTaskMultiplier = 0.8    // 非 default reader 的任务量乘数
    minMaxPendingTaskCount  = 1000    // 最小最大待处理任务数
    queueIOTimeout          = 5s      // IO 超时，防止阻塞
    forceNewSliceDuration   = 5min    // 强制新切片，防止无限增长
)
```

关键机制：
- **Reader Scope 分片读取**：每个 Reader 管理一个范围的任务，支持并行处理
- **强制新切片**：每 5 分钟强制创建新 slice，防止单个 slice 无限增长
- **动态调整**：待处理任务数根据 reader ID 动态调整
- **超时保护**：所有 IO 操作有 5s 超时

### 2.4 Graceful Shutdown + Linger

`service/history/shard/controller_impl.go` → `shardLingerThenClose`

```go
const shardLingerMaxTimeLimit = 1 * time.Minute

// 节点放弃 Shard 所有权时，不立即关闭，而是延迟
func (c *ControllerImpl) shardLingerThenClose(ctx context.Context, shardID int32) {
    if !c.beginLinger(shard) { return }
    defer c.endLinger(shard)
    c.doLinger(ctx, shard)  // 最多延迟 1 分钟
}
```

**目的**：集群成员变更时（扩容、缩容、节点故障），给新 Owner 充足时间完成接管，避免正在处理的任务丢失。

### 2.5 Membership + Ringpop — 成员管理

`common/membership/` 基于 SWIM gossip 协议：

| 机制 | 说明 |
|------|------|
| 心跳检测 | 定期探测其他节点存活状态 |
| 成员变更 | 自动检测节点加入/离开 |
| 分片定位 | `Lookup(shardID)` 查找 Shard 当前归属 |
| 所有权验证 | `verifyOwnership` 确认操作权限 |
| 故障转移 | 节点宕机 → 成员更新 → Shard 自动重新分配 |

### 2.6 Dynamic Config — 运行时动态配置

所有限流参数、超时参数、功能开关都通过 Dynamic Config 管理：

- 支持数据库、文件、环境变量等多种来源
- **运行时修改，无需重启**
- 支持全局配置和命名空间级别配置
- 典型配置：

```go
FrontendRPS                          = NewGlobalIntSetting("frontend.rps", ...)
FrontendMaxNamespaceRPSPerInstance   = NewNamespaceIntSetting("frontend.namespaceRPS", ...)
HistoryRPS                           = NewGlobalIntSetting("history.rps", ...)
PersistenceMaxQPS                    = NewGlobalIntSetting("persistenceMaxQPS", ...)
```

---

## 三、核心机制总结

### 持久性保证链

```
Event Sourcing (不可变事件)
    + Mutable State (原子更新)
    + Persistence Retry (自动重试)
    + Continue-As-New (历史截断)
    + Workflow Reset (状态回滚)
    = 状态永不丢失
```

### 稳定性保证链

```
Shard + RangeID (防脑裂)
    + Membership (自动故障转移)
    + Multi-layer Rate Limiting (过载保护)
    + Queue Processor (异步任务处理)
    + Graceful Shutdown + Linger (优雅关闭)
    + Dynamic Config (运行时调整)
    = 系统持续可靠运行
```

### 两者协同

持久性和稳定性通过以下机制串联：
1. **PersistenceRetryableClient** — 即使存储层暂时不可用，重试机制也能保证最终一致
2. **RangeID Fencing** — 节点故障转移时，新 Owner 的写入不会被旧 Owner 覆盖
3. **Graceful Linger** — Shard 迁移期间，旧 Owner 延迟关闭，新 Owner 完全接管后才释放
4. **Dynamic Config** — 发现问题后可运行时调整限流参数，无需重启服务
