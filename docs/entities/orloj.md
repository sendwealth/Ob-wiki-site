---
title: Orloj
created: 2026-05-25
updated: 2026-06-28
type: entity
tags: [project, ai, kubernetes, agent-platform, open-source, b2b]
sources:
  - ~/Projects/orloj (源码)
  - https://docs.orloj.dev
confidence: high
---

# Orloj

> "Agents are infrastructure." — 多 Agent 系统全栈平台：声明式 YAML 定义 Agent/Tool/Model/Memory，内置治理、可观测性、A2A 互操作、Kubernetes CRD GitOps，从本地单机到分布式生产一键扩展。

---

## 定位

Orloj 是一个面向生产级多 Agent 系统的全栈管理平台。核心理念是把 Agent 当基础设施对待 —— 用 YAML 声明 Agent、Tool、Model Endpoint、Memory、Schedule、Policy，平台负责调度执行、治理审批、链路追踪和运维部署。

**一句话**：Kubernetes for AI Agents。

- **仓库**：`github.com/OrlojHQ/orloj`
- **语言**：Go 1.26（单一代码库）
- **许可证**：Apache-2.0
- **状态**：v0.16.x，活跃开发中，API 1.0 前可能变动

## 架构

```
┌──────────────────────────────────────────────────────┐
│                    Interfaces                         │
│  YAML · orlojctl · REST API · SDKs · K8s CRDs · UI  │
├──────────────────────────────────────────────────────┤
│              Agent Definitions                        │
│  Agent · AgentSystem · Prompts · Graph Topology      │
│  Roles · Execution Contracts · Runtime Bounds         │
├──────────────────────────────────────────────────────┤
│            Execution Runtime                          │
│  Sequential / Message-Driven · Workers · Leases       │
│  Heartbeats · Retries · Idempotency · Dead-Letter    │
├──────────────────────────────────────────────────────┤
│          Model & Context Layer                        │
│  ModelEndpoint · ContextAdapter · Provider Routing    │
│  Fallback Models · Secrets · Token Budgets · Memory   │
├──────────────────────────────────────────────────────┤
│        Tool & Integration Layer                       │
│  HTTP · gRPC · MCP · A2A · Webhooks · WASM           │
│  Docker/K8s Isolation · Auth · Timeouts · Retries     │
├──────────────────────────────────────────────────────┤
│       Governance & Human Review                       │
│  AgentPolicy · AgentRole · ToolPermission              │
│  ToolApproval · TaskApproval                          │
├──────────────────────────────────────────────────────┤
│     Observability & Operations                        │
│  Traces · Logs · Messages · Prometheus · OTel         │
│  Watch Streams · Events · UI Views                    │
├──────────────────────────────────────────────────────┤
│     State & Deployment Substrate                      │
│  In-Memory / Postgres · NATS JetStream                │
│  Docker Compose · VPS · K8s · CRD GitOps              │
└──────────────────────────────────────────────────────┘
```

## 核心数据流

```
声明 → 协调 → 调度 → 认领 → 执行 → 治理 → 观察 → 扩展
 (YAML) (Controller) (Queue) (Worker) (Agent Loop) (Policy) (Trace) (Scale)
```

1. **声明**：用 YAML 定义 Agent、System、Tool、Model Endpoint、Memory、Secret、Evaluation、Policy
2. **协调**：Controller 校验资源、更新状态、发现 MCP 工具、管理 Schedule
3. **调度**：Task 指向 AgentSystem，按容量分配 Worker
4. **认领**：Worker 通过 Lease 认领 Task，持续心跳，超时可被接管
5. **执行**：有界 Agent Loop 路由 Model 调用、调用 Tool、使用 Memory、在 Graph 中传递消息
6. **治理**：Policy / Role / ToolPermission / Approval 在运行时 fail-closed
7. **观察**：每次运行记录 Trace Event、Task History、Message、Metric、OTel Span
8. **扩展**：从嵌入式 Worker 单机起步，迁移到 Postgres + NATS JetStream 分布式

## 技术栈

