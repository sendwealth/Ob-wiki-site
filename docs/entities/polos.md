---
title: Polos
created: 2026-07-02
updated: 2026-07-02
type: entity
tags: [product, project, platform, saas, b2b, ai, active, mvp]
sources:
  - https://github.com/polos-dev/polos
  - https://polos.dev/docs
  - https://www.linkedin.com/pulse/why-i-built-polos-durable-execution-ai-agents-neha-deodhar-wjp1c
confidence: medium
---

# Polos

> Polos 是一个**面向 AI Agent 的开源持久化执行运行时（Durable Execution Runtime for AI Agents）**。它的核心理念是"You write the agent. Polos handles the rest."——开发者只需写 Agent 业务逻辑，Polos 负责沙箱化执行、持久化状态、人工审批、触发器与可观测性等生产级基础设施。Orchestrator 用 **Rust** 编写、Postgres 持久化；Worker 用 **Python / TypeScript SDK** 连接。本质上是把 [[temporal]] 的持久化执行范式（事件溯源 + 确定性重放）专门优化到了 LLM Agent 场景，并叠加了沙箱、HITL、Prompt 缓存等 Agent 特有能力。

---

## 一句话定位

**给 AI Agent 用的 Temporal**——把 LLM 调用、工具副作用、人工审批都变成可持久化、可重放、不重复计费的 durable step。

与通用工作流引擎的关键差异：

| 维度 | 通用 Agent 框架（LangGraph/CrewAI） | 通用 Durable 引擎（[[temporal]]） | **Polos** |
|------|------------------------------------|----------------------------------|-----------|
| 持久化执行 | ❌ 崩溃重来 | ✅ 事件溯源 | ✅ 事件溯源，**且针对 LLM 调用做缓存去重** |
| 沙箱执行 | ❌ DIY 或裸跑 | ❌ 不关心 | ✅ Docker/E2B/VM 内置 exec/read/write/grep/web_search |
| 人工审批 | ❌ 自己造 | ⚠️ 通用 Signal，需手写 | ✅ Slack/UI/Terminal 一键审批 |
| 触发器 | ⚠️ 粘合代码 | ⚠️ 需自建 | ✅ Webhook/HTTP/Cron/Event/Slack 开箱即用 |
| 编程模型 | ⚠️ Graph/DAG | ✅ 普通代码 | ✅ 普通代码，**No DAGs. No graph syntax.** |

---

## 解决的核心痛点

源自作者 Neha Deodhar（Google 高级工程经理）的判断："**AI Agent 在生产中失败，本质是分布式系统问题**"。具体痛点：

1. **LLM 调用昂贵且不可重入**——Agent 跑到第 8 步崩溃，传统方式要从第 1 步重跑，已花的 token 钱白花
2. **长时任务易中断**——网络抖动、供应商限流、进程重启都会让几分钟/几小时的 Agent 任务前功尽弃
3. **Agent 需要危险操作**（执行代码、删文件、部署），但**没有现成的安全沙箱 + 审批闭环**
4. **触发与协作零散**——每个 Webhook、每个 Slack 入口都要写粘合代码
5. **可观测性靠 grep**——Agent 做了什么决策、调了什么工具，全埋在日志里

Polos 的回答：把每一步副作用（工具调用、API 响应、延时）都记进 **durable log**，崩溃后从 log 重放，已完成的步骤直接返回历史结果，**LLM 调用永远不付两次钱**。

---

## 整体架构

Polos 采用经典的 **Orchestrator–Worker 分离**架构（与 [[temporal]] 的 Cluster–Worker 拓扑同构）：

