---
title: Kagent — Kubernetes 原生 AI Agent 框架
created: 2026-05-22
updated: 2026-06-28
type: entity
tags: [kubernetes, ai-agent, platform, open-source, mcp, a2a, go, python]
sources: [~/Projects/kagent 源码研究]
confidence: high
---

# Kagent — Kubernetes 原生 AI Agent 框架

> Kubernetes-native framework for building, deploying, and managing AI agents. 通过 CRD 声明式定义 Agent，Controller 自动编排运行时，支持多 LLM Provider、MCP 工具协议、A2A Agent 间通信。
> 版本：v0.x.x (Alpha) | License: Apache 2.0 | GitHub: kagent-dev/kagent
> 核心贡献者：Peter Jausovec (335)、Eitan Yarmush (314)、Scott Weiss (67)、Brian Fox (56)

---

## 一、项目定位

### 1.1 解决什么问题

AI Agent 在 Kubernetes 上的部署和管理缺乏标准化方案。现有痛点：

- Agent 部署需要手动管理 Pod、Service、ConfigMap
- LLM Provider 配置分散，缺少统一管理
- Agent 间通信依赖应用层实现
- 工具集成（MCP Server）需要手动配置
- 缺少 Agent 生命周期管理（创建→运行→监控→销毁）

### 1.2 核心理念

**Everything as Kubernetes Resources** — Agent、Model、ToolServer、Memory 都是 CRD：

```
传统方式:                              Kagent 方式:
┌─────────────┐                       ┌──────────────────┐
│ 手写 Dockerfile │                    │ Agent CRD (YAML)  │
│ 手动 K8s manifests│                  │   ├─ spec.type    │
│ 管理 API Keys   │                    │   ├─ LLM config   │
│ 配置工具连接    │                     │   ├─ tools/skills  │
│ 无统一观测     │                     │   └─ memory        │
└─────────────┘                       └──────────────────┘
       │                                      │
       ▼                                      ▼
  手动运维                           Controller 自动编排
```

---

## 二、架构总览

### 2.1 系统架构图

```
                         ┌──────────────────────────────────────────────┐
                         │                Kagent UI                     │
                         │           (Next.js 16 + React 19)           │
                         └────────────────────┬─────────────────────────┘
                                              │ HTTP API
                         ┌────────────────────▼─────────────────────────┐
                         │              HTTP Server (Go)                │
                         │   ┌──────────┐ ┌──────────┐ ┌────────────┐ │
                         │   │ Sessions │ │ Agents   │ │ Memories   │ │
                         │   │ Handler  │ │ Handler  │ │ Handler    │ │
                         │   └──────────┘ └──────────┘ └────────────┘ │
                         │        │ Auth (OIDC/Proxy) │                │
                         └────────┼───────────────────┼────────────────┘
                                  │                   │
            ┌─────────────────────▼──┐    ┌──────────▼──────────────────┐
            │   Controller (Go)       │    │     Database               │
            │   ┌──────────────────┐  │    │   ┌──────────┐ ┌────────┐ │
            │   │ AgentController  │  │    │   │ SQLite   │ │Postgres│ │
            │   │ MCPController    │  │    │   │ (dev)    │ │ (prod) │ │
            │   │ ModelController  │  │    │   └──────────┘ └────────┘ │
            │   │ ServiceController│  │    └────────────────────────────┘
            │   │ HarnessController│  │
            │   └──────────────────┘  │
            └────────────┬─────────────┘
                         │ Creates / Manages
                         ▼
            ┌─────────────────────────┐
            │   Agent Runtime Pods     │
            │   ┌───────────┐         │
            │   │ Python ADK│ ◄── Google ADK / CrewAI / LangGraph / OpenAI
            │   │ Go ADK    │ ◄── Go Agent Development Kit
            │   │ BYO Agent │ ◄── 自定义容器镜像
            │   └───────────┘         │
            │         │                │
            │    MCP Tools            │
            │   ┌──────────────────┐  │
            │   │ K8s │ Istio │ Helm│  │
            │   │Argo│Prom │Cilium│  │
            │   └──────────────────┘  │
            └─────────────────────────┘
```

### 2.2 四大核心组件

| 组件 | 语言 | 职责 | 关键文件 |
|------|------|------|----------|
| **Controller** | Go | 监听 CRD 变化，创建/管理 Agent 运行资源 | `go/core/internal/controller/` |
| **HTTP Server** | Go | REST API，Session 管理，认证授权 | `go/core/internal/httpserver/` |
| **UI** | TypeScript (Next.js) | Web 管理界面，Agent 配置/对话 | `ui/src/` |
| **Engine** | Python/Go | Agent 运行时，调用 LLM，执行工具 | `python/packages/`, `go/adk/` |

