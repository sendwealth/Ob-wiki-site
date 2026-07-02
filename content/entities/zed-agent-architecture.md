---
title: Zed Agent 架构深度分析
created: 2026-05-22
updated: 2026-06-28
type: entity
tags: [ai, architecture, rust, agent, acp, mcp, zed]
sources: [~/Projects/zed/ 源码研究]
confidence: high
---

# Zed Agent 架构深度分析

> Zed 编辑器的 Agent 系统架构：8 个核心 crate、ACP/MCP 双协议集成、内置 NativeAgent + 外部 Agent 子进程通信、完整的工具系统与 Context Server 注册机制。源自 ~/Projects/zed 源码研究。

---

## 1. 核心架构总览

Zed Agent 系统由 **8 个核心 crate** 组成，分为协议层、核心逻辑层和 UI 层：

```
用户输入 → AgentPanel(UI) → AcpThread(协议抽象) → AgentConnection → 后端
                                                                  ├─ NativeAgent (内置，直接调用 LLM)
                                                                  └─ AcpConnection (外部 Agent，ACP/JSON-RPC)
```

### Crate 职责表

| Crate | 路径 | 职责 |
|-------|------|------|
| `agent` | `crates/agent/` | 内置 Agent（NativeAgent）、Thread、ThreadStore、所有内置工具、ContextServerRegistry |
| `agent_servers` | `crates/agent_servers/` | `AgentServer` trait + 两个实现：`AcpConnection` 和 `CustomAgentServer` |
| `acp_thread` | `crates/acp_thread/` | `AcpThread` 实体 + `AgentConnection` trait（UI 与后端的统一接口） |
| `acp_tools` | `crates/acp_tools/` | ACP 调试面板，查看原始 JSON-RPC 消息 |
| `agent_ui` | `crates/agent_ui/` | AgentPanel、ConversationView、AgentConfiguration、InlineAssistant 等 |
| `agent_settings` | `crates/agent_settings/` | Agent 配置类型（AgentSettings、AgentProfile）、Profile 系统 |
| `agent_skills` | `crates/agent_skills/` | 从 `.agents/skills/` 目录加载用户自定义 Skill |
| `context_server` | `crates/context_server/` | MCP 客户端实现（stdio + HTTP 两种传输） |

## 2. Agent 选择与注册机制

### Agent 枚举

`agent_ui/src/agent_ui.rs:343` 定义了两种 Agent 类型：

```rust
pub enum Agent {
    #[default]
    NativeAgent,              // Zed 内置 Agent
    Custom { id: AgentId },   // 外部 ACP Agent（Claude、Gemini、Codex 等）
}
```

内置 Agent ID 为 `"Zed Agent"`。已知的外部 Agent ID：`"gemini"`、`"claude-acp"`、`"codex-acp"`。

### AgentServerStore — 注册中心

`project/src/agent_server_store.rs` 是 Agent 的注册中心：

```rust
pub struct AgentServerStore {
    state: AgentServerStoreState,
    pub external_agents: HashMap<AgentId, ExternalAgentEntry>,
}
```

- 维护 `external_agents` HashMap，存储所有外部 Agent 配置
- `AgentConnectionStore` 管理 Agent 的连接生命周期：`Connecting → Connected → Error`
- 监听 `AgentServersUpdated` 事件，当设置变更时重建连接

### AgentServer trait — 服务端抽象

`agent_servers/src/agent_servers.rs` 定义：

```rust
pub trait AgentServer: Send {
    fn agent_id(&self) -> AgentId;
    fn connect(&self, delegate, project, cx) -> Task<Result<Rc<dyn AgentConnection>>>;
    // + logo, default_mode, favorite_model_ids 等
}
```

两个实现：
- **`NativeAgentServer`** → `NativeAgentConnection`：直接用 Thread/LLM，不走 ACP
- **`CustomAgentServer`** → `AcpConnection`：启动子进程，ACP JSON-RPC 通信

