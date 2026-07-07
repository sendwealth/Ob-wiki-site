---
title: LobeChat 多智能体协作架构
created: 2026-07-06
updated: 2026-07-06
type: concept
tags: [ai, agent, multi-agent, orchestration, architecture, knowledge-management]
sources: [本地源码 /home/rowan/Projects/lobehub, packages/agent-runtime, src/store/chat/agents/GroupOrchestration]
confidence: high
---

# LobeChat 多智能体协作架构

> LobeChat 在 `@lobechat/agent-runtime` 包中自研了一套 **Brain(决策)+ Engine(执行)** 分离的 Agent 运行时,多智能体协作建立在此之上的 **Supervisor-Executor 双层状态机** 架构:Supervisor Agent 通过工具调用(speak/broadcast/delegate)表达协作意图,确定性状态机翻译为指令,Executor 复用单 Agent 运行时执行。支持浏览器 LLM、云沙箱、异构 CLI Agent(Claude Code/Codex)三种执行后端统一抽象。

---

## 一、整体定位

LobeHub 不仅是 ChatGPT Web 应用,`packages/agent-runtime` 是一套**完整的自研 Agent 运行时**,支持从单 Agent 到多智能体协作的完整光谱。多智能体协作是其核心差异化能力,核心代码分布在三个层次:

| 层次 | 位置 | 职责 |
|---|---|---|
| **运行时** | `packages/agent-runtime/src/` | 通用 Plan→Execute 循环、状态、事件 |
| **编排** | `src/store/chat/agents/GroupOrchestration/` | Supervisor 状态机、Group Executors |
| **调度/传输** | `src/store/chat/slices/agentRun/` | Runtime 路由、异构执行、Gateway、UI 桥接 |

## 二、核心架构:三层 Plan→Execute 循环

多智能体协作建立在 **Brain + Engine 分离** 模式上,这个模式被**复用了两次**(自相似):

```
┌─────────────────────────────────────────────────────────────┐
│  单 Agent 层 (AgentRuntime)                                  │
│    Agent(Brain) ──instruction──► AgentRuntime(Engine)       │
│    指令: call_llm / call_tool / call_tools_batch /          │
│          finish / request_human_approve|prompt|select /     │
│          resolve_blocked_tools                              │
└─────────────────────────────────────────────────────────────┘
                          ▲ 复用
                          │
┌─────────────────────────────────────────────────────────────┐
│  多 Agent 层 (GroupOrchestrationRuntime)                     │
│    Supervisor(Brain) ──instruction──► Executor(Engine)      │
│    指令: call_supervisor / call_agent /                     │
│          parallel_call_agents / delegate /                  │
│          exec_async_task / batch_exec_async_tasks /         │
│          finish                                             │
└─────────────────────────────────────────────────────────────┘
```

**关键设计洞察**:Group Orchestration 不是另起炉灶,而是**把单个 Agent 当作一个 Executor 来驱动**。Supervisor 本身也是一个 Agent,它通过"工具调用"指挥其他 Agent。这是 LobeHub 多智能体协作的精髓——单 Agent 和多 Agent 用同一个 Plan→Execute 模式,Group Orchestration 把 Agent 当 Executor 复用,而不是另造体系。

详见 [[lobechat-highlights]] 的 Brain/Engine 分离架构与 GraphAgent 节。

## 三、单 Agent 运行时(`packages/agent-runtime/src/core/`)

`AgentRuntime` 是 Engine,执行来自 Agent(Brain)的指令。核心循环 `runtime.step(state, context)`:

### 3.1 指令集(7 类 Executor)

| 指令 | 用途 |
|---|---|
| `call_llm` | 调用大模型(流式) |
| `call_tool` / `call_tools_batch` | 调用工具,支持批量并发(用 `p-map`) |
| `finish` | 结束 |
| `request_human_approve` | 人工审批 |
| `request_human_prompt` | 人工输入 |
| `request_human_select` | 人工选择 |
| `resolve_blocked_tools` | 处理被阻断的工具 |

**优先级覆盖**:`agent.executors > config.executors > 内置`,允许 Agent 自带定制执行器。

### 3.2 状态与事件

