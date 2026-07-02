---
title: Temporal
created: 2026-05-11
updated: 2026-06-28
type: entity
tags: [company, product, project, platform, saas, b2b, active]
sources:
  - https://github.com/temporalio/temporal
  - ~/Projects/temporal
confidence: high
---

# Temporal

> Temporal 是一个**持久化执行平台（Durable Execution Platform）**，源自 Uber Cadence 的分支，由 Temporal Technologies 开发。它让开发者能以代码定义 Workflow，由平台保证在进程崩溃、网络分区等故障下仍能正确执行，本质是用**事件溯源（Event Sourcing）** 实现分布式编排的可靠性。

---

## 核心价值主张

| 维度 | 说明 |
|------|------|
| **持久化执行** | Workflow 状态持久存储，进程崩溃后自动恢复，不丢进度 |
| **确定性重放** | 通过事件历史重放恢复 Workflow 状态，无需额外快照 |
| **语言无关** | SDK 支持 Go / Java / TypeScript / Python / PHP 等 |
| **水平扩展** | History Shard 分片机制支持百万级并发 Workflow |
| **可观测性** | Web UI + CLI 完整查看每个 Workflow 的事件历史 |

---

## 整体架构

Temporal 系统分为两层：**Temporal Cluster**（服务端）和 **User-hosted Processes**（用户侧 Worker）。

```
┌─────────────────────────────────────────────────────┐
│                   User Application                   │
│         (SDK → Start/Signal/Query Workflow)          │
└──────────────┬──────────────────────┬───────────────┘
               │ gRPC                 │ Long Poll
               ▼                      ▼
┌──────────────────────────────────────────────────────┐
│                  Temporal Cluster                     │
│                                                       │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐           │
│  │ Frontend │  │ History  │  │ Matching │           │
│  │ :7233    │  │ (sharded)│  │ :7235    │           │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘           │
│       │             │              │                  │
│  ┌────┴─────┐      │         ┌────┴─────┐           │
│  │ Internal │      │         │ Task     │           │
│  │ Worker   │      │         │ Queues   │           │
│  └──────────┘      │         └──────────┘           │
│                    ▼                                   │
│           ┌─────────────────┐                         │
│           │  Persistence    │                         │
│           │  (Cassandra /   │                         │
│           │   PostgreSQL /  │                         │
│           │   MySQL / SQLite)│                        │
│           └─────────────────┘                         │
└──────────────────────────────────────────────────────┘
```

---

## 四大核心服务

### 1. Frontend Service（端口 7233 gRPC / 7243 HTTP）

- **API 网关**：所有外部请求的统一入口
- 职责：认证/鉴权（JWT + ClaimMapper + Authorizer）、限流、路由
- 将请求转发到对应的 History / Matching 服务实例
- 暴露 Nexus HTTP 路由用于跨集群通信

### 2. History Service（核心，最复杂）

- **每个 Workflow Execution 的生命周期管理者**
- 两大职责：
  1. 处理来自用户或 Worker 的 RPC 请求（Start/Cancel/Signal/Complete 等）
  2. 异步处理内部队列任务（Transfer Queue / Timer Queue / Replication Queue）
- 通过 **History Shard** 实现水平扩展
- 每次请求 → 确定新的 History Events → 追加到事件历史 → 按需创建 Transfer/Timer 任务
- **Mutable State**：为每个 Workflow 维护内存中的状态摘要（进行中的 Activity、Timer、子 Workflow 等），持久化为单行记录

#### History Shard 机制

- 集群创建时确定 Shard 数量，**不可更改**
- Shard 通过 `ShardController` + Ringpop 成员协议分配给 History 实例
- 每个 Shard 管理多个内部队列（Transfer / Timer / Replication / Visibility）
- `RangeID`（单调递增代数）用于 fencing，防止脑裂

### 3. Matching Service（端口 7235）

- **任务调度器**：管理 Task Queue，将 Task 分发给 Worker
- Worker 通过 Frontend 发起 Long Poll → 路由到 Matching
- **Task Queue Partition**：默认 4 个分区，形成树状结构，支持任务/轮询者跨分区转发
- 调度两类任务：
  - **Workflow Task**：驱动 Workflow 代码执行（重放）
  - **Activity Task**：执行用户定义的 Activity 函数

### 4. Internal Worker Service

- 集群内部的 Worker 进程，处理系统级任务
- 包括：Timer 处理、Archive、Replication（多集群）、Batch 操作、Workflow Delete 等
- 本质上与用户的 Worker 使用相同的 SDK 框架

---

## 核心概念

### Workflow

- 用代码定义的业务流程，**必须确定性、无副作用**
- SDK 负责重放（Replay）事件历史来恢复执行状态
- 支持：Timer、Activity 调用、子 Workflow、Signal、Query、Update

### Activity