---

## 三、技术栈详细分析

### 3.1 Go 工作空间 (`go/`)

```
go/
├── go.work              # Go workspace（多模块）
├── api/                 # 共享类型：CRDs, ADK types, DB models, HTTP client
│   └── v1alpha2/        # 当前 API 版本
│       ├── agent_types.go           # Agent CRD
│       ├── modelconfig_types.go     # ModelConfig CRD
│       ├── modelproviderconfig_types.go  # ModelProviderConfig CRD
│       ├── remotemcpserver_types.go # RemoteMCPServer CRD
│       ├── agentharness_types.go    # AgentHarness CRD
│       ├── sandboxagent_types.go    # SandboxAgent CRD
│       └── common_types.go          # 共享类型（AllowedNamespaces, ValueRef）
├── core/                # 基础设施：controller, HTTP server, CLI
│   ├── cmd/controller/  # Controller 入口
│   ├── internal/
│   │   ├── controller/  # 7 个 Reconciler
│   │   ├── httpserver/  # HTTP API + Auth
│   │   ├── database/    # SQLite / Postgres 双驱动
│   │   ├── a2a/         # A2A 协议实现
│   │   ├── mcp/         # MCP handler
│   │   └── telemetry/   # OpenTelemetry tracing
│   └── cli/             # kagent CLI (Bubble Tea TUI)
└── adk/                 # Go Agent Development Kit
```

**Go 模块依赖亮点：**
- `controller-runtime v0.24.0`（K8s 1.36 支持）
- `trpc-a2a-go`（A2A 协议 Go 实现）
- `anthropic-sdk-go v1.43.0`
- `charmbracelet/bubbletea`（CLI TUI 框架）

### 3.2 Python 工作空间 (`python/`)

```
python/
├── pyproject.toml       # UV workspace
└── packages/
    ├── kagent-adk/      # 基于 Google ADK 的运行时
    ├── kagent-core/     # 核心共享逻辑
    ├── kagent-openai/   # OpenAI 集成
    ├── kagent-crewai/   # CrewAI 集成
    ├── kagent-langgraph/# LangGraph 集成
    ├── kagent-skills/   # 技能系统
    ├── agentsts-core/   # Agent TypeScript 核心桥接
    └── agentsts-adk/    # Agent TypeScript ADK 桥接
```

**多框架支持是核心设计决策** — Agent 运行时可以是 Python ADK、CrewAI、LangGraph、OpenAI 或 Go ADK，通过统一接口抽象。

### 3.3 UI (`ui/`)

```
ui/
├── package.json         # Next.js 16 + React 19
└── src/
    ├── components/
    │   ├── agent-form/  # Agent 创建/编辑表单
    │   ├── prompts/     # Prompt 库管理
    │   ├── models/      # 模型列表
    │   ├── onboarding/  # 引导向导
    │   └── ui/          # shadcn/ui 基础组件
    ├── contexts/        # AuthContext
    └── hooks/           # useSpeechRecognition 等
```

**技术栈：** Next.js 16 + React 19 + Radix UI + Tailwind CSS + Zustand + React Hook Form + Zod

### 3.4 Helm Charts (`helm/`)

```
helm/
├── kagent-crds/         # CRD 定义（必须先安装）
│   └── templates/       # 8 个 CRD YAML
├── kagent/              # 主应用 Chart
│   └── values.yaml      # 全局配置 + 组件配置
├── agents/              # 预置 Agent Charts
│   ├── k8s/             # Kubernetes 管理 Agent
│   ├── istio/           # Istio 管理 Agent
│   ├── cilium-debug/    # Cilium 调试 Agent
│   ├── argo-rollouts/   # Argo Rollouts Agent
│   ├── observability/   # 可观测性 Agent
│   ├── promql/          # PromQL Agent
│   ├── helm/            # Helm 管理 Agent
│   └── kgateway/        # k-gateway Agent
└── tools/               # 工具 Charts
    ├── querydoc/        # 文档查询
    └── grafana-mcp/     # Grafana MCP Server
```

---

## 四、CRD 资源模型

### 4.1 核心 CRD（8 个）

