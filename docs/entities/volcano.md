---
title: Volcano
created: 2026-08-03
updated: 2026-08-03
type: entity
tags: [project, platform, ai, scheduling, kubernetes, batch, cncf]
sources: [https://github.com/volcano-sh/volcano, ~/Projects/volcano]
confidence: high
---

# Volcano
> Kubernetes 原生的批量调度系统（CNCF 孵化项目），在 kube-batch 基础上演进而来，为 AI/ML、大数据、高性能计算等批处理工作负载提供 gang scheduling、队列管理、公平share、抢占回填等 kube-scheduler 不具备的能力。

---

## 核心价值主张

| 维度 | 说明 |
|------|------|
| 解决什么问题 | 原生 kube-scheduler 面向无状态长服务，对"全部起或全部不起"的批处理作业（训练任务、Spark/Flink 批作业）缺乏 gang 调度、队列权重、抢占回收等能力，容易造成死锁与资源浪费 |
| 定位 | K8s 原生 batch scheduling 系统，扩展 kube-scheduler 调度框架，作为独立调度器（schedulerName: volcano）运行 |
| 核心能力 | Gang scheduling（minAvailable 全或无）、多级队列与权重 fair-share（DRF/proportion）、抢占与回收（preempt/reclaim/backfill）、拓扑感知（NUMA/HyperNode/网络拓扑）、Job 生命周期管理（maxRetry/事件策略） |
| 谁在用 | 华为（发起方）、Spark/Flink/Ray/TensorFlow/PyTorch/MindSpore/PaddlePaddle/MPI/Horovod 等主流 AI/数据生态均有官方或社区集成 |
| 成熟度 | CNCF 孵化项目，模块 `volcano.sh/volcano`，Go 1.26，Helm 官方 chart，生产级 |

## 整体架构

```
                        ┌─────────────────────────────────────┐
                        │          Kubernetes API             │
                        │   (Pod / PodGroup / Queue / Job)     │
                        └───────────┬──────────┬──────────┬───┘
                                    │          │          │
                  watch CRD/Pod     │          │ watch    │ watch
                                    ▼          ▼          ▼
   ┌──────────────────────┐  ┌──────────────┐ ┌───────────────┐ ┌────────────────┐
   │  vc-scheduler        │  │ vc-controller│ │ vc-webhook   │ │ vc-agent /     │
   │  (schedulerName=     │  │ -manager     │ │ -manager     │ │ vc-agent-      │
   │   volcano)           │  │ (job/pg/     │ │ (mutating/   │ │ scheduler      │
   │                      │  │  queue/jobflow│ │  validating │ │ + network-qos) │
   │  Session 每 1s 开启   │  │  cron/gc/    │ │  Job/PG/     │ │ (节点侧 NUMA/  │
   │  Actions 流水线执行   │  │  hypernode/  │ │  Queue CRD)  │ │ 网络QoS上报)    │
   │  Plugins 注入策略     │  │  sharding/   │ │              │ │                │
   │                      │  │  colocation) │ │              │ │                │
   └──────────┬───────────┘  └──────────────┘ └───────────────┘ └────────────────┘
              │ 绑定 Pod → Node
              ▼
        ┌──────────────────┐
        │  Cluster Nodes   │
        │  (kubelet)       │
        └──────────────────┘

  ── 自定义资源 (CRDs) ─────────────────────────────────────────
   batch.volcano.sh/      Job, CronJob, JobFlow, JobTemplate
   scheduling.volcano.sh/  PodGroup, Queue
   bus.volcano.sh/         Command
   nodeinfo.volcano.sh/    NUMATopology
   topology.volcano.sh/    HyperNode
   shard.volcano.sh/       NodeShard
   config.volcano.sh/      ColocationConfiguration
```

调度器是核心：以 **Session** 为调度单位（默认每 1 秒开启一次），Session 内持有 Queues / JobsMap / PendingTasks / NodeList 的本地快照，按配置的 **Actions** 流水线（enqueue → allocate → backfill → preempt → reclaim …）依次执行，每个 Action 调用注册的 **Plugins** 完成过滤、评分、抢占决策。

## 核心服务 / 组件

### 1. vc-scheduler（调度器）
- 入口 `cmd/scheduler`，结构体 `pkg/scheduler/scheduler.go:Scheduler` 持有 cache、schedulerConf、fileWatcher、schedulePeriod、`actions []framework.Action`、`plugins []conf.Tier`、schGateManager
- **热加载**：`NewScheduler` 通过 filewatcher 监听 scheduler config 变化，不停机调整 actions/plugins
- **Session 机制**（`pkg/scheduler/framework/session.go`）：每个调度周期 `Open()` 一次，从 cache 拷贝快照，执行 actions，`Close()` 回写。隔离周期内状态，避免长锁
- **Action 流水线**（`pkg/scheduler/actions/`）：
  | Action | 作用 |
  |--------|------|
  | `enqueue` | 把满足条件的 PodGroup 加入待调度队列 |
  | `allocate` | 主调度：对 pending task 做 predicate + scoring + 绑定（pipeline 预分配） |
  | `backfill` | 填补空闲资源，给低优先级/可延迟任务 |
  | `preempt` | 抢占：高优 task 抢低优 task 资源（满足 minAvailable） |
  | `reclaim` | 回收：队列权重失衡时跨队列回收 |
  | `gangpreempt` / `gangreclaim` | 面向 gang 调度的抢占/回收（按 PodGroup 整组操作） |
  | `shuffle` | 重排，打散堆积 |

### 2. vc-controller-manager（控制器集合）
位于 `pkg/controllers/`，多控制器共享 cache 与 framework：
| 控制器 | 职责 |
|--------|------|
| `job` | 解析 Job spec.tasks → 创建 Pod，设 OwnerReference，处理 maxRetry/事件策略 |
| `podgroup` | 维护 PodGroup 状态（minMember 满足度、queue 归属） |
| `queue` | Queue 状态机、权重/层级管理、reclaimable 标志 |
| `jobflow` / `jobtemplate` | JobFlow 编排多 Job 依赖（DAG），复用 JobTemplate |
| `cronjob` | 定时触发 Job |
| `garbagecollector` | 清理已完成 PodGroup/Job 残留 |
| `hypernode` / `sharding` | 拓扑资源（HyperNode/NodeShard）维护 |
| `colocationconfig` | 在离线混部配置 |
| `cache` / `metrics` / `sharding` | 共享缓存、Prometheus 指标、分片控制 |

### 3. vc-webhook-manager（准入控制）
- `installer/helm/chart/volcano/templates/webhooks.yaml` + `admission.yaml`
- 对 Job / PodGroup / Queue / Command 等 CRD 做 Mutating + Validating 准入
- 注入 `schedulerName: volcano`、env/svc/ssh 插件 sidecar、默认 queue 等

### 4. vc-agent + vc-agent-scheduler + network-qos（节点侧组件）
- `vc-agent`：上报节点 NUMA 拓扑、设备信息，执行节点侧 QoS/绑核
- `vc-agent-scheduler`：节点级本地调度协同（配合 HyperNode/NodeShard 分层调度）
- `network-qos`：节点网络 QoS 限速（在离线混部场景下保护在线）

### 5. vcctl（命令行）
- `cmd/cli`：`vcctl job submit / list / delete`、`vcctl queue`、`vcctl podgroup` 等
- 面向运维的 K8s 之外直接管理 Volcano 资源

## 核心概念

1. **PodGroup**（`scheduling.volcano.sh/v1beta1`）：一组 Pod 的逻辑集合，是调度的最小"整组"单位。`spec.minMember` 即 gang 调度的最小满足数；`spec.queue` 指定归属队列；`spec.priority` 控制抢占优先级。Job 控制器自动为每个 Job 创建 PodGroup。
2. **Queue**（`scheduling.volcano.sh/v1beta1`）：资源分配的逻辑队列。`spec.weight`（1–65535）决定 fair-share 权重；`spec.capability` 上限硬约束；`spec.reclaimable` 是否可被其他队列回收；`spec.guarantee` 资源预留。支持通过 annotation `volcano.sh/hierarchy` + `hierarchy-weights` 实现多级层级队列（root/eng/prod 1/2/8）。
3. **Job**（`batch.volcano.sh/v1alpha1`）：Volcano 高层作业抽象。`spec.minAvailable` 全局最小起数；`spec.schedulerName: volcano`；`spec.tasks[]` 每个任务有 `name/replicas/template(PodTemplateSpec)/policies`；`spec.policies[]` 事件→动作映射（如 `PodEvicted → RestartJob`）；`spec.plugins` 启用 env/ssh/svc 等内置 sidecar 插件；`spec.maxRetry` 控制重启上限。
4. **Gang Scheduling**：核心调度语义。PodGroup 的 `minMember` 个 Pod 必须同时被分配，否则一个都不起（避免占着资源跑不起来的死锁）。Volcano 通过 allocate + preempt/gangpreempt 实现。
5. **Session**：调度周期的隔离上下文。每周期开启→快照→跑 actions→关闭。把长事务拆成短周期，状态隔离清晰。
6. **Action + Plugin 框架**：Action 定义"做什么"（allocate/preempt…），Plugin 定义"怎么判断"（gang/binpack/drf/priority…）。同一 Action 可挂载多个 Plugin 形成策略组合。二者通过 `framework.Session` 共享状态。
7. **Tier 与 Plugins 配置**：`plugins []conf.Tier` 支持 Tier 分层（多级策略链），每 Tier 可挂多个 Plugin，按权重/顺序生效。
8. **HyperNode / NodeShard / NUMATopology**：拓扑资源抽象。HyperNode 表示网络/拓扑域（一档、二档、三档亲代），NodeShard 做分片，NUMATopology 上报节点 NUMA/设备拓扑，供 `numaaware`/`network-topology-aware`/`task-topology` 等 plugin 做拓扑亲和。
9. **Command**（`bus.volcano.sh/v1alpha1`）：内部事件总线命令，触发器驱动的 Job 生命周期动作（重启、增删 Pod 等）。
10. **ColocationConfiguration**：在离线混部配置（CPU/内存/网络 QoS 策略、best-effort vs burstable 隔离），配合 `overcommit`/`usage`/`cdp`/`conformance` 等 plugin。

## 数据流（一次调度周期）

1. **周期触发**：`Scheduler.Run()` 每 `schedulePeriod`（默认 1s）触发一次 `scheduler.RunScheduledOnce`。
2. **Session.Open(ssn)**：从 `cache` 拷贝当前 Queues、Jobs（含 PodGroup）、Nodes、PendingTasks 的快照到 `Session`，构建任务优先队列与节点索引。
3. **Plugins.OnSessionOpen(ssn)**：各注册 plugin 初始化本周期数据结构（如 gang plugin 预计算 PodGroup 满足度、binpack 预计算节点装箱分数、drf 预计算各用户主导份额）。
4. **Actions 流水线执行**（按 volcano-scheduler.conf 的 actions 顺序）：
   1. `enqueue`：将 PodGroup 状态推进到 Inqueue（待调度）。
   2. `allocate`（主）：
      - 按队列优先级遍历 pending tasks
      - 对每个 task 调 `PredicateFn`（predicates/numaaware/deviceshare…）过滤节点
      - 调 `NodeOrderFn`/`BatchNodeOrderFn`（nodeorder/binpack/task-topology…）打分排序
      - 选最优节点 → pipeline 预分配（先占坑，再下周期确认）
      - 满足 PodGroup minAvailable → `AllocateFunc` 绑定 Pod↔Node
   3. `backfill`：对剩余低优先级/弹性 task 填补空隙。
   4. `preempt` / `reclaim` / `gangpreempt` / `gangreclaim`：当高优 task 资源不足，按策略抢占低优 Pod（优先级/队列权重驱动），抢占后等下周期 allocate 收尾。
   5. `shuffle`：必要时打散。
5. **Plugins.OnSessionClose(ssn)**：plugin 收尾（写 metrics、释放临时结构）。
6. **Session.Close()**：绑定结果通过 `BindContext` 提交 kube-apiserver（`BindFunc`），更新 PodGroup 状态、metrics。
7. **Controller 反应**：Job/podgroup 控制器 watch 到 Pod 绑定/状态变化，更新 PodGroup phase、Job phase；若 Pod 被驱逐触发 `policies` 动作（如 RestartJob），经 `bus` Command 重新创建 Pod，进入下一轮 maxRetry 计数。

## 持久化层 / 数据模型

Volcano 本身**无独立数据库**——所有状态以 K8s 自定义资源形式持久化在 etcd：

| GVK | 资源 | 用途 |
|-----|------|------|
| `batch.volcano.sh/v1alpha1` Job | 作业定义 + tasks + 策略 | 控制器据此创建 Pod 与 PodGroup |
| `batch.volcano.sh/v1alpha1` CronJob | 定时触发 | 按周期生成 Job |
| `batch.volcano.sh/v1alpha1` JobFlow / JobTemplate | DAG 编排 | 多 Job 依赖、模板复用 |
| `scheduling.volcano.sh/v1beta1` PodGroup | 调度单元 | minMember/queue/priority/phase |
| `scheduling.volcano.sh/v1beta1` Queue | 资源队列 | weight/capability/reclaimable/hierarchy |
| `bus.volcano.sh/v1alpha1` Command | 事件总线 | 触发 Job 生命周期动作 |
| `nodeinfo.volcano.sh/...` NUMATopology | 节点 NUMA 拓扑 | agent 上报 |
| `topology.volcano.sh/...` HyperNode | 拓扑域 | 分层亲和调度 |
| `shard.volcano.sh/...` NodeShard | 节点分片 | 大集群分片调度 |
| `config.volcano.sh/...` ColocationConfiguration | 混部配置 | 在离线隔离策略 |

调度器运行时状态在 `pkg/scheduler/cache/` 内存缓存（watch apiserver 增量更新），不落盘。参见 [[kubernetes-crd]] 理解 CRD 模型本质。

## 项目结构

```
volcano/
├── cmd/                          # 7 个二进制入口
│   ├── scheduler/                # vc-scheduler
│   ├── controllers/              # vc-controller-manager
│   ├── webhook/                  # vc-webhook-manager
│   ├── agent/                   # vc-agent (节点侧)
│   ├── agent-scheduler/         # vc-agent-scheduler
│   ├── cli/                      # vcctl
│   └── network-qos/             # network-qos
├── pkg/
│   ├── scheduler/
│   │   ├── framework/           # Action/Plugin/Session/BindContext 接口与实现
│   │   ├── actions/             # enqueue/allocate/backfill/preempt/reclaim/gang*/shuffle
│   │   ├── plugins/             # 28 个 plugin: gang/binpack/capacity/drf/priority/
│   │   │                        # proportion/overcommit/resourcequota/pdb/tdm/sla/usage/
│   │   │                        # nodeorder/predicates/numaaware/deviceshare/
│   │   │                        # network-topology-aware/nodegroup/rescheduling/
│   │   │                        # resource-strategy-fit/task-topology/cdp/conformance/extender
│   │   ├── cache/               # 调度器内存缓存 + BindContext
│   │   ├── conf/                # scheduler config 解析（Tiers/Plugins）
│   │   ├── metrics/             # Prometheus 指标
│   │   ├── gate/                # 特性开关（schGateManager）
│   │   └── util/
│   ├── controllers/             # 15 个控制器 + 共享 cache/framework/metrics/sharding
│   ├── agent/                   # 节点侧 agent 逻辑
│   └── ...
├── staging/src/volcano.sh/apis/ # CRD API 定义（types.go）
├── installer/helm/chart/volcano/# Helm chart（CRD + Deployment + 监控）
│   └── templates/
│       ├── *_*.yaml             # CRDs + 组件 Deployment
│       └── grafana/prometheus/ # 监控栈
├── example/                     # 示例 Job/Queue/部署
├── docs/design/                 # 架构与设计文档（execution-flow.md/job-api.md）
└── Makefile                     # 构建入口
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Go 1.26 |
| 模块 | `volcano.sh/volcano` |
| K8s 依赖 | client-go、k8s.io/api、k8s.io/apimachinery、k8s.io/apiserver、scheduler-plugins framework |
| 调度框架 | 自研 `pkg/scheduler/framework`（Action/Plugin/Session/BindContextHandler 接口） |
| CRD | kubebuilder 风格 markers（validation/default/pattern） |
| 准入 | mutating/validating webhook（k8s admission) |
| 监控 | Prometheus + Grafana（内置 chart） |
| 部署 | Helm chart、官方镜像、YAML 清单 |
| 构建 | Makefile + docker buildx（支持多架构 DOCKER_PLATFORMS） |
| 可选能力 | CGO 插件机制（SUPPORT_PLUGINS=yes 时 musl-gcc 编译，支持外挂 .so plugin） |

## 构建与测试

```bash
# 全量构建（在仓库根）
make all            # = vc-scheduler vc-agent-scheduler vc-controller-manager
                   #   vc-webhook-manager vc-agent vcctl command-lines

# 启用外挂 CGO 插件支持（musl 静态链接）
SUPPORT_PLUGINS=yes make all    # CGO_ENABLED=1 + musl-gcc

# 构建镜像（多架构）
make images DOCKER_PLATFORMS="linux/amd64,linux/arm64"

# 运行单测
make test
# 或
go test ./pkg/... ./cmd/...

# Helm 安装到 K8s（最快上手）
helm repo add volcano-sh https://volcano-sh.github.io/helm-charts
helm repo update
kubectl create namespace volcano-system
helm install volcano volcano-sh/volcano -n volcano-system

# 纯 YAML 安装（无 Helm）
kubectl apply -f https://raw.githubusercontent.com/volcano-sh/volcano/main/installer/volcano-development.yaml

# 提交一个 Job
kubectl apply -f example/job.yaml
kubectl get job -n default
kubectl get podgroup -n default
```

框架接口（`pkg/scheduler/framework/interface.go`）：

```go
type Action interface {
    Name() string
    Initialize()
    Execute(ssn *Session)
    UnInitialize()
}
type Plugin interface {
    Name() string
    OnSessionOpen(ssn *Session)
    OnSessionClose(ssn *Session)
}
type BindContextHandler interface {
    SetupBindContextExtension(state *k8sframework.CycleState, bindCtx *cache.BindContext)
}
```

## 设计权衡

1. **独立调度器而非 kube-scheduler plugin**：Volcano 作为 `schedulerName: volcano` 的独立调度器运行，而非默认调度器的 plugin。代价是要接管整个 Node 的 Pod 调度权；收益是能实现跨 Pod 的 gang 决策、队列级抢占，这些在单 Pod 视角的 kube-scheduler 框架内做不到。与 [[kagent]]（CRD+controller 声明式）不同，Volcano 用独立调度器实现复杂调度语义。
2. **Session 隔离 vs 长事务**：每周期开新 Session、快照、跑完关闭。优势是状态隔离、无长锁、热加载友好；代价是周期内无法跨周期保持复杂中间态（需落回 CRD/PodGroup 状态）。1s 周期是吞吐与响应延迟的折中。
3. **Action + Plugin 正交解耦**：Action 管"流程"（allocate/preempt…），Plugin 管"策略"（gang/drf/binpack…）。可自由组合，新增调度策略无需改 Action。但 Plugin 间通过 Session 共享状态有隐式耦合，需 Tier 配置控制优先级。
4. **CRD 即状态层**：所有持久化走 etcd + CRD，无独立 DB。好处是与 K8s 生态（RBAC、controller、watch）天然一致；坏处是大集群 PodGroup/Queue 数量受 etcd 限速约束（`sharding` 控制器正是为此分片）。参见 [[kubernetes-crd]]。
5. **Pipeline 预分配**：allocate 阶段先"占坑"（pipeline），下周期确认。降低并发冲突概率，但引入一个周期的确认延迟——以吞吐换正确性。
6. **混部优先 vs 专享**：通过 `overcommit`/`cdp`/`conformance` 等 plugin 支持在离线混部，但也意味着默认配置可能不够"保守"——生产 AI 训练通常关掉 overcommit，靠 `gang` + `proportion` + `priority` 保证 SLA。
7. **CGO 插件可选**：`SUPPORT_PLUGINS=yes` 编译进 CGO，允许外挂 .so 扩展调度策略。灵活但破坏静态链接与跨平台分发——默认不开，官方镜像都是纯静态 Go。
8. **生态集成靠 PodGroup 注解而非 fork**：Spark/Flink/Ray 等通过识别 `schedulerName: volcano` + PodGroup 注解接入，Volcano 不 fork 这些框架。集成面薄、维护成本低，但要求上游配合。

## 生态系统

| 集成方向 | 说明 |
|----------|------|
| Spark on K8s | 通过 volcano-sh/spark-on-k8s-operator，PodGroup 自动创建，gang 调度 driver+executors |
| Flink | native Kubernetes + Volcano 调度，JobManager/TaskManager 整组 |
| Ray | Ray KubeRay + Volcano，RayCluster CRD 调度 |
| TensorFlow / PyTorch / MPI | 训练框架 Pod 注 `schedulerName: volcano`，Volcano Job 管 worker/ps 整组 |
| MindSpore / PaddlePaddle / MXNet / KubeGene | 国产/分布式训练框架，均以 PodGroup 为调度单元接入 |
| Argo Workflows | 与 [[argo-workflows]] 互补：Argo 管 DAG 工作流，Volcano 管单步批调度 |
| Kubeflow | [[kubeflow]] 训练 operator 可指定 volcano scheduler |
| Horovod | 弹性训练 + Volcano gang |
| 监控 | 内置 Prometheus + Grafana chart，暴露调度延迟、队列资源、抢占次数等指标 |

与工作流生态对比：[[apache-airflow]]、[[argo-workflows]]、[[kubeflow]]、[[temporal]] 偏"流程编排/任务依赖"，Volcano 偏"资源调度/整组分配"——常与编排层（如 [[argo-workflows]]）分层组合。

## 相关链接

- 仓库：<https://github.com/volcano-sh/volcano>
- 官网：<https://volcano.sh>
- Helm chart：<https://volcano-sh.github.io/helm-charts>
- 设计文档：`docs/design/execution-flow.md`、`docs/design/job-api.md`
- CNCF 页面：<https://www.cncf.io/projects/volcano/>

**Wiki 关联**：[[kubernetes-crd]]（CRD 模型）· [[kagent]]（K8s 原生 Go 项目对照）· [[argo-workflows]]（编排层互补）· [[kubeflow]]（ML 生态上层）· [[apache-airflow]]（工作流对比）· [[temporal]]（持久化执行对照）
