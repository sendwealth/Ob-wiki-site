---
title: ACP (Agent Client Protocol) 深度技术参考
created: 2026-05-20
updated: 2026-05-20
type: concept
tags: [acp, agent-protocol, editor, json-rpc, mcp, interoperability, zed, jetbrains]
---

# ACP (Agent Client Protocol) 深度技术参考

> Zed Industries + JetBrains 联合推动的开放协议，标准化 **代码编辑器/IDE** 与 **AI 编码 Agent** 之间的通信。
> 类比：LSP 之于语言服务 = ACP 之于 AI Agent
> Source: https://agentclientprotocol.com/ | GitHub: https://github.com/agentclientprotocol/agent-client-protocol

## 一、定位与价值

### 1.1 解决什么问题

```
当前 AI 编码 Agent 生态碎片化：

┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ Claude   │  │ Codex    │  │ Gemini   │  │ Copilot  │
│ Code     │  │          │  │ CLI      │  │          │
└─────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
      │             │             │              │
      └─────────────┴──────┬──────┴──────────────┘
                           │
                     ACP Protocol
                  （统一编辑器通信层）
```

每个 Agent-编辑器组合都需要定制集成，导致：
- **集成开销大**：每个新组合都要定制开发
- **兼容性受限**：Agent 只能在少数编辑器中使用
- **开发者锁定**：选了 Agent 就被锁定在其生态

ACP 一次实现，任意编辑器可用。**解耦 Agent 和编辑器**，两边独立创新。

### 1.2 与 MCP / A2A 的关系

| 维度 | ACP | MCP (Model Context Protocol) | A2A (Agent-to-Agent) |
|------|-----|------------------------------|----------------------|
| 定位 | 编辑器 ↔ Agent 通信 | Agent ↔ 工具/资源 连接 | Agent ↔ Agent 协作 |
| 类比 | 老板给员工派活 | 员工使用工具 | 员工之间协作 |
| 粒度 | 编辑层协议（调度） | 资源层协议（主从） | 应用层协议（对等） |
| 核心 | Session、Prompt Turn、Tool 权限 | 工具描述、调用、结果 | 发现、任务、协商 |

```
User → 编辑器 (ACP Client)
         │
         ├── ACP ──→ Agent (ACP Server)
         │              │
         │              ├── MCP ──→ 文件系统
         │              ├── MCP ──→ API
         │              └── MCP ──→ 数据库
         │
         │              ├── A2A ──→ Agent B
         │              └── A2A ──→ Agent C
```

**三者互补**：ACP 让编辑器调度 Agent，MCP 让 Agent 使用工具，A2A 让 Agent 之间协作。

## 二、核心设计原则

| 原则 | 说明 |
|------|------|
| **MCP-friendly** | 基于 JSON-RPC，复用 MCP 的 JSON 类型（不需要发明新的数据表示） |
| **UX-first** | 专为 AI Agent 交互设计，支持 diff 展示、实时进度流、权限控制 |
| **Trusted** | 信任模型下工作，编辑器授权 Agent 访问本地文件和 MCP Server |

## 三、架构

### 3.1 通信模型

```
┌─────────────────┐                    ┌─────────────────┐
│   编辑器 (Client) │ ◄── JSON-RPC ──► │  Agent (Server)  │
│                 │    stdio / HTTP    │                 │
│  - Zed          │                    │  - Claude Code   │
│  - JetBrains    │                    │  - Codex         │
│  - VS Code      │                    │  - Copilot       │
│  - ...          │                    │  - ...           │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │  转发 MCP Server 配置                  │  Agent 可直连
         └──────── MCP Server ──────────────────┘
```

### 3.2 传输方式

| 模式 | 传输 | 场景 |
|------|------|------|
| **本地 Agent** | JSON-RPC over stdio | Agent 作为编辑器子进程 |
| **远程 Agent** | HTTP / WebSocket | Agent 部署在云端（开发中） |

### 3.3 关键特性

- **多会话并发**：一个连接支持多个并行 Session（多条思维线索同时进行）
- **实时流式更新**：通过 JSON-RPC notification 推送 Agent 进度
- **双向请求**：Agent 可向 Client 请求权限（如 Tool Call 审批）
- **MCP 透传**：编辑器将 MCP Server 配置转发给 Agent，Agent 可直连 MCP Server

## 四、协议生命周期

### 4.1 完整流程

```
阶段 1: 初始化
  Client → Agent:  initialize       ← 协商版本和能力
  Client → Agent:  authenticate     ← 认证（如果 Agent 要求）

阶段 2: 会话建立（二选一）
  Client → Agent:  session/new      ← 创建新会话
  Client → Agent:  session/load     ← 恢复已有会话（需 loadSession 能力）

阶段 3: Prompt Turn（核心交互循环）
  Client → Agent:  session/prompt   ← 发送用户消息
  Agent → Client:  session/update   ← 流式进度通知（可多次）
  Agent → Client:  文件操作/权限请求  ← Agent 请求编辑器协助
  Client → Agent:  session/cancel   ← 用户中断（可选）
  Agent → Client:  session/prompt 响应 ← 返回最终结果 + stop reason

阶段 3 可重复多次（多轮对话）
```

### 4.2 Agent 方法一览

#### 基线方法（必须实现）