```
┌─────────────────────────────────────────────────────────────────┐
│                        Polos 架构                                │
└─────────────────────────────────────────────────────────────────┘

   开发者侧                          Polos 平台侧
 ┌────────────┐     注册/心跳     ┌──────────────────────────────┐
 │            │ ◀──────────────▶ │   Orchestrator (Rust)         │
 │  Agent 代码 │                  │  ┌────────────────────────┐  │
 │  (Py/TS)   │                  │  │ 执行状态机 + Durable Log│  │
 │            │     任务分发      │  │ 重试 / 调度 / 触发器    │  │
 │  Worker    │ ◀──────────────  │  │ 审批协调 / Dashboard UI │  │
 │  (SDK)     │                  │  └────────────────────────┘  │
 │            │ ─── 工具调用 ──▶ │         │                    │
 └─────┬──────┘   副作用结果     │         ▼ 持久化              │
       │                         │   ┌────────────┐             │
       │ 拉起/销毁                │   │  Postgres   │             │
       ▼                         │   └────────────┘             │
 ┌────────────┐   可观测性       └──────────────────────────────┘
 │  Sandbox   │ ◀── OTel Trace ─────────┘
 │ Docker/E2B │
 │ /VM        │   ┌────────────┐
 │ +内置工具  │   │ Slack/HTTP  │ ◀── 审批 / 触发
 └────────────┘   │ /Cron/Webhk │
                  └────────────┘
```

**两个核心组件：**

- **Orchestrator（Rust）**：管理执行状态、durable log、重试、调度、触发器、审批流、Dashboard。Rust 选型保障高并发低延迟，Postgres 做单一事实源（事件日志）。
- **Worker（Python/TypeScript SDK）**：运行用户 Agent 与 workflow，连接 Orchestrator 拉取任务。**水平扩展只需多开 Worker 进程**，天然适配 LLM Agent 长时、I/O 密集特征。

---

## 核心能力（六大支柱）

### 1. 沙箱化执行（Sandboxed Execution）

Agent 运行在隔离环境，内置一套开箱即用的 `sandboxTools()`：

| 内置工具 | 作用 |
|---------|------|
| `exec` | 在沙箱内跑 shell 命令 |
| `read` / `write` / `edit` | 文件操作 |
| `glob` / `grep` | 代码库导航 |
| `web_search` | 联网检索 |

**沙箱后端可切换**：Docker（`node:20-slim` 等镜像，可配 memory/CPU）、E2B（云沙箱）、Cloud VM。开发者无需写沙箱生命周期管理代码，传一个 `sandboxTools()` 即可。

可与 [[openshell]]（NVIDIA 的 Landlock+seccomp+namespace+OPA 多层隔离沙箱）、[[agent-sandbox]]（K8s SIG 的 Sandbox CRD）对比——Polos 更偏"应用层易用"，后两者更偏"系统级强隔离"。

### 2. 持久化工作流（Durable Workflows）

- **自动重试 + 状态持久化**：从失败的那一步精确恢复（resume from the exact step that failed）
- **Prompt 缓存**：官方宣称 **60–80% 成本节省**
- **并发控制**：跨 Agent 的速率协调，避免 LLM API 限流混乱

底层原理（与 [[temporal]] 一致）：捕获每个副作用结果入 durable log；进程死亡后重放 workflow，对已记录的步骤直接返回缓存值，**本地变量与调用栈在毫秒级恢复**。区别在于 Polos 把"LLM 调用"也视为一种可缓存的副作用——这是通用 workflow 引擎不会做的优化。详见 [[temporal-durability-stability]] 与 [[durable-execution-for-agents]]（待建）。

### 3. 人在环（Human-in-the-Loop）

任意工具调用都可挂审批门：
- **多渠道触达**：Slack、Discord、Email
- **三种 UI**：Slack / Dashboard / Terminal
- **可配置规则**：哪些操作需要审批（如 `exec` 命令 allowlist，命中自动放行，未命中暂停等审批）
- **暂停即零成本**：Agent 暂停等待审批时不消耗任何算力

```typescript
// 审批示例：exec 走 allowlist，其余人工审批
exec: {
  security: "allowlist",
  allowlist: ["node *", "npm install *", "cat *", "ls *"],
}
// 自定义工具：approval: "always" 每次都要人审
const deployTool = defineTool(
  { id: "deploy", approval: "always", /* ... */ },
  async (ctx, input) => { /* 审批通过后才执行 */ }
);
```

### 4. 触发器（Triggers）

每个 Agent **自动获得一个 Webhook URL**，可直接对接 GitHub / JIRA / Salesforce。外加：
- HTTP API
- Cron 定时
- Event-driven 事件驱动
- 内置 Slack 集成（在聊天里 @mention 即可触发 Agent）

### 5. 可观测性（Observability）