| CRD | 用途 | 关键字段 |
|-----|------|----------|
| **Agent** | Agent 声明式定义 | type (Declarative/BYO), description, skills, sandbox |
| **ModelConfig** | LLM 模型配置 | provider, model name, temperature 等 |
| **ModelProviderConfig** | LLM Provider 凭证 | API key (Secret ref), endpoint |
| **ToolServer** | MCP 工具服务器 | container image, config |
| **RemoteMCPServer** | 远程 MCP 服务器 | URL, auth |
| **AgentHarness** | Agent 运行时包装 | runtime config |
| **SandboxAgent** | 沙箱化 Agent | sandbox config |
| **Memory** | Agent 长期记忆 | (设计阶段, EP-1256) |

### 4.2 Agent CRD 深度分析

```go
// Agent 两种类型
type AgentType string
const (
    AgentType_Declarative = "Declarative"  // 声明式（kagent 管理）
    AgentType_BYO         = "BYO"          // 自带部署（用户管理）
)

// 声明式运行时
type DeclarativeRuntime string
const (
    DeclarativeRuntime_Python = "python"  // Python ADK
    DeclarativeRuntime_Go     = "go"      // Go ADK
)
```

**设计决策：**
- Declarative 模式：kagent Controller 自动创建 Deployment/Service/ConfigMap
- BYO 模式：用户自行管理部署，kagent 仅注册 A2A/MCP 端点
- Skills 从容器镜像拉取，通过 `/skills` 目录挂载
- AllowedNamespaces 实现跨命名空间引用控制（Gateway API 模式）

### 4.3 跨命名空间安全模型

```go
type AllowedNamespaces struct {
    From FromNamespaces  // All | Same | Selector
    Selector *metav1.LabelSelector
}
// 双向握手：Agent 声明允许哪些命名空间引用自己
// 与 Gateway API 的 cross-namespace routing 同模式
```

---

## 五、核心数据流

### 5.1 Agent 创建流程

```
用户创建 Agent CRD (kubectl apply / UI)
       │
       ▼
Controller Watch 检测到新 Agent
       │
       ├─ 1. 验证 Agent spec (type, runtime, LLM config)
       │
       ├─ 2. 获取 ModelProviderConfig → 解析 API Key (Secret ref)
       │
       ├─ 3. [Declarative] 翻译 Agent spec → K8s 资源:
       │      ├─ Deployment (Agent Runtime Pod)
       │      ├─ Service (Agent API endpoint)
       │      ├─ ConfigMap (Agent 配置)
       │      └─ ServiceAccount (RBAC)
       │
       ├─ 4. 注册 MCP 工具服务器连接
       │
       ├─ 5. 注册 A2A Agent Card (如果启用)
       │
       └─ 6. 更新 Agent Status (Ready / Error)
```

### 5.2 Agent 运行时对话流

```
用户 → UI → HTTP Server → Agent Runtime Pod
                              │
                              ├─ 调用 LLM (OpenAI/Anthropic/...)
                              │   └─ System Prompt + Tools + Memory
                              │
                              ├─ 工具调用 (MCP Protocol)
                              │   └─ MCP Server (K8s/Istio/Helm/...)
                              │
                              ├─ 子 Agent 调用 (A2A Protocol)
                              │   └─ 其他 Agent Runtime
                              │
                              └─ 流式响应 → UI 渲染
```

---

## 六、设计决策与权衡

### 6.1 关键架构决策

| 决策 | 选择 | 原因 | 权衡 |
|------|------|------|------|
| Agent 定义方式 | CRD | 声明式、版本化、可 gitops | 学习曲线 |
| 多运行时支持 | Python + Go | 生态覆盖 | 双语言维护成本 |
| 数据库 | SQLite (dev) + Postgres (prod) | 开发体验 + 生产强度 | 抽象层复杂度 |
| 认证 | OIDC + Proxy Auth | 企业集成 | 配置复杂 |
| 工具协议 | MCP | 行业标准 | 性能开销 |
| Agent 间通信 | A2A | 对等协作而非工具调用 | 额外协议栈 |
| UI 框架 | Next.js 16 + React 19 | 最新生态 | 升级风险 |

### 6.2 与同类项目对比

| 特性 | Kagent | Langflow | AutoGen |
|------|--------|----------|---------|
| 运行平台 | Kubernetes | Docker/Self-hosted | Python 进程 |
| Agent 定义 | CRD (YAML) | 可视化 Flow | Python Code |
| 多框架支持 | ADK/CrewAI/LangGraph/OpenAI | LangChain | AutoGen |
| Agent 间通信 | A2A Protocol | ❌ | AutoGen 协议 |
| 工具协议 | MCP | LangChain Tools | 函数调用 |
| 生产就绪度 | Helm + RBAC + Auth | 中 | 低 |
| 观测性 | OpenTelemetry | 基础 | 基础 |