## 3. ACP 协议实现

ACP (Agent Communication Protocol) 是 Zed 与外部 Agent 通信的协议，基于 **JSON-RPC over stdio**。

### 协议库

`agent-client-protocol` 是外部 crate（crates.io，v0.12.1），定义了所有 ACP schema 类型（`SessionId`、`PromptRequest`、`ContentBlock`、`ModelId`、`ToolKind` 等）和 JSON-RPC 传输层（`Agent`、`Client`、`ConnectionTo<Agent>`、`Responder` 等）。

### AcpConnection — 核心 ACP 实现

`agent_servers/src/acp.rs` 中的 `AcpConnection` 结构体：

```rust
pub struct AcpConnection {
    id: AgentId,
    connection: ConnectionTo<Agent>,       // JSON-RPC 连接
    sessions: Rc<RefCell<HashMap<acp::SessionId, AcpSession>>>,
    pending_sessions: ...,
    auth_methods: Vec<acp::AuthMethod>,
    agent_capabilities: acp::AgentCapabilities,
    child: Option<Child>,                  // 子进程
    _io_task: Task<()>,                    // 读 stdout
    _dispatch_task: Task<()>,              // 分发到前台线程
    _wait_task: Task<Result<()>>,          // 等待进程退出
    _stderr_task: Task<Result<()>>,        // 读 stderr
}
```

### 连接流程

```
AcpConnection::stdio()
  → 启动 Agent 子进程（配置的 command/args）
  → 建立 stdin/stdout JSON-RPC I/O
  → 发送 initialize 请求，获取 Agent 能力
  → 返回 Rc<dyn AgentConnection>
```

### 会话流程

```
AgentConnection::new_session()
  → AcpConnection 发送 ACP createSession 请求

AgentConnection::prompt()
  → AcpConnection 发送 ACP prompt 请求
  → 接收流式事件（文本增量、工具调用等）
  → 通过 unbounded channel 分发到 GPUI 前台线程
  → AcpSession 转发事件到 AcpThread 实体
```

前台分发机制：ACP 使用 `unbounded` channel（`dispatch_tx`/`dispatch_rx`）将 Agent 的 inbound JSON-RPC 请求（如工具执行）分发到 GPUI 前台线程，因为 GPUI 实体是 `!Send` 的。

### AgentConnection trait — 客户端抽象

`acp_thread/src/connection.rs` 定义：

```rust
pub trait AgentConnection {
    fn agent_id(&self) -> AgentId;
    fn new_session(...) -> Task<Result<Entity<AcpThread>>>;
    fn prompt(&self, id, params, cx) -> Task<Result<acp::PromptResponse>>;
    fn authenticate(&self, method, cx) -> Task<Result<()>>;
    fn model_selector(&self, session_id) -> Option<Rc<dyn AgentModelSelector>>;
    fn session_list(&self, cx) -> Option<Rc<dyn AgentSessionList>>;
    // + supports_resume_session, supports_load_session, supports_logout 等
}
```

可选能力 trait（Agent 按需实现）：
- `AgentSessionModes` — 会话模式切换（code mode / ask mode）
- `AgentSessionConfigOptions` — 动态配置选项
- `AgentSessionList` — 历史会话列表/删除
- `AgentModelSelector` — 模型列表和选择
- `AgentTelemetry` — 遥测数据

## 4. 内置 NativeAgent

`agent/src/agent.rs` 定义了 Zed 的内置 Agent：

```rust
pub struct NativeAgent {
    sessions: HashMap<acp::SessionId, Session>,
    pending_sessions: HashMap<acp::SessionId, PendingSession>,
    thread_store: Entity<ThreadStore>,
    projects: HashMap<EntityId, ProjectState>,
    language_models: LanguageModels,
    // ...
}
```

每个 `Session` 同时持有：
- `thread: Entity<Thread>` — 内部线程，与语言模型直接通信
- `acp_thread: Entity<AcpThread>` — 协议层线程，用于 UI 渲染