- **OpenTelemetry** 全链路追踪：每一步、每个工具调用、每次审批都有 span
- 完整执行历史
- 可视化 Dashboard（`polos dev` 起在 `http://localhost:5173`）

可与 [[langfuse]]（LLM 专用可观测）、[[langfuse]] 的 trace 模型对照——Polos 的 OTel 路线更通用、更易接入既有 APM。

### 6. 携带自有栈（Bring Your Stack）

- **任意 LLM**：OpenAI / Anthropic / Google 等，经 Vercel AI SDK 与 LiteLLM
- **携带既有 Agent**：CrewAI、LangGraph、Mastra 写的 Agent 可直接接入，获得 Polos 的持久化/可观测/沙箱，**无需重写**
- **双语言 SDK**：Python 与 TypeScript
- **开源、可自托管**

---

## 编程模型

**核心卖点：No DAGs. No graph syntax. Just Python or TypeScript.**

这是对 LangGraph 等图编排框架的明确反旗——Polos 认为 Agent 逻辑就该是普通代码，持久化由平台透明保障（这正是 [[temporal]] 的哲学）。

**Python 示例（沙箱 Agent）：**
```python
from polos import Agent, sandbox_tools, SandboxToolsConfig, DockerConfig

sandbox = sandbox_tools(SandboxToolsConfig(
    env="docker",
    docker=DockerConfig(image="node:20-slim", memory="2g"),
))

coding_agent = Agent(
    id="coding_agent",
    provider="anthropic",
    model="claude-sonnet-4-5",
    system_prompt="You are a coding agent.",
    tools=sandbox,
)
```

**TypeScript 示例（带审批）：** 见上文 HITL 段。

---

## CLI 体验

```bash
curl -fsSL https://install.polos.dev/install.sh | bash   # 安装
npx create-polos          # TS 脚手架
pipx run create-polos     # Python 脚手架

polos dev                 # 起 server + worker，热重载
polos run <agent>         # 交互式跑某个 Agent
polos agent list          # 列出可用 Agent
polos tool list           # 列出可用工具
polos logs <agent>        # 流式日志
```

`polos dev` 后开 `http://localhost:5173` 看 Dashboard，体验对标 Vercel/Mastra 的 DX。

---

## 与相邻方案的定位关系

Polos 处在一个有趣的**交叉地带**，可同时与多类项目对比：

```
       持久化执行能力强  ▲
                        │
            Temporal ●  │
                        │
                        │      ● Polos  ← 把 Temporal 的能力
                        │              专为 Agent 优化
       通用编排 ◀────────┼────────▶ Agent 专用
                        │
        Airflow ●       │       ● LangGraph
        Dagster ●       │       ● CrewAI
        Prefect ●       │       ● Mastra
                        │
                        │  ● n8n / Dify（低代码流）
                        │
                  持久化弱  ▼
```

- **vs [[temporal]]**：Temporal 是通用持久化引擎，强大但需自己处理沙箱/LLM/审批。Polos = Temporal 思路 + Agent 专用层（沙箱工具、Prompt 缓存、HITL、Slack）。Polos 甚至允许把 Temporal 当作底层借鉴对象。
- **vs [[opengeni]]**（同周调研的最直接竞品）：同为"AI Agent 持久化运行时"，但 Polos **自研 Rust orchestrator**、强调"No DAGs 普通代码"；OpenGeni **直接复用 Temporal**、借力 OpenAI Agents SDK、把"Agent 跑在你自己机器上（Connected Machine）"做成与云沙箱对等的一等公民，且工程成熟度（强制 RLS 多租户、exactly-once SSE、Stripe 计费、部署产物）明显更高。
- **vs LangGraph / CrewAI**：这些是 Agent 编排框架（图/角色），但**不保证持久化**，崩溃即重来。Polos 可"包裹"它们，给既有 Agent 加上持久化与可观测。
- **vs [[dagster]]/[[prefect]]/[[apache-airflow]]**：数据工作流引擎，擅长 ETL/批处理，不针对 LLM Agent。详见 [[ai-workflow-landscape]]。
- **vs [[dify]]/[[n8n]]/[[langflow]]**：低代码可视化流，适合非开发者；Polos 是代码优先（code-first）。
- **vs [[agents-cli]] / [[adk-python]]**：Google ADK 生态偏 Agent 构建与评估，Polos 偏 Agent **运行时基础设施**，可互补。