- **`AgentState`**:维护 `messages / usage / cost / stepCount / status / userInterventionConfig / maxSteps / toolManifestMap`
- **事件流**:`init / llm_start / llm_stream / llm_result / tool_pending / tool_result / human_*_required`,驱动前端流式 UI
- **统一 finish reasons**:`completed / max_steps_exceeded / cost_limit_exceeded / user_aborted / user_requested / max_steps_completed` — 标准化枚举跨系统统一,是工程化质量标志

## 四、多智能体协作:GroupOrchestrationRuntime

### 4.1 三角色架构

| 角色 | 实现 | 职责 |
|---|---|---|
| **Supervisor(大脑)** | `GroupOrchestrationSupervisor` | 状态机,接收 ExecutorResult → 产出下一个 SupervisorInstruction |
| **Executor(执行层)** | `createGroupOrchestrationExecutors` | 接收 SupervisorInstruction → 执行 → 返回 ExecutorResult |
| **Runtime(协调器)** | `GroupOrchestrationRuntime` | 编排 Supervisor↔Executor 循环,管理 operationId / abort |

### 4.2 Supervisor 的决策逻辑(确定性状态机)

这是最值得注意的设计——**Supervisor 是确定性状态机,不是 LLM**。它只做"指令翻译":

```
init                              → call_supervisor        (启动)
supervisor_decided(speak)         → call_agent             (单点发言)
supervisor_decided(broadcast)     → parallel_call_agents   (广播并行)
supervisor_decided(delegate)      → delegate               (委托)
supervisor_decided(execute_task)  → exec_async_task        (异步任务)
supervisor_decided(execute_tasks) → batch_exec_async_tasks (并发任务)
supervisor_decided(finish)        → finish                 (结束)
agent_spoke / agents_broadcasted /
  task_completed / tasks_completed → call_supervisor OR finish  (回到决策)
delegated                         → finish
```

真正的"由谁发言"决策发生在 **Supervisor Agent 调用工具**时——即 LLM 通过 function call 表达意图,Supervisor 状态机只是把这个意图翻译成指令。

> **核心设计哲学**:把 LLM 的不确定性隔离在工具调用层,而编排逻辑保持确定、可测、可枚举。这是整个系统最值得学习的点。

### 4.3 三种协作模式 + 异步任务

通过 supervisor 的 `decision` 字段实现:

| decision | 含义 | 说明 |
|---|---|---|
| `speak` | 单个 Agent 发言 | 顺序对话 |
| `broadcast` | 多个 Agent 并行发言 | 可 `disableTools`(纯回复,不调工具) |
| `delegate` | 委托给另一个 Agent 接管 | 接管后 `skipCallSupervisor` 直接结束 |
| `execute_task` | 异步任务(服务端) | SWR 轮询状态,5s 间隔 |
| `execute_tasks` | 并发异步任务 | 多任务批量执行 |
| `finish` | 结束编排 | |

异步任务支持 `runInClient` 在客户端运行,通过 `aiAgentService.execSubAgentTask` 触发。

### 4.4 关键的解耦:工具即协作触发器

> 当 Supervisor 调用 group-management 工具(speak/broadcast/delegate)时,工具返回 `stop: true` 终止 AgentRuntime,并注册 `afterCompletion` 回调触发编排。

这是一个非常优雅的设计,解耦了"决策"与"编排":

```
Supervisor Agent 走标准 AgentRuntime 循环
        │
        ├─► 调用 speak/broadcast/delegate 工具
        │       │
        │       ├─► 工具返回 stop: true (终止当前 AgentRuntime)
        │       └─► 注册 afterCompletion 回调
        │
        ├─► Supervisor Agent 自然结束
        │
        └─► afterCompletion 触发 groupOrchestration.triggerSpeak/Broadcast/Delegate
                │
                └─► 构造 initialResult 启动新一轮 GroupOrchestrationRuntime 循环
```

**为什么不在工具执行器里直接递归启动 Runtime?** 避免了在工具执行中途嵌套启动新 Runtime 的复杂性(状态污染、abort 传播、上下文丢失)。先让当前 Agent 干净结束,再用回调启动下一轮,每一轮 Runtime 生命周期独立。

实现位置:
- `packages/builtin-tool-group-management/src/executor.ts` — speak/broadcast/delegate 工具执行器
- `packages/builtin-tool-agent-management/src/executor.ts` — call_agent / @agent 工具
- `src/store/chat/slices/aiAgent/actions/groupOrchestration.ts` — `triggerSpeak/Broadcast/Delegate/ExecuteTask`