- 实际执行副作用的地方（API 调用、数据库写入等）
- 需满足**幂等性或不可重试**（至少一次或至多一次语义）
- 支持超时、重试策略、Heartbeat

### Task Queue

- Worker 通过 Task Queue Poll 获取任务
- 同一 Queue 可被多个 Worker 消费，实现负载均衡
- 支持优先级（Priority）和版本路由（Worker Versioning）

### Namespace

- 资源隔离单元，类似"租户"
- 每个 Namespace 独立的 Workflow ID 空间、Retention 策略、安全配置

### Event Sourcing

- Workflow 的所有状态变更以**不可变事件序列**存储
- 状态 = f(初始状态, 事件序列) —— 完全可通过重放重建
- 事件类型：WorkflowExecutionStarted、WorkflowTaskScheduled、ActivityTaskCompleted 等

---

## 数据流：一个典型 Workflow 的执行

以伪代码 `myWorkflow() { result = callActivity(myActivity); return result; }` 为例：

```
1. StartWorkflowExecution
   App → Frontend → History → Persistence
   事件: [WorkflowExecutionStarted, WorkflowTaskScheduled]
   创建 Transfer Task (Workflow Task)

2. Worker Poll + 执行 Workflow Task
   Worker → Frontend → Matching → PollWorkflowTask
   Matching → History → RecordWorkflowTaskStarted
   Worker 收到事件历史 → 重放 → 遇到 callActivity → 阻塞
   Worker → History → RespondWorkflowTaskCompleted(ScheduleActivity)
   事件追加: [WorkflowTaskCompleted, ActivityTaskScheduled]
   创建 Transfer Task (Activity Task)

3. Worker 执行 Activity
   Worker → Matching → PollActivityTask → 执行 → 完成
   Worker → History → RespondActivityTaskCompleted
   事件追加: [ActivityTaskCompleted, WorkflowTaskScheduled]
   创建 Transfer Task (新的 Workflow Task)

4. Worker 完成 Workflow
   Worker 重放 → 无更多调用 → return result
   事件追加: [WorkflowTaskCompleted, WorkflowExecutionCompleted]
```

---

## 持久化层

### 支持的数据库

| 数据库 | 用途 | 状态 |
|--------|------|------|
| **Cassandra** | 最早支持，历史最久 | 生产就绪 |
| **PostgreSQL** | 广泛使用 | 生产就绪 |
| **MySQL** | 广泛使用 | 生产就绪 |
| **SQLite** | 开发/测试用 | `temporal server start-dev` 默认 |
| **Elasticsearch** | 高级 Visibility 查询 | 可选 |

### 关键表结构（以 SQL 为例）

```sql
-- Shard 元数据
shards (shard_id, range_id, data, data_encoding)

-- Workflow 执行记录（核心表）
executions (shard_id, namespace_id, workflow_id, run_id,
            next_event_id, data, state, ...)

-- 当前执行索引（快速查找 "某 workflow 的最新 run"）
current_executions (shard_id, namespace_id, workflow_id,
                    run_id, state, status, ...)

-- 事件历史（Cassandra 版本，使用 tree + branch + node 模型）
history_node (tree_id, branch_id, node_id, txn_id, data, ...)
```

### 两个数据库

- **Default Store**：存储 Workflow 执行数据（事件历史、Mutable State）
- **Visibility Store**：存储 Workflow 列表查询索引（用于 UI 搜索/过滤）

---

## 项目结构

```
temporal/
├── api/                  # 公共 API proto 定义 + 生成的 Go 代码
├── chasm/                # CHASM 框架（Coordinated Heterogeneous ASM）
├── client/               # 服务间通信客户端库
│   ├── frontend/         # Frontend 客户端
│   ├── history/          # History 客户端
│   ├── matching/         # Matching 客户端
│   └── admin/            # Admin 客户端
├── cmd/                  # 入口程序
│   └── server/main.go    # temporal-server 主程序
├── common/               # 跨服务共享模块
│   ├── persistence/      # 持久化抽象层（接口 + 多 DB 实现）
│   ├── dynamicconfig/    # 动态配置（运行时修改，无需重启）
│   ├── membership/       # 集群成员管理（Ringpop）
│   ├── metrics/          # Prometheus / OpenTelemetry 指标
│   ├── namespace/        # Namespace 缓存
│   ├── nexus/            # Nexus RPC 集成
│   └── ...
├── components/           # Nexus 组件
├── config/               # 配置模板（development.yaml 等）
├── docs/                 # 文档
│   └── architecture/     # 架构文档（History/Matching/Workflow Lifecycle）
├── proto/                # 内部服务 proto 定义
├── schema/               # 数据库 Schema
│   ├── cassandra/        # Cassandra CQL
│   ├── postgresql/       # PostgreSQL SQL
│   ├── mysql/            # MySQL SQL
│   └── sqlite/           # SQLite SQL
├── service/              # 四大核心服务实现
│   ├── frontend/
│   ├── history/          # 最大最复杂（含 API handler、Queue Processor、Workflow State Machine）
│   ├── matching/
│   └── worker/
└── temporal/             # Server 组装层（DI via go.uber.org/fx）
```

