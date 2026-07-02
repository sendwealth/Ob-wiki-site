# Temporal 项目亮点分析

> Temporal 是一个开源的 **durable execution platform**（持久化执行平台），用于构建可靠的大规模分布式应用。
> 项目使用 Go 语言编写，约 2653 个 Go 源文件，是一个工业级的 Go 项目典范。

---

## 1. 依赖注入：Uber FX 框架

**文件**: `service/fx.go`

Temporal 使用 Uber 的 [FX](https://pkg.go.dev/go.uber.org/fx) 框架做依赖注入，而不是手动管理依赖关系。

```go
// 通过 struct tag 声明依赖
type GrpcServerOptionsParams struct {
    fx.In  // FX 自动注入所有字段

    Logger                  log.Logger
    RPCFactory              common.RPCFactory
    ServiceErrorInterceptor *interceptor.ServiceErrorInterceptor
    // optional 表示可选依赖
    AdditionalInterceptors  []grpc.UnaryServerInterceptor `optional:"true"`
}

// 通过 fx.Out 声明产出
type PersistenceRateLimitingParams struct {
    fx.Out
    PersistenceMaxQps          persistenceClient.PersistenceMaxQps
    PersistenceNamespaceMaxQps persistenceClient.PersistenceNamespaceMaxQps
}
```

**学习价值**：
- `fx.In` / `fx.Out` 用 struct tag 声明依赖图
- `optional:"true"` 处理可选依赖
- 模块化组织：`fx.Options`, `fx.Provide`, `fx.Invoke`

---

## 2. Goroutine 安全管理：goro 包

**文件**: `common/goro/goro.go`

原生 `go func()` 的问题是：无法优雅停止、无法获取错误、无法等待完成。Temporal 封装了 `goro.Handle` 解决这些问题。

```go
// 创建一个可管理的 goroutine handle
handle := goro.NewHandle(ctx)

// 启动 goroutine（只能调用一次）
handle.Go(func(ctx context.Context) error {
    // 业务逻辑...
    // ctx 被 cancel 时应主动退出
    return nil
})

// 优雅停止：请求取消（非强制杀死）
handle.Cancel()

// 等待完成
<-handle.Done()

// 获取错误
if err := handle.Err(); err != nil { ... }
```

**设计亮点**：
- `NewHandle` 和 `Go` 分离 —— 可以先存 handle 再启动，避免 goroutine 自引用的竞态
- `Cancel()` 是协作式的（cancel context），不是强制 kill
- `Done()` channel 允许外部阻塞等待
- 使用 `atomic.Value` 存储错误，线程安全

---

## 3. 泛型 Future 类型

**文件**: `common/future/future.go`

极简的 Future/Promise 抽象，利用 Go 1.18+ 泛型：

```go
type Future[T any] interface {
    Get(ctx context.Context) (T, error)  // 阻塞获取结果
    Ready() bool                          // 非阻塞检查是否完成
}
```

**学习价值**：Go 泛型接口的标准写法，简单但实用。

---

## 4. 流式批处理器：stream_batcher

**文件**: `common/stream_batcher/batcher.go`

一个优雅的泛型批处理器，将并发到达的单个请求聚合成批量处理：

```go
type Batcher[T, R any] struct {
    fn         func([]T) R          // 批处理函数
    submitC    chan batchPair[T, R]  // 提交 channel
    running    atomic.Pointer[chan struct{}]  // goroutine 状态
}
```

**核心设计**：
- **惰性启动**：没有请求时 goroutine 不运行（`running == nil`），有请求时用 `CompareAndSwap` 竞争启动
- **自动关闭**：`IdleTime` 后 goroutine 自动退出，节省资源
- **背压控制**：`Add()` 会阻塞直到批处理完成
- **可测试**：注入 `clock.TimeSource`，不用 `time.Sleep`

**学习价值**：
- `atomic.Pointer` 的 CAS 操作实现无锁状态机
- Channel + goroutine 的生产者-消费者模式
- 泛型 channel `chan batchPair[T, R]`

---

## 5. 时钟抽象：可测试的时间

**文件**: `common/clock/`

Temporal 从不直接使用 `time.Now()` 或 `time.AfterFunc()`，而是全部通过 `TimeSource` 接口：

```go
type TimeSource interface {
    Now() time.Time
    AfterFunc(d time.Duration, f func()) Timer
    // ...
}
```

生产环境用 `RealTimeSource`，测试用 `EventTimeSource`（手动推进时间）。

还封装了与 TimeSource 配合的 context timeout：

```go
// 替代 context.WithTimeout，使用自定义时钟
ctx, cancel := clock.ContextWithTimeout(ctx, time.Second, timeSource)
```

**学习价值**：这是 Go 测试的经典技巧 —— 把时间做成依赖，测试完全可控。

---

## 6. 分片架构（Sharding）

**文件**: `service/history/shard/controller.go`

Temporal 使用分片来水平扩展 history 服务：

```go
type Controller interface {
    GetShardByID(shardID int32) (historyi.ShardContext, error)
    GetShardByNamespaceWorkflow(namespaceID namespace.ID, workflowID string) (historyi.ShardContext, error)
    CloseShardByID(shardID int32)
    ShardIDs() []int32
    Start()
    Stop()
    InitialShardsAcquired(context.Context) error  // 阻塞等待初始分片获取完成
}
```

**设计模式**：
- 通过 `namespaceID + workflowID` 哈希到分片
- 分片可以在节点间迁移（`CloseShardByID` + 重新获取）
- `InitialShardsAcquired` 保证启动后状态一致

---

## 7. 事件溯源（Event Sourcing）

**文件**: `service/history/history_engine.go`

Temporal 的核心是事件溯源模式 —— workflow 的状态通过一系列不可变事件重建：

```go
type historyEngineImpl struct {
    shardContext               historyi.ShardContext
    executionManager           persistence.ExecutionManager
    queueProcessors            map[tasks.Category]queues.Queue
    replicationAckMgr          replication.AckManager
    eventNotifier              events.Notifier
    // ...
}
```

**架构亮点**：
- 所有状态变更以事件形式追加（append-only）
- 通过重放事件重建当前状态
- 天然支持时间旅行和审计

---

## 8. 丰富的任务类型系统

**文件**: `service/history/tasks/`

Temporal 定义了精细的任务分类，每种任务有独立的处理逻辑：

```
activity_task.go          - Activity 执行任务
workflow_task.go          - Workflow 决策任务
user_timer.go             - 用户定时器
workflow_run_timer.go     - 运行超时定时器
close_task.go             - 关闭 workflow
signal_task.go            - 信号投递
child_workflow_task.go    - 子 workflow
reset_task.go             - 重置任务
state_machine_task.go     - 状态机任务
chasm_task.go             - Chasm 引擎任务
```

**学习价值**：用类型系统而不是字符串/枚举来区分任务，编译器保证完备性。

---

## 9. gRPC 拦截器链

**文件**: `common/rpc/interceptor/`

Temporal 构建了完善的 gRPC 中间件链：

```
service_error_interceptor   - 统一错误处理
telemetry.go                - 遥测追踪
rate_limit.go               - 全局限流
namespace_rate_limit.go     - 命名空间级限流
namespace.go                - 命名空间验证
redirection.go              - 请求路由
health_check.go             - 健康检查
sdk_version.go              - SDK 版本检查
slow_request_logger.go      - 慢请求日志
concurrent_request_limit.go - 并发请求限制
routing_key_interceptor.go  - 路由键提取
```

**设计模式**：责任链模式，每个拦截器关注一个横切面。

---

## 10. 谓词（Predicate）系统

**文件**: `common/predicates/predicates.go`

```go
type Predicate[T any] interface {
    Test(T) bool                 // 测试是否满足条件
    Equals(Predicate[T]) bool   // 结构化相等比较
    Size() int                   // 估算内存大小
}
```

**学习价值**：泛型接口 + 组合模式，可以构建复杂的过滤条件链。

---

## 11. 多数据中心复制引擎

**文件**: `service/history/replication/`

支持全球多数据中心部署的关键组件：

```
bi_direction_stream.go     - 双向流式复制
task_processor.go          - 复制任务处理
ack_manager.go             - 确认管理器
dlq_handler.go             - 死信队列
progress_cache.go          - 进度缓存
stream_sender.go           - 发送端流控
stream_receiver.go         - 接收端流控
```

**亮点**：双向流 + 流控 + 死信队列 + 进度缓存，是分布式系统复制的教科书实现。

---

## 12. 分层状态机（HSM）

**文件**: `service/history/hsm/`

```
sm.go          - 状态机核心
tree.go        - 状态树（层级结构）
registry.go    - 状态注册表
executor.go    - 状态执行器
events.go      - 状态转换事件
tasks.go       - 状态机触发的任务
```

**学习价值**：层级状态机（Hierarchical State Machine）是复杂状态管理的工业解法。

---

## 总结：从 Temporal 学到的 Go 工程实践

| 模式 | 位置 | 核心思想 |
|------|------|----------|
| 依赖注入 | `service/fx.go` | Uber FX，声明式依赖管理 |
| Goroutine 管理 | `common/goro/` | Handle 封装，优雅启停 |
| 泛型工具 | `common/future/` | 泛型接口的标准写法 |
| 批处理 | `common/stream_batcher/` | 惰性启动 + CAS 无锁 |
| 时钟抽象 | `common/clock/` | 控制时间，测试友好 |
| 分片 | `service/history/shard/` | 水平扩展的基础 |
| 事件溯源 | `service/history/` | append-only 事件重建状态 |
| 拦截器链 | `common/rpc/interceptor/` | gRPC 中间件责任链 |
| 多活复制 | `service/history/replication/` | 双向流 + 流控 + DLQ |
| 状态机 | `service/history/hsm/` | 层级状态管理 |

---

## 推荐阅读顺序（作为 Go 初学者）

1. `common/goro/goro.go` — 学习 goroutine 管理（最简单）
2. `common/future/future.go` — 学习 Go 泛型接口
3. `common/clock/` — 学习接口抽象和可测试设计
4. `common/predicates/predicates.go` — 学习泛型 + 接口组合
5. `common/stream_batcher/batcher.go` — 学习 channel + 并发模式
6. `service/fx.go` — 学习依赖注入和模块化
7. `service/history/tasks/` — 学习类型系统设计
8. `service/history/replication/` — 学习分布式系统模式