### 4.5 边界保护

- **最大轮次**:`DEFAULT_MAX_ROUNDS = 10`,超限触发 `max_rounds_exceeded` 事件
- **`skipCallSupervisor`**:某些决策执行完后不再回到 Supervisor,直接结束(如 delegate)
- **AbortController**:每个 operation 绑定,支持用户中止,贯穿整个调用链
- **operationId 传播**:Supervisor 执行时不传 operationId,让其创建子 operation(隔离)

## 五、三种执行后端(Runtime Type)

LobeHub 的多智能体不只是"多 LLM 调用",而是支持**异构执行后端**。`selectRuntimeType` 统一在所有入口点(sendMessage / regenerate / resume / continue / sub-agent dispatch)做路由:

| Type | 含义 | 适用场景 |
|---|---|---|
| `client` | 浏览器内 AgentRuntime | 默认,本地 LLM API 调用 |
| `gateway` | 云沙箱(Gateway WebSocket) | 远端执行,`agent-gateway.lobehub.com` |
| `hetero` | 异构 CLI Agent | Claude Code / Codex,通过 desktop IPC 或 sandbox |

**优先级**:`parentRuntime > hetero(desktop only) > gateway > client`

### 5.1 集中化路由决策

`selectRuntimeType` 注释明确:"每个入口点都用同一套优先级,新增入口不需要重新推导路由规则"。这是避免路由逻辑碎片化的关键——所有入口(sendMessage / regenerate / resume / continue / sub-agent dispatch)都经过同一个决策函数。

### 5.2 异构执行器(`heterogeneousAgentExecutor.ts`)

最复杂的部分:
- 通过 `@lobechat/heterogeneous-agents` 的 `reduceMainAgent` reducer 解释 main-agent 协调意图
- 处理 CLI 认证失败,识别 6 种 auth 失败模式(`401 / unauthorized / auth_error / not authenticated / failed to authenticate / invalid authentication credentials`),分别给出 `CLAUDE_CODE_CLI_INSTALL_DOCS_URL` / `CODEX_CLI_INSTALL_DOCS_URL` 修复指引
- 支持 `device` / `sandbox` / `local` 三种执行目标,通过 `resolveExecutionTarget` 在服务端/桌面/浏览器间统一解析
- `openclaw` / `hermes` 远程设备走 gateway 路径(`lh connect` 连接的设备,非 desktop IPC)

## 六、用户触发协作的三种入口

所有入口都映射到统一的 `AgentInvocationIntent`,再交给 `dispatchNonHeteroSubAgent`:

| 入口 | 触发方式 | 说明 |
|---|---|---|
| `callSubAgent` | 主 Agent 主动调用子 Agent | 工具调用 |
| `callAgent` | Group Orchestration 中 supervisor 调度 | 编排内部 |
| `@agent` 提及 | 用户在输入框 `@某个Agent` | UI 层 `useMentionCategories` + `MentionedUsers` |

设计契约明确排除了三种情况(各走专用管线):
- 异构 Agent → hetero 管线
- Group Orchestration → `triggerSpeak`
- 异步任务模式 → `execSubAgent` executor

> **统一 Intent 模式**:三种入口统一映射为 `AgentInvocationIntent`,运行时路由完全由 dispatcher 负责,调用方只声明"做什么",不关心"怎么做"。这与 [[acp-protocol]] 的 Session 抽象、[[a2a-protocol]] 的 Task 抽象思路一致。

## 七、前端协作 UI

| 组件 | 位置 | 用途 |
|---|---|---|
| `AssistantGroup` | `src/features/Conversation/Messages/AssistantGroup/` | 多 Agent 消息分组渲染 |
| `Tasks/` | `src/features/Conversation/Messages/Tasks/` | 异步任务 UI(`ClientTaskItem` 等) |
| `AgentTasks` | `src/features/AgentTasks/` | Agent 任务工作区(List/Detail/CreateModal/WorkspaceLayout),带 routeMeta + workspace 作用域 |
| `metadata.isSupervisor` | 消息元数据 | 标记 supervisor 身份,UI 据此差异化渲染 |
| `toolMessageId` 作为 parentId | 广播场景 | 用工具消息 ID 作为父 ID,构建正确的消息树 |