`NativeAgentConnection`（line 1748）包装 `Entity<NativeAgent>` 并实现 `AgentConnection`。当 `prompt()` 被调用时：
1. 调用 `Thread::run_turn()` 从语言模型流式获取补全
2. 将事件（文本、工具调用、工具结果）转发到 `AcpThread` 供 UI 渲染

## 5. 工具系统

### AgentTool trait

`agent/src/thread.rs:3464` 定义：

```rust
pub trait AgentTool: 'static + Sized {
    type Input: Deserialize + Serialize + JsonSchema;
    type Output: Deserialize + Serialize + Into<LanguageModelToolResultContent>;
    const NAME: &'static str;
    fn description() -> SharedString;
    fn kind() -> acp::ToolKind;
    fn run(self: Arc<Self>, input, event_stream, cx) -> Task<Result<Self::Output, Self::Output>>;
    // + initial_title, input_schema, replay, erase
}
```

### 内置工具列表

| 类别 | 工具 |
|------|------|
| 文件 I/O | `read_file_tool`, `edit_file_tool`, `write_file_tool` |
| 文件系统 | `list_directory_tool`, `create_directory_tool`, `delete_path_tool`, `move_path_tool`, `copy_path_tool` |
| 搜索 | `grep_tool`, `find_path_tool` |
| LSP 操作 | `go_to_definition_tool`, `find_references_tool`, `get_code_actions_tool`, `apply_code_action_tool`, `rename_tool` |
| 诊断 | `diagnostics_tool` |
| 终端 | `terminal_tool` |
| Web | `fetch_tool`, `web_search_tool` |
| Agent | `spawn_agent_tool`（子 Agent，深度限制为 1） |
| 其他 | `skill_tool`（用户自定义 Skill）, `update_plan_tool`, `context_server_registry` |

### MCP Context Server 集成

`context_server/` crate 实现 MCP 客户端，支持协议版本 `2024-11-05` 到 `2025-11-25`。

**注册路径：**
```
Extension
  → extension_host_proxy
  → ContextServerDescriptorRegistryProxy
  → ContextServerStore
  → ContextServerRegistry
  → 包装为 AnyAgentTool
  → NativeAgent 可用
```

- 每个 MCP 工具 ID 格式：`mcp:<server_id>:<tool_name>`
- 支持 **stdio**（子进程）和 **HTTP** 两种传输方式
- Extension 通过 `ExtensionContextServerProxy` 机制注册 Context Server

## 6. UI 层

### AgentPanel

`agent_ui/src/agent_panel.rs` — GPUI Panel（dock widget）：
- 切换 NativeAgent / Custom Agent
- 管理当前活跃的 `AcpThread`（会话）
- 创建/切换/归档/删除线程

### ConversationView

`agent_ui/src/conversation_view.rs` — 会话渲染：
- 消息列表（用户消息、助手消息、工具调用）
- 消息编辑器 + 补全/提及支持
- 工具权限提示（允许一次/总是允许/拒绝）
- Follow 模式、流式文本、重试

### AgentConfiguration

`agent_ui/src/agent_configuration.rs` — 配置 UI：
- LLM 提供商配置
- Context Server 配置
- Profile 管理（按 Profile 自定义工具）
- 模型选择

## 7. 完整数据流

```
用户在 AgentPanel 输入
  → ConversationView 发送消息
  → AcpThread.prompt()
  → AgentConnection.prompt() 分发到：
      [NativeAgent 路径]
        → NativeAgentConnection.run_turn()
        → Thread.run_turn()
        → LanguageModel.stream_completion()
        → 工具执行循环（AgentTool::run）
        → 事件转发到 AcpThread
      [外部 Agent 路径]
        → AcpConnection.prompt()
        → JSON-RPC "prompt" 发送到子进程
        → 流式事件通过 stdio 接收
        → 通过 channel 分发到 AcpThread
  → AcpThread 发出事件
  → ConversationView 渲染更新
```