---

## 技术栈

| 分类 | 技术 |
|------|------|
| 语言 | **Go 1.26** |
| 通信协议 | **gRPC** + Protobuf，HTTP/2（grpc-gateway） |
| 依赖注入 | **go.uber.org/fx** |
| 日志 | **go.uber.org/zap** |
| 指标 | **Prometheus** + OpenTelemetry |
| 成员协议 | **Ringpop**（基于 SWIM 的 gossip 协议） |
| CLI 框架 | **urfave/cli/v2** |
| 测试 | **testify**（require > assert）、mock（go.uber.org/mock） |
| CI | GitHub Actions，Buf（proto lint + breaking change） |

---

## 构建与测试

```bash
# 构建
make install          # 编译所有二进制
make bins             # 编译 temporal-server 等二进制
make proto            # 重新生成 proto 代码

# 测试
make unit-test        # 单元测试（-tags test_dep -race -shuffle）
make lint-code        # 代码检查

# 本地开发
temporal server start-dev   # SQLite 内存模式，零依赖启动
```

---

## 新兴特性

### CHASM（Coordinated Heterogeneous Application State Machines）

- 新一代 Workflow 引擎框架，位于 `/chasm`
- 概念：**Application State Machine (ASM)** = 注册表 + 库 + 组件类型 + 任务 + 字段
- 目标：替代传统 Workflow 的某些场景，提供更灵活的状态机抽象

### Nexus

- 跨集群/跨服务的 RPC 调用框架
- Frontend 暴露 HTTP 路由：`/nexus/endpoints/{id}/services`
- 支持 Callback 完成异步操作
- 基于 nexus-rpc/sdk-go

---

## 生态系统

| 组件 | 说明 |
|------|------|
| **Temporal CLI** | `temporal` 命令行工具，替代旧版 tctl |
| **Web UI** | 默认 :8233，可视化 Workflow 执行 |
| **SDK** | Go / Java / TypeScript / Python / PHP，定义 Workflow + Activity |
| **Temporal Cloud** | 托管服务，免运维 |
| **Temporalite** | 单进程版本（已合并到 CLI 的 `start-dev`） |
| **docker-compose** | 官方 docker-compose.template.yaml 用于本地开发 |

---

## 关键设计决策与权衡

1. **Event Sourcing vs 状态快照**：选择事件溯源，优势是完整审计追踪，代价是长时间运行的 Workflow 事件历史膨胀（需 Continues-As-New 截断）
2. **确定性要求**：Workflow 代码必须确定性，SDK 通过拦截非确定性操作来保证。代价是编程模型受限
3. **Shard 数量不可变**：集群创建时固定，扩展需新集群 + 迁移
4. **用户侧执行**：Activity/Workflow 代码在用户进程中运行，Cluster 不执行用户代码，安全且灵活
5. **Cassandra 优先设计**：持久化层接口偏向 Cassandra 的数据模型（宽行、分区键），SQL 实现做适配

---

## 最新动态：Replay 2026（截至 2026-06-28）

> [!note] 从"工作流引擎"转向"Durable Execution for AI"
> Temporal 在 Replay 2026 大会宣布 **Serverless Workers、Standalone Activities、Workflow Streams**，并把 durable execution 明确定位为 **AI agent 的可靠性基础设施**。

### Replay 2026 核心发布

| 新能力 | 意义 |
|--------|------|
| **Serverless Workers** | 无需自管 worker，降低运维门槛（CEO Samar Abbas 主推）|
| **Standalone Activities** | 活动可独立于 workflow 运行，更灵活的组合 |
| **Workflow Streams** | 流式数据处理，适配 AI agent 的流式交互 |
| **Temporal Nexus GA** | 跨 namespace 连接，支持分布式 agent 协作 |

### 战略转向：Durable Execution for AI
- 官方叙事从"工作流编排"升级为 **"Durable Execution = crash-proof execution for AI agents"**
- CTO Maxim Fateev 强调 serverless + workflow streams 是为 AI 场景设计
- 让 Temporal 成为 [[automaton]]、[[ruflo]] 等 long-running agent 的潜在可靠性底座

### 生态信号
- Reddit/LinkedIn 社区讨论"durable execution changes everything"持续发热
- 2026-01 Nexus GA 后，跨组织 agent 协作场景案例增加

## 相关链接

- 官方文档: https://docs.temporal.io/
- GitHub: https://github.com/temporalio/temporal
- 社区论坛: https://community.temporal.io
- 架构文档: https://github.com/temporalio/temporal/tree/main/docs/architecture
