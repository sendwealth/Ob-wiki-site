---
title: OpenWorker
created: 2026-07-25
updated: 2026-07-25
type: entity
tags: [ai-agent, desktop-app, local-first, open-source, productivity, mcp]
sources: [https://github.com/andrewyng/openworker, https://openworker.com]
confidence: high
---

# OpenWorker

> AI 原生桌面协作者：本地优先、模型中立、产出物导向，由 Andrew Ng 团队开源，基于自研 [aisuite](https://github.com/andrewyng/aisuite) 构建。

## 一句话定位

OpenWorker 是运行在用户桌面的开源 AI 同事（coworker），目标不是聊天，而是直接交付**可分享的文件、Slack 回复、整理好的日历、分流过的收件箱**等完成品。它本地优先、自带 25+ 连接器、支持任意模型，并通过审批门控确保人在环。

## 核心能力

- **交付真实产物**：文档、表格、报告、网页以文件形式落地，而非仅返回文本。
- **多入口触发**：桌面应用内对话、Slack `@OpenWorker` 提及、定时自动化（automation）、无人值守运行（unattended）。
- **25+ 连接器**：GitHub、Slack、Jira、Notion、Linear、HubSpot、Outlook、monday.com、Gmail、Google Calendar 等，外加任意 MCP Server。
- **模型中立**：OpenAI、Anthropic、Google Gemini、Inkling、GLM、DeepSeek、Kimi、Qwen、MiniMax、Mistral、Grok、Together、Fireworks、Ollama 本地模型等。
- **本地优先**：agent 循环、对话、连接器 token、模型 key 全部存在本机密钥库；仅有 OAuth 握手走云端代理。
- **审批门控**：写入、发送、shell 命令等关键动作需要用户批准，无人值守时改为 Inbox 挂单。

## 整体架构

```text
┌────────────────────────────────────────────────┐
│              OpenWorker desktop app            │  Tauri + React 原生桌面壳
├────────────────────────────────────────────────┤
│           local agent server (Python)          │  FastAPI + TurnEngine + 连接器
├───────────────┬────────────────┬───────────────┤
│  your files   │   your tools   │  your model   │  全部用你自己的 key，跑在本地
│  & terminal   │ 25+ connectors │  any provider │
└───────────────┴────────────────┴───────────────┘
```

### 目录结构

| 目录 | 职责 |
|---|---|
| `coworker/` | Python 后端：agent 引擎、模型 provider、连接器、MCP 客户端、记忆、自动化 |
| `surfaces/gui/` | 桌面应用：React + Vite + Tauri（Rust） |
| `stt/` | 语音输入旁路（Rust） |
| `packaging/` | macOS DMG、Windows 安装包、自动更新清单 |
| `docs/` | 设计规范与决策日志 |
| `tests/` | 后端测试套件（80+ 文件） |

## 核心组件

### 1. Agent 表面（Surfaces）

每个 agent 是一个带系统提示 + 工具集 + workspace 需求的表面（surface）。

- **Code**：代码 agent，工作区绑定，工具为 `code_files`、`git`、`search`、`shell`、`todo`，类似 Claude Code 的编码体验。
- **Cowork**：通用知识工作 agent，产出物导向，支持多根目录 `files`。
- **Chat**：纯对话 agent，无需 workspace。
- **MyHelper**：常驻助手，与 Cowork 共享工具集，处理入站消息。
- **Ops**：内置 persona，面向运维、排障、runbook。

agent 通过 `Agent` dataclass 定义（`coworker/agents/base.py:28`），关键字段包括 `family`（`code` / `knowledge`）、`messaging`、`connectors`。

### 2. TurnEngine —— 受控的 Agent 循环

`coworker/engine.py:52` 是核心循环：

- 每轮用户输入可触发多次 model↔tool 迭代，直到模型不再请求工具、护栏触发或被中断。
- 同批低风险工具调用（读、搜索）并发执行；写入 / shell 严格串行。
- 支持中断：`_cancel` Event + `interrupt_hooks`，可终止流、工具或等待中的审批。
- 模型可热切换：`switch_model()` 通过统一 OpenAI 消息格式在各 provider 间迁移。

### 3. PermissionEngine —— 权限与模式

`coworker/permissions.py:84` 决定每个工具调用是放行、拒绝还是询问用户：

- **Mode 五态**：`discuss`（只读聊天）、`plan`（只读+计划工作流）、`interactive`（默认审批）、`auto`（全放行）、`custom`（按配置 auto-allow）。
- 写入路径必须落在可写 root 下；shell 命令需通过白名单或逐条批准。
- **Standing rules**：针对外部风险工具（如 `send_message`），可绑定精确目标实现任务级自动放行（`tool → target`）。
- 命令白名单校验：先拒绝含 shell 操作符（`; | &&` 等）的命令，再做 argv 前缀匹配，避免 `git status && rm -rf ~` 被误放行。

### 4. 工具系统

工具通过 `ToolRegistry` 注册，来源包括：

- 内置 catalog：`code_files`、`files`、`git`、`search`、`shell`、`todo`、`ask_user`、`propose_plan`、`request_directory` 等（`coworker/catalog.py`）。
- 连接器工具：根据已启用连接器动态生成（`coworker/connectors/tools.py`）。
- MCP 工具：通过 `MCPManager` 连接 stdio / streamable-http MCP Server 后动态暴露。
- Skill 工具：Anthropic 格式的可加载 skill，任意 agent 可调用。

### 5. MCP 客户端

`coworker/mcp/client.py:33` 是自研的薄异步 MCP 客户端：

- 每个 server 跑在独立 asyncio task 中，负责 enter/exit 整个生命周期。
- 支持 `stdio` 和 `http`（含 OAuth）两种 transport。
- 同步的 `ToolRegistry` 通过 `run_coroutine_threadsafe` 桥接到异步 MCP 调用。

### 6. 记忆（Memory）

`coworker/memory/sqlite_store.py:13` 提供 SQLite 持久化记忆：

- 作用域：`global`、`workspace`、`session`。
- 提供 `remember`、`memory_update`、`memory_forget` 工具。
- 系统提示中注入记忆使用指南：只存用户纠正、偏好、无法从代码中重新推导的项目上下文，避免噪音。

### 7. SessionManager —— 控制中心

`coworker/server/manager.py:106` 是单进程控制中心，持有：

- 每个 session 的 `TurnEngine` 实例。
- SQLite 记忆、审计、会话、自动化、Inbox、订阅、mention thread 等存储。
- `MCPManager`、`PersonaRegistry`、`Gateway`（入站消息监听）、`Scheduler`（定时任务）。
- ProviderRouter：按模型前缀路由到对应 provider，共享同一密钥库。

### 8. FastAPI 服务器

`coworker/server/app.py:165` 暴露：

- WebSocket：承载引擎事件流与审批通道。
- OpenAI-compatible `/v1/chat/completions`：任何 OpenAI 格式客户端都可用。
- REST：sessions、agents、personas、connectors、MCP、automations、inbox 等。
- CORS 严格限制为 `tauri://localhost`、`localhost`、`127.0.0.1`，防止任意网页跨源驱动本地 agent。

### 9. 自动化与入站消息

- **Scheduler**：30 秒 tick，`run-once-catch-up` + `skip-on-overlap`，支持因审批挂单而暂停、恢复（`coworker/automation/scheduler.py:23`）。
- **Slack mention 路由**：`@OpenWorker` 被提及时，若无订阅 session，则为该 thread 新建 session 并持有回复权（`coworker/mentions.py:32`）。
- **Channel subscription**：监听频道消息，触发 session 响应。
- **Unattended**：无人值守运行将审批请求放入 Inbox，而不是阻塞或自动执行。

## 数据流示例

1. 用户在桌面应用输入任务。
2. GUI 通过 WebSocket 发送给 FastAPI server。
3. `SessionManager` 找到/创建 `TurnEngine`。
4. `TurnEngine` 调用 `ProviderRouter` 发送消息给模型。
5. 模型返回 tool calls，`PermissionEngine` 决策；需要审批则通过 WS 返回审批卡片。
6. 工具执行结果写回消息历史，继续迭代。
7. 最终产物写入本地文件或发送到连接器目标，事件流回 GUI 渲染。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.10+、FastAPI、uvicorn、Pydantic v2、aisuite |
| 桌面壳 | Rust + Tauri v2 |
| 前端 | React 18 + Vite + Tailwind CSS + TypeScript |
| 测试 | pytest（后端）、Vitest + Playwright（前端/E2E） |
| 数据库 | SQLite（记忆、会话、自动化、审计等） |
| 协议 | MCP（stdio/streamable-http）、OAuth、WebSocket、OpenAI-compatible REST |
| 语音 | Rust STT sidecar |

## 安全设计要点

- **本地 token**：server 启动生成 per-launch token，桌面用内存 token，浏览器 dev 模式读用户私有 token 文件。
- **Origin 门控**：浏览器来源必须匹配本地/Tauri origin，阻断恶意网页驱动本地 agent。
- **Workspace trust**：代码工作区需显式信任，未信任时 shell 命令需逐条审批。
- **路径作用域**：写入只能在用户授权的根目录内。
- **SecretStore**：连接器 token、模型 key 存本机密钥库。
- **MCP OAuth**：`interactive=True` 才允许弹浏览器登录，避免后台静默劫持。

## 与相关项目的关系

- **aisuite**：OpenWorker 构建在 aisuite 之上，是其 agent 层的一个完整桌面应用参考实现。
- **Claude Code / Codex CLI**：OpenWorker Code agent 提供类似的编码体验，但更强调多连接器、本地运行、模型中立和完成品交付。
- **Browser-Use / n8n / Dify**：OpenWorker 不是纯浏览器自动化或工作流编排器，而是面向桌面个人/团队的通用 coworker，连接器 + MCP 让它可以接入这些能力。
- **agentspace / multica**：同为 AI 原生协作 workspace，OpenWorker 更偏向本地桌面优先、个人生产力；agentspace 更偏向组织级数字员工与跨 harness 调度。

## 关键设计洞察

1. **完成品优先**：系统提示反复强调产出可打开、可分享的文件，而不是聊天回复。
2. **本地优先 ≠ 孤立**：通过 MCP 和 25+ 连接器连接外部世界，但执行核心和凭据留在本地。
3. **人在环是默认**：所有可能产生后果的动作都走审批；自动化场景用 Inbox 挂单而非自动执行。
4. **模型中立**：用 aisuite 统一 provider API，用户可切换任意模型，降低供应商锁定。
5. **agent 即 surface**：Code / Cowork / Chat / MyHelper 共享同一引擎，但通过 persona、工具集、workspace 需求区分体验。

## 适用场景

- 个人桌面 AI 助理：整理文件、写报告、查日历、回邮件。
- 开发者本地编码 agent：类似 Claude Code 的代码编辑、测试、git 操作。
- 运维值班助手：读日志、查指标、写 incident note、Slack 回复。
- 定时自动化：晨间简报、周报、频道监控。

## 局限与注意事项

- 当前仅 macOS Apple Silicon 提供签名公证安装包；Windows 版本未代码签名，SmartScreen 会警告。
- 项目处于公开 beta，核心功能可用，但仍在快速迭代打磨。
- 开源 MIT 协议，但团队表示会基于内部路线图开发，部分社区 PR 可能与愿景冲突。
- 服务端为单进程本地 server，非为大规模多用户并发设计。

## Related Pages

- [[aisuite]] — OpenWorker 底层统一 LLM API 与 agent 工具库
- [[claude-code]] — 同类型本地编码 agent 体验
- [[browser-use]] — 网页自动化 agent，可通过 MCP 接入 OpenWorker
- [[agentspace]] — 组织级 agent-native 协作 workspace
- [[multica]] — AI 原生任务管理平台
- [[mcp-protocol]] — Model Context Protocol 连接外部工具
- [[a2a-protocol]] — Agent 间协作协议，可与 MCP 互补