| 层面 | 技术 |
|------|------|
| 语言 | Go 1.26 |
| 数据库 | PostgreSQL (pgx/v5) + pgvector 向量搜索 |
| 消息队列 | NATS JetStream |
| 容器编排 | Kubernetes (controller-runtime + client-go) |
| 可观测性 | Prometheus + OpenTelemetry |
| 模型接入 | AWS Bedrock (anthropic/openai/openrouter/ollama 等) |
| 工具沙箱 | Docker 容器 / K8s Jobs / WASM (wazero) |
| CLI | Cobra (orlojctl) |
| API | REST + OpenAPI 3.1 |
| 部署 | Helm Chart + Docker Compose |
| 前端 | 内置 Web Console |

## 8 个 CRD 资源

| CRD | Short Name | 用途 |
|-----|-----------|------|
| Agent | oagent | Agent 定义（prompt、model、tools） |
| AgentSystem | - | Agent 拓扑编排（pipeline/hierarchical/swarm） |
| Tool | - | 工具定义（HTTP/gRPC/CLI/WASM/MCP） |
| McpServer | - | MCP 服务器注册与工具自动发现 |
| ModelEndpoint | - | 模型端点 + Provider 路由 + Fallback |
| Memory | - | 短期/长期记忆 + pgvector 向量存储 |
| AgentPolicy | - | 治理策略（Role、Permission、Approval） |
| Secret | - | 加密密钥管理 |

## API 资源端点

REST API v1 覆盖 18 个资源域：

- `/v1/agents` · `/v1/agent-systems` · `/v1/model-endpoints` · `/v1/tools`
- `/v1/secrets` · `/v1/sealed-secrets` · `/v1/memories`
- `/v1/agent-policies` · `/v1/agent-roles` · `/v1/tool-permissions` · `/v1/tool-approvals` · `/v1/task-approvals`
- `/v1/tasks` · `/v1/task-schedules` · `/v1/task-webhooks`
- `/v1/workers` · `/v1/mcp-servers` · `/v1/a2a`
- `/v1/auth` · `/v1/system` · `/v1/events`

认证：Bearer Token + Session Cookie 双模式。

## 二进制组件

| 二进制 | 用途 |
|--------|------|
| `orlojd` | API Server + 控制平面（可嵌入 Worker） |
| `orlojworker` | 独立分布式 Worker |
| `orlojctl` | CLI 工具（validate / seal / eval / a2a card） |
| `orloj-operator` | CRD Sync Operator（K8s GitOps） |
| `orloj-alertcheck` | 告警检查 |
| `orloj-loadtest` | 负载测试 |

## 关键特性

### A2A 协议互操作
- 暴露 Agent 为 A2A 端点（Agent Card + JSON-RPC）
- 调用远程 A2A Agent 作为 Tool
- 每个 AgentSystem 独立认证（`spec.a2a.auth: bearer | none`）
- 支持 `tasks/send`、`tasks/sendSubscribe`（SSE）、`tasks/get`、`tasks/cancel`

### Kubernetes 深度集成
- **CRD Sync Operator**：让 Orloj 资源成为真正的 K8s CRD，支持 `kubectl apply` 和 GitOps（Argo CD / Flux）
- **K8s Agent 执行**：Agent 作为临时 K8s Job 运行（`--agent-k8s-enabled`）
- **K8s Tool 隔离**：Tool 以临时 K8s Job 执行（`isolation_mode: kubernetes`）

### 治理与审批
- `AgentPolicy` + `AgentRole` + `ToolPermission` 定义权限边界
- `ToolApproval` / `TaskApproval` 支持人工审批流
- 运行时 fail-closed：策略未定义则拒绝

### 可观测性
- 每个 Task 全链路 Trace Event
- Prometheus Metrics + OpenTelemetry Spans
- Watch Streams 实时事件推送
- Web Console 可视化（拓扑图、Task Trace 时间线、Sparkline 健康度）

## 项目结构