详细生态对照见 [[ai-workflow-deep-comparison]]。

---

## 设计取舍（基于公开材料的推断）

| 决策 | 选择 | 推断理由 |
|------|------|---------|
| Orchestrator 语言 | **Rust** | 高并发低延迟，内存安全；对标 Temporal 的 Go 但更激进 |
| 状态存储 | **Postgres** | 单一事实源，事务保证 durable log 一致性，运维门槛低 |
| Worker 语言 | **Python + TypeScript** | 覆盖 ML 生态与 Web 生态，是 Agent 开发者两大主力语言 |
| 编程模型 | **普通代码（非 DAG）** | 降低门槛，持久化透明化，直接继承 Temporal 哲学 |
| 沙箱 | **多后端可切** | 本地开发用 Docker，生产用 E2B/VM，灵活权衡隔离强度 |
| LLM 适配 | **Vercel AI SDK + LiteLLM** | 不锁定供应商，最大化"bring your stack" |
| 可观测 | **OpenTelemetry** | 业界标准，易接入既有 APM（Datadog/Honeycomb 等） |

---

## 适用场景（推测）

✅ **适合：**
- 长时、多步骤、易中断的 Agent（coding agent、研究 agent、数据处理 agent）
- 需要人工审批的高风险操作（部署、转账、删数据）
- 团队想用 Slack 驱动 Agent 协作
- 已有 LangGraph/CrewAI Agent 想加生产级可靠性
- 对 LLM 成本敏感、想用 Prompt 缓存省钱

⚠️ **可能不适合：**
- 单轮问答、无副作用的轻量 Agent（持久化开销不划算）
- 需要极强系统级隔离的高安全场景（Polos 沙箱偏应用层，[[openshell]] 更硬）
- 已重度投入 Temporal/Argo 的团队（能力重叠）

---

## 相关

- [[temporal]] — 通用持久化执行平台，Polos 的范式来源与核心对照
- [[temporal-durability-stability]] — Temporal 持久化与稳定性原理，Polos 底层同构
- [[temporal-highlights]] — Temporal 设计亮点
- [[opensource-project-practices-from-temporal]] — Temporal 开源工程实践（Polos 可借鉴）
- [[openshell]] — NVIDIA 系统级 Agent 沙箱，与 Polos 应用级沙箱对照
- [[agent-sandbox]] — K8s SIG Sandbox CRD，另一种沙箱路线
- [[langfuse]] — LLM 可观测平台，与 Polos OTel 路线对照
- [[ai-workflow-landscape]] / [[ai-workflow-deep-comparison]] — AI 工作流生态全景与深度对比
- [[langchain]] / [[crew-ai]] — 可被 Polos 包裹加持久化的 Agent 框架
- [[dagster]] / [[prefect]] / [[apache-airflow]] — 通用数据工作流引擎对照
- [[dify]] / [[n8n]] / [[langflow]] — 低代码流对照（Polos 是 code-first）

---

## 参考来源

- [polos-dev/polos — GitHub](https://github.com/polos-dev/polos)
- [Polos 官方文档](https://polos.dev/docs)
- [Why I Built Polos: Durable Execution for AI Agents — Neha Deodhar](https://www.linkedin.com/pulse/why-i-built-polos-durable-execution-ai-agents-neha-deodhar-wjp1c)
- [The Distributed Systems Problem: Why AI Agents Break in Production — Neha Deodhar](https://www.linkedin.com/pulse/distributed-systems-problem-why-ai-agents-break-neha-deodhar-isd3c)
- [Polos Durable Execution 文档](https://polos.dev/docs/fundamentals/durable-execution)
- [Polos Sandbox 文档](https://polos.dev/docs/agents/sandbox)

---

> **置信度说明**：定位、架构（Rust Orchestrator + Postgres + Py/TS Worker）、六大能力、CLI、代码示例均来自官方 README 与文档，**置信度高**。Star 数、License、精确目录结构等因 GitHub API 限流未能核验，标注 **medium**。设计取舍多为基于公开材料的合理推断。