## 8. 线程持久化

- `ThreadStore`（`agent/src/thread_store.rs`）— 全局 GPUI 实体，管理线程元数据
- `ThreadsDatabase`（通过 `db` crate）— 持久化存储线程数据
- `ThreadMetadataStore` 和 `TerminalThreadMetadataStore` — UI 层元数据
- 会话通过 `acp::SessionId`（基于 UUID）标识

## 9. 关键文件索引

| 组件 | 文件路径 |
|------|----------|
| NativeAgent 核心 | `crates/agent/src/agent.rs` |
| Thread 对话循环 | `crates/agent/src/thread.rs` |
| ThreadStore | `crates/agent/src/thread_store.rs` |
| AgentTool trait | `crates/agent/src/thread.rs:3464` |
| 所有内置工具 | `crates/agent/src/tools/` |
| ContextServerRegistry | `crates/agent/src/tools/context_server_registry.rs` |
| NativeAgentServer | `crates/agent/src/native_agent_server.rs` |
| AgentServer trait | `crates/agent_servers/src/agent_servers.rs` |
| AcpConnection | `crates/agent_servers/src/acp.rs` |
| CustomAgentServer | `crates/agent_servers/src/custom.rs` |
| AgentConnection trait | `crates/acp_thread/src/connection.rs` |
| AcpThread 实体 | `crates/acp_thread/src/acp_thread.rs` |
| Agent Panel UI | `crates/agent_ui/src/agent_panel.rs` |
| ConversationView | `crates/agent_ui/src/conversation_view.rs` |
| AgentConnectionStore | `crates/agent_ui/src/agent_connection_store.rs` |
| Agent Settings | `crates/agent_settings/src/agent_settings.rs` |
| MCP Client | `crates/context_server/src/client.rs` |
| Agent Server Store | `crates/project/src/agent_server_store.rs` |

## 10. 设计亮点

1. **双路径架构**：NativeAgent 和外部 Agent 共享同一 `AgentConnection` 接口，UI 层无需关心后端差异
2. **前台线程隔离**：GPUI 的 `!Send` 约束通过 `unbounded` channel 优雅解决，ACP 子进程的 inbound 请求安全分发到前台
3. **工具统一抽象**：内置工具和 MCP 工具都通过 `AnyAgentTool` 统一，NativeAgent 无差别调用
4. **ACP 外部 crate**：协议类型独立为 `agent-client-protocol` crate，外部 Agent 实现者可直接引用
5. **Extension 注册链**：MCP Server 通过 Extension Host → Proxy → Store → Registry 的完整链路注册，解耦清晰

---

关联：[[acp-protocol]] — ACP 协议通用参考 | [[multica-acp-integration]] — Multica 的 ACP 集成实践 | [[context-mode]] — AI 编码上下文优化 | [[heuristic-learning]] — Agent 学习范式

---

## 最新动态（截至 2026-06-28）

> [!note] ACP 协议层获行业背书，本文分析的 `agent-client-protocol` crate 影响力扩大
> 本笔记分析的 Zed Agent 双路径架构（NativeAgent + ACP 外部）所依赖的 ACP 协议，在 2025 下半年获得 **Google + JetBrains** 联合支持（详见 [[zed]] 最新动态）。这验证了本文第 4 点设计决策——"ACP 外部 crate 独立为 `agent-client-protocol`，外部 Agent 实现者可直接引用"——的前瞻性：该 crate 正成为跨编辑器 agent 接入的事实标准。

### 对本文架构分析的影响
- **双路径架构价值提升**：NativeAgent（内置）+ ACP（外部）的分离，让 Zed 既能自研 agent，又能接入任何遵循 ACP 的第三方 agent（含 JetBrains 生态）
- **MCP 注册链不变**：Extension Host → Proxy → Store → Registry 的 MCP 注册机制仍是核心，2026 无架构级改动
- 详细的 ACP 协议演进见 [[zed]] 和 [[acp-protocol]]