```
orloj/
├── api/            # REST API 层（路由、处理器、认证）
├── controllers/    # 控制器（资源协调、Schedule 管理）
├── scheduler/      # Task 调度与 Worker 分配
├── runtime/        # Agent 执行运行时（a2a、conformance）
├── crds/           # K8s CRD 类型定义 + Reconciler
├── resources/      # 资源模型（Agent、Tool、Graph、Policy）
├── store/          # 存储层（内存 + Postgres）
├── eventbus/       # 事件总线（内存 + NATS）
├── telemetry/      # 遥测与可观测性
├── cli/            # orlojctl CLI
├── cmd/            # 二进制入口
├── config/crd/     # 生成 CRD YAML
├── charts/orloj/   # Helm Chart
├── openapi/        # OpenAPI 3.1 Spec
├── monitoring/     # Grafana Dashboards + Alerts
├── examples/       # 蓝图（pipeline/hierarchical/swarm-loop）
├── docs/           # 文档站
└── testing/        # 测试场景与 Stub
```

## 设计决策与权衡

| 决策 | 选择 | 理由 |
|------|------|------|
| 声明式 YAML | 是 | GitOps 友好，版本控制，可 diff |
| Go 单体仓库 | 是 | 编译速度 + 类型安全 + K8s 生态天然亲和 |
| 双存储后端 | 内存 + Postgres | 本地开发零依赖，生产用 Postgres |
| 双执行模式 | Sequential + Message-Driven | 简单任务顺序执行，复杂系统消息驱动 |
| Worker Lease 模型 | 是 | 支持分布式 Worker、故障接管 |
| CRD 冲突策略 | 默认 warn | GitOps 和 REST API 并存时的优雅降级 |
| 内嵌 Worker | 可选 | 开发便利性 vs 生产独立性 |

## 版本历程（近期）

| 版本 | 日期 | 重点 |
|------|------|------|
| 0.16.1 | 2026-05-21 | A2A 安全修复（auth bypass、namespace mismatch） |
| 0.16.0 | 2026-05-17 | CRD Sync Operator、K8s Agent/Tool 执行、Helm Operator 模板 |
| Unreleased | - | Gold/Bronze UI 设计系统、A2A 安全加固 |

## 与相关项目对比

- **vs [[kagent]]**：Orloj 更成熟（治理/审批/可观测全栈），kagent 更轻量（K8s-native + 多运行时 ADK/CrewAI/LangGraph）。Orloj 自研执行运行时，kagent 委托给外部 Agent 框架。
- **vs [[a2a-protocol]]**：Orloj 是 A2A 协议的生产级实现者（endpoint + client），不是协议本身。
- **vs [[temporal]]**：Temporal 是通用持久化执行平台，Orloj 专注 Agent 场景（Model 调用、Tool 执行、Memory、Policy）。Orloj 的 Worker Lease 模式与 Temporal 的 Workflow/Activity 模式设计理念相近。

## 局限性

- API 1.0 前 schema 可能变动
- 单一副本部署（HA 需要 Leader Election）
- 目前 Go-only 运行时（不像 kagent 支持多语言 Agent 框架）
- 依赖 PostgreSQL + NATS JetStream 分布式部署

## 最新动态（截至 2026-06-28）

> [!note] 无显著新动态，但所处赛道（K8s 声明式 agent 基础设施）在 2026 持续升温
> Orloj 本身 2026 上半年未见重大版本或战略变动，但其主张的"Agents are infrastructure + 声明式 CRD"路线正成为行业共识。

### 行业背景（虽非 Orloj 自身动态，但影响其定位）
- **K8s + AI agent 收敛趋势**：CNCF 2026 博文"The Great Migration"指出 AI 平台集体向 K8s 收敛，Orloj 的 CRD 路线踩中趋势
- **[[kagent]] 升温**：同为 K8s 声明式 agent 框架，kagent 2026 在 KubeCon 曝光增加，带动整个赛道关注度
- **Agent Sandbox CRD**：K8s SIG Apps 推出 Sandbox CRD（详见 [[agent-sandbox]]），与 Orloj 的多 CRD 方案形成参照

### Orloj 的差异化仍成立
- **8 CRD 治理体系**（审批/互操作/GitOps）比 kagent（偏编排）和 agent-sandbox（偏隔离）更全面
- **A2A 互操作**原生支持，在多 agent 协作场景有定位
- 但曝光度不及 kagent（CNCF 加持），社区规模差距明显

### 仍待观察
- 是否会寻求 CNCF/CNCF-adjacent 治理以提升曝光
- Go-only 运行时是否会扩展多语言