---

## 七、活跃开发方向

### 7.1 近期特性（从 git log 分析）

| 方向 | 示例 PR | 状态 |
|------|---------|------|
| 记忆系统 | EP-1256 Memory CRD | 设计阶段 |
| MCP 原生支持 | EP-685 kmcp | 设计阶段 |
| OIDC 认证 | EP-476 Proxy Auth | 已实现 |
| Podman 支持 | 容器运行时替代 | 已合并 |
| HPA 管理 | BYO 部署保留 nil replicas | 已修复 |
| Bedrock 兼容 | 工具名 sanitization | 已修复 |
| Goroutine 泄漏检测 | goleak 测试用例 | 已合并 |

### 7.2 社区活跃度

- **总贡献者**: 20+ 活跃贡献者
- **近期节奏**: 每天 2-5 个合并 PR
- **主要贡献公司**: (从贡献者推断) 可能与云原生生态相关
- **依赖更新**: dependabot 自动化（go-minor-patch, python-minor-patch 组）

---

## 八、本地开发速查

```bash
# 创建 Kind 集群
make create-kind-cluster

# 配置集群
make use-kind-cluster

# 设置模型 Provider
export KAGENT_DEFAULT_MODEL_PROVIDER=openAI
export OPENAI_API_KEY=sk-xxx

# 构建镜像 + Helm 部署
make helm-install

# 访问 UI
kubectl port-forward -n kagent svc/kagent-ui 8001:8080

# 运行测试
make test           # 全部测试
make -C go e2e      # E2E 测试
make -C go lint     # 代码检查

# 生成 CRD 代码
make -C go generate
```

---

## 九、评价与观察

### 9.1 优势

- **Kubernetes-native**: 真正的声明式 Agent 管理，可 GitOps
- **多运行时**: 不是绑定单一框架，支持 ADK/CrewAI/LangGraph/OpenAI/Go
- **协议标准**: MCP (工具) + A2A (Agent 间) 双标准协议
- **企业就绪**: OIDC 认证、RBAC、跨命名空间安全模型
- **多 LLM Provider**: OpenAI/Anthropic/Azure/Gemini/Ollama/Bedrock

### 9.2 风险/局限

- **Alpha 阶段**: API 可能随时变动（v1alpha2）
- **复杂度**: K8s 知识门槛高，需要理解 CRD/Controller/Helm
- **双语言栈**: Go (infra) + Python (agent) 增加维护负担
- **记忆系统未完成**: 长期记忆还在设计阶段
- **文档分散**: CLAUDE.md/DEVELOPMENT.md/README.md 有重叠

### 9.3 适合场景

- 已有 Kubernetes 基础设施的团队
- 需要标准化 Agent 部署管理的组织
- 多 Agent 协作场景（利用 A2A）
- 需要企业级安全和审计的 AI Agent 平台

---

## 最新动态（截至 2026-06-28）

> [!note] CNCF 首个 K8s 原生 AI Agent 框架，进入主流云原生叙事
> kagent 2025-05-22 被 CNCF 接受为 **sandbox 项目**（发布仅两个月就入选，速度罕见）。2026 年成为 "AI 平台向 Kubernetes 收敛" 趋势的代表项目。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| CNCF 状态 | sandbox | **sandbox**（持续，未升级 incubating）|
| 行业地位 | K8s 原生 agent 框架 | **CNCF 调研 82% K8s 采纳**趋势下的标杆 |
| 曝光 | 社区项目 | **KubeCon Amsterdam 2026**（3 月）专题演讲 |

### 2026 生态信号
- **"The Great Migration"** —— CNCF 2026-03 博文指出 AI 平台正集体向 K8s 收敛，kagent 是这一趋势的受益者
- Go Operator 路线让 AI agent 成为 K8s 一等公民（`kubectl get agents`），与 [[agent-sandbox]] 的 CRD 路线呼应
- 深度解析文称其为"CNCF 首个 Kubernetes 原生 AI Agent 框架"，定位清晰

### 仍待观察
- 仍是 sandbox，距离 incubating/graduated 还有距离
- 与商业 K8s AI 平台的竞争（功能 vs 易用性）

## 关联

- [[adk-python]] — Kagent 使用 Google ADK 作为 Python 运行时基础
- [[a2a-protocol]] — Kagent 采用 A2A 协议实现 Agent 间对等通信
- [[superpowers]] — 类似的 AI Agent 工程流程规范体系
- [[context-mode]] — AI 编码 Agent 上下文优化技术
- [[heuristic-learning]] — Agent 学习范式参考