## 八、可观测性与工程化

### 8.1 完整可观测性栈(独立 packages)

| package | 用途 |
|---|---|
| `agent-tracing` | 链路追踪 |
| `agent-signal` | 信号桥接(`agentSignalBridge.ts`) |
| `agent-mock` | 测试 mock |
| `audit/` | 审计 |
| `subagentMetrics.ts` | 子 Agent 指标(token / cost) |

### 8.2 类型驱动

- `SupervisorInstruction` 和 `ExecutorResult` 都是 **tagged union**,`type` 字段做穷尽判断
- `FinishReason` 标准化枚举跨整个系统统一
- 类型系统保证了"新增 decision 必须处理对应 instruction"的穷尽性

### 8.3 测试覆盖

- `GroupOrchestration/__tests__/call-supervisor.test.ts` — supervisor 执行器
- `GroupOrchestration/__tests__/batch-exec-async-tasks.test.ts` — 批量异步任务
- `executor.test.ts` — 工具执行器
- `createAgentExecutors/__tests__/call-tool.test.ts` — 工具调用
- 测试用 mock store + mock aiAgentService,`vi.mock` 优先于 `vi.spyOn`(项目规范)

### 8.4 Legacy 隔离

`@deprecated` 标记旧 `GroupOrchestrationPhase` / `GroupOrchestrationContext`,正在从"phase 字符串"迁移到"类型化 Instruction/Result"。迁移期双轨并存,新代码用类型化指令。

## 九、架构总结:五个值得学习的点

1. **Brain/Engine 双层 + 自相似**:单 Agent 和多 Agent 用同一个 Plan→Execute 模式,Group Orchestration 把 Agent 当 Executor 复用,而非另造体系。

2. **LLM 不确定性隔离在工具层**:Supervisor 状态机本身确定性,LLM 的决策通过 function call 工具(speak/broadcast/delegate)表达,编排逻辑可测、可枚举、可中断。

3. **工具的 `stop: true` + `afterCompletion` 回调**:让 Supervisor Agent 自然结束再触发下一轮编排,避免在工具执行器里直接递归启动 Runtime 的复杂性。每轮 Runtime 生命周期独立。

4. **异构执行后端统一抽象**:同一套 AgentRuntime 概念支持浏览器 LLM、云沙箱、Claude Code/Codex CLI,`selectRuntimeType` 单点路由,所有入口共用。

5. **工程化护栏**:最大轮次、cost limit、abort、统一 finish reason、完整 tracing/metrics、tagged union 类型穷尽、legacy 隔离迁移。

## 十、与生态对比

| 维度 | LobeChat | [[crew-ai]] | [[auto-gen]] | [[langchain]] LangGraph |
|---|---|---|---|---|
| 编排模式 | Supervisor 状态机 + 工具触发 | Role-playing Agents | 对话式 GroupChat | Graph 状态机 |
| 决策位置 | LLM 工具调用(隔离) | Agent 内 | LLM 轮次 | Graph 节点 |
| 确定性 | 编排逻辑确定 | 低 | 低 | 中(Graph 结构确定) |
| 执行后端 | 浏览器/云沙箱/CLI 异构 | Python 进程 | Python 进程 | Python/JS |
| 人机协作 | approve/prompt/select 内置 | 弱 | 弱 | 中断点 |

LobeChat 的差异化在于:**编排确定性 + 异构后端 + Web 原生**。CrewAI/AutoGen 偏 Python 生态的"模拟人类团队",LobeChat 则是"工程化的可扩展运行时"。

## See Also

- [[lobechat-architecture]] — LobeChat 整体架构(Next.js 后端 + Vite SPA 前端)
- [[lobechat-highlights]] — 项目十大工程亮点,含 Agent Runtime 基础、GraphAgent
- [[opensource-practices-from-lobechat]] — 开源项目开发维护实践
- [[e2e-practices-from-lobechat]] — Cucumber + Playwright E2E 实践
- [[crew-ai]] / [[auto-gen]] / [[langchain]] — 多 Agent 框架对比
- [[claude-code-workflow]] — 确定性多 agent 编排引擎,另一种编排思路
- [[acp-protocol]] / [[a2a-protocol]] — Agent 通信协议标准