| 方法 | 说明 |
|------|------|
| `initialize` | 版本协商 + 能力交换 |
| `authenticate` | 认证（如需） |
| `session/new` | 创建新会话 |
| `session/prompt` | 发送用户 Prompt |

#### 可选方法

| 方法 | 说明 | 前置能力 |
|------|------|---------|
| `session/load` | 恢复已有会话 | `loadSession` |
| `session/set_mode` | 切换 Agent 操作模式 | — |

### 4.3 Agent 通知（Agent → Client）

| 通知 | 说明 |
|------|------|
| `session/update` | 流式进度更新（文本、diff、tool 状态等） |
| `session/task_started` | Agent 开始处理子任务 |
| `session/task_completed` | 子任务完成 |

### 4.4 Client 方法一览

Client 也有方法供 Agent 调用（双向 JSON-RPC）：

| 方法 | 说明 |
|------|------|
| `fs/read` | Agent 请求读取文件 |
| `fs/write` | Agent 请求写入文件 |
| `tool/call` | Agent 请求执行工具 |
| `tool/permission` | Agent 请求工具调用权限 |

## 五、核心能力

### 5.1 内容类型

| 能力 | 说明 |
|------|------|
| **文本内容** | Markdown 格式的用户可读文本（默认格式） |
| **Diff 展示** | Agent 可发送代码 diff，编辑器以原生 diff UI 渲染 |
| **Tool Calls** | Agent 调用工具，Client 控制权限审批 |
| **文件系统** | Agent 可读写编辑器工作区的文件 |
| **终端** | Agent 可执行终端命令 |
| **Agent Plan** | Agent 展示执行计划，用户可审批 |

### 5.2 会话模式

Agent 支持多种操作模式（如编码模式、问答模式），通过 `session/set_mode` 切换。

### 5.3 斜杠命令

Agent 可声明支持的斜杠命令（如 `/fix`、`/explain`），编辑器据此展示可用命令列表。

## 六、与 MCP 的深度集成

```
┌─────────────────┐                    ┌─────────────────┐
│   编辑器 (Client) │                    │  Agent (Server)  │
└────────┬────────┘                    └────────┬────────┘
         │                                      │
         │  1. session/prompt                    │
         │     + mcpServers: [{name, config}]   │
         │─────────────────────────────────────►│
         │                                      │
         │                                      │  2. Agent 使用 MCP config
         │                                      │     直连 MCP Server
         │                                      │────────────────►
         │                                      │                 MCP Server
         │                                      │◄────────────────
         │                                      │
```

编辑器在转发用户 Prompt 时，附带已配置的 MCP Server 信息。Agent 获得配置后**直连** MCP Server（不经编辑器中转），减少延迟。

## 七、可扩展性

| 机制 | 说明 |
|------|------|
| `_meta` 字段 | 在标准消息中附加自定义数据 |
| `_` 前缀方法 | 定义自定义方法（如 `_myAgent/customAction`） |
| 能力声明 | 初始化时声明自定义能力，Client 据此调整行为 |

## 八、协议约定

| 约定 | 规则 |
|------|------|
| 消息格式 | JSON-RPC 2.0 |
| 对象属性 | `camelCase` |
| 判别字段值 | `snake_case` |
| 文件路径 | **必须**绝对路径 |
| 行号 | 1-based |
| 错误处理 | 标准 JSON-RPC 2.0 error object（`code` + `message`） |

## 九、SDK 生态

| 语言 | 状态 |
|------|------|
| Kotlin | 官方支持 |
| Java | 官方支持 |
| Python | 官方支持 |
| Rust | 官方支持 |
| TypeScript | 官方支持 |

## 十、ACP Registry

ACP 提供 Agent 注册中心（Registry），编辑器可从中发现可用的 Agent，无需手动配置。

## 十一、与 Multica 的关联思考

Multica 作为 AI 原生任务管理平台，ACP 的设计有多个可借鉴点：

| ACP 概念 | Multica 对应 | 启示 |
|----------|-------------|------|
| Session | Agent Runtime Session | 统一会话管理，支持多会话并行 |
| Tool Call Permission | Agent 任务审批流 | 用户控制 Agent 操作权限 |
| MCP 透传 | Agent 可访问外部工具 | Agent 通过统一接口访问 MCP 工具生态 |
| Prompt Turn | Task 执行循环 | Agent 处理 Issue 的交互循环 |
| Agent Plan | Task 执行计划展示 | 向用户展示 Agent 将如何处理任务 |
| Client Notifications | 前端实时更新 | WS 推送 Agent 进度（已实现） |
| ACP Registry | Agent Runtime 发现 | 用标准化的方式发现和注册 Agent |

ACP 与 A2A 的关系：ACP 管「编辑器如何调度 Agent」，A2A 管「Agent 之间如何协作」。Multica 可以同时参考两者——内部用 ACP 思路管理 Agent 与平台的交互，Agent 之间用 A2A 思路协作。

## 十二、关键参考

| 资源 | 链接 |
|------|------|
| 官网 | https://agentclientprotocol.com/ |
| GitHub | https://github.com/agentclientprotocol/agent-client-protocol |
| llms.txt | https://agentclientprotocol.com/llms.txt |
| 背后公司 | Zed Industries (zed.dev) + JetBrains |
| 关联 | [[a2a-protocol]]、[[multica]]、[[multica-runtime-discovery]]、[[adk-python]] |
