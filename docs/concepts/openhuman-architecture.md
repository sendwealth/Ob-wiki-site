---
title: OpenHuman 技术架构深度解析
created: 2026-05-18
updated: 2026-05-18
type: concept
tags: [ai, agent, rust, react, tauri, architecture, desktop, event-bus, domain-driven-design]
sources:
  - ~/Projects/openhuman
  - https://github.com/tinyhumansai/openhuman
confidence: high
related:
  - "[[opensource-project-practices-from-openhuman]]"
  - "[[lobechat-architecture]]"
  - "[[langflow-architecture]]"
---

# OpenHuman 技术架构深度解析

> OpenHuman 是一个面向社区的 AI 助手，采用 **Rust 核心 + React/Tauri v2 桌面壳** 架构。核心理念：Rust 是权威真相源（authoritative），前端只负责展示和编排。

## 1. 整体架构：三层分离

```
┌─────────────────────────────────────────────────┐
│           Tauri 桌面壳 (app/src-tauri)           │
│  窗口管理 · 进程生命周期 · CDP扫描 · 原生通知     │
├─────────────────────────────────────────────────┤
│           React 前端 (app/src)                   │
│  Redux状态 · Service单例 · 路由 · Provider链      │
├─────────────────────────────────────────────────┤
│           Rust 核心 (src/)                       │
│  域逻辑 · RPC控制器 · 事件总线 · 持久化 · CLI      │
└─────────────────────────────────────────────────┘
```

**关键决策**：Core 作为 tokio 任务运行在 Tauri 进程内（[[#6-进程内运行模型]]），不是 sidecar。前端通过 `core_rpc_relay` IPC → HTTP `127.0.0.1:<port>/rpc` 访问核心，bearer token 认证。

### 1.1 仓库布局

| 路径 | 角色 |
|------|------|
| `app/` | pnpm workspace：Vite + React 前端 + Tauri 桌面壳 |
| `src/` (root) | Rust lib crate `openhuman` + CLI binary `openhuman-core` |
| `src/core/` | 传输层：Axum/HTTP、JSON-RPC、CLI、事件总线 |
| `src/openhuman/*` | 40+ 业务域（agent、channels、cron、memory...） |
| `gitbooks/developing/` | 公开贡献者文档 |
| `scripts/debug/` | Agent 友好的测试运行器封装 |

---

## 2. Rust 核心：域驱动设计

### 2.1 域目录结构

```
src/openhuman/
├── agent/          # AI代理执行
├── channels/       # 社区频道连接
├── composio/       # 能力矩阵
├── config/         # TOML配置 + 环境变量覆盖
├── cron/           # 定时任务
├── memory/         # 记忆管线
├── skills/         # 技能元数据（运行时已移除）
├── threads/        # 对话线程
├── tools/          # 工具系统
├── webhooks/       # Webhook处理
└── ... (40+ 域)
```

每个域遵循统一结构：
- `mod.rs` — 导出焦点，不写业务逻辑
- `rpc.rs` / `schemas.rs` — RPC 控制器 + schema 注册
- `ops.rs` — 操作逻辑
- `store.rs` — 持久化
- `types.rs` — 域类型

### 2.2 控制器注册模式

OpenHuman 用**注册表模式**而非路由分支：

```rust
// src/openhuman/<domain>/schemas.rs
fn all_registered_controllers() -> Vec<RegisteredController>
fn all_controller_schemas() -> Vec<ControllerSchema>
fn handle_XXX(params: Map<String, Value>) -> ControllerFuture
```

- 控制器通过 `src/core/all.rs` 统一注册，不在 `cli.rs` / `jsonrpc.rs` 中添加域分支
- 共享 schema 类型：`ControllerSchema`、`FieldSchema`、`TypeSchema`（`src/core/types.rs`）
- 返回值统一使用 `RpcOutcome<T>` 模式

**对比** [[lobechat-architecture|LobeChat]] 的插件注册：LobeChat 在前端用 plugin manifest，OpenHuman 在 Rust 端用编译时注册表，两者都追求"新增功能不改框架代码"。

---

## 3. 事件总线：中枢神经系统

`src/core/event_bus/` 实现两种通信面：

### 3.1 广播 Pub/Sub

```
publish_global(event) → 多订阅者 → 无返回值
```

- 底层 `tokio::sync::broadcast`
- 一对多，fire-and-forget
- 用于通知："消息已接收"、"技能已加载"

### 3.2 原生请求/响应

```
register_native_global("domain.verb", handler)
request_native_global("domain.verb", req) → Response
```

- 一对一，按方法名字符串分发
- **零序列化**：直接传递 `Arc`、`mpsc::Sender`、`oneshot::Sender`
- 仅限进程内使用；JSON-RPC 可调用的走 `src/core/all.rs`

### 3.3 域事件设计

`DomainEvent` 是 `#[non_exhaustive]` 枚举，域包括：`agent`、`memory`、`channel`、`cron`、`skill`、`tool`、`webhook`、`system`。每个域有 `bus.rs` 定义 `EventHandler` 实现（如 `CronDeliverySubscriber`、`WebhookRequestSubscriber`）。

**新增事件流程**：添加 `DomainEvent` 变体 → 扩展 `domain()` match → 创建 `<domain>/bus.rs` → 注册订阅者 → 通过 `publish_global` 发布。

---

## 4. 前端架构

### 4.1 Provider 链

```
Sentry.ErrorBoundary
  → Redux Provider
    → PersistGate (redux-persist)
      → BootCheckGate
        → CoreStateProvider (fetchCoreAppSnapshot RPC)
          → SocketProvider
            → ChatRuntimeProvider
              → HashRouter
                → CommandProvider
                  → ServiceBlockingGate
                    → AppShell
```

**注意**：没有 `UserProvider` / `AIProvider` / `SkillProvider`。认证和核心快照在 `CoreStateProvider` 中，通过 RPC 获取（token 不在 redux-persist 中，存储在进程内核心）。

### 4.2 状态管理

- Redux Toolkit slices：`accounts`、`channelConnections`、`chatRuntime`、`coreMode`、`socket`、`thread` 等
- `redux-persist` 持久化部分 slice
- 临时 UI 状态（如 upsell 弹窗标记）用 `localStorage`
- **配置集中化**：`app/src/utils/config.ts` 读取 `VITE_*`，其他模块不直接用 `import.meta.env`

### 4.3 Service 层

单例服务：`apiClient`、`socketService`、`coreRpcClient` + `coreCommandClient`（通过 Tauri IPC 的 HTTP 桥接）、`chatService`、`analytics`、`notificationService`、`webviewAccountService`、`daemonHealthService`。

---

## 5. Tauri 壳：薄交付层

Tauri 壳 (`app/src-tauri/`) 只做平台交付，不写业务逻辑：

- **核心生命周期**：`CoreProcessHandle` 启动 JSON-RPC server 为 tokio 任务，bearer token 认证
- **CDP 扫描器**：每个 Provider（Discord、Slack、Telegram、WhatsApp 等）有独立 scanner 模块
- **CEF Webview**：嵌入式第三方页面（Telegram、LinkedIn、Slack 等）**零 JS 注入** — 所有抓取通过 CDP 从外部完成
- **原生能力**：通知、屏幕截图、语音热键、窗口状态、摄像头

### 5.1 CEF 安全策略

第三方 webview 不得添加新 JS 注入。这是硬约束：
- 不新增 `.js` 文件
- 不扩展 `build_init_script` / `RUNTIME_JS`
- 不使用 `Page.addScriptToEvaluateOnNewDocument`
- 新行为只能通过 CEF handlers 或 CDP scanner 模块实现

---

## 6. 进程内运行模型

```
Tauri 主进程
├── GUI 线程
├── Core tokio 任务 (HTTP :7788/rpc)
│   ├── JSON-RPC handler
│   ├── Event bus
│   └── Domain logic
└── CDP/scanner 线程们
```

- PR #1061 移除了 sidecar 二进制
- `CoreProcessHandle` 拥有核心生命周期，Cmd+Q 时核心随 GUI 一起退出
- 调试可用 `OPENHUMAN_CORE_REUSE_EXISTING=1` 连接到外部进程
- 认证：每启动生成 hex bearer token，前端通过 `core_rpc_token` Tauri command 获取

---

## 7. 双 Socket 实时基础设施

OpenHuman 使用双 socket 同步架构：
- `socketService` — 主实时通信
- MCP transport — 工具协议层

修改实时协议时必须保持两端对齐（参见 architecture.md 双 socket 章节）。

---

## 8. 技术栈总结

| 层 | 技术 | 用途 |
|----|------|------|
| 桌面壳 | Tauri v2 (CEF) | 跨平台窗口、IPC、原生API |
| 前端 | React + Vite + Redux Toolkit | UI、状态管理、路由 |
| 后端核心 | Rust (Axum + tokio) | 业务逻辑、RPC、事件总线 |
| 传输 | JSON-RPC over HTTP | 前端↔核心通信 |
| 实时 | Socket.io | 双向推送 |
| 测试 | Vitest + WDIO + cargo test | 单元、集成、E2E |
| 构建 | pnpm workspace | Monorepo 管理 |

---

## 核心启示

> **OpenHuman 的架构哲学是"Rust 权威、前端薄壳"。**
>
> 所有业务逻辑在 Rust 核心中以域为单位组织，通过注册表模式暴露给 RPC/CLI，前端仅负责呈现和编排。事件总线提供进程内零序列化的域间通信。这种分层使得：
> 1. 核心可以独立测试（不依赖 GUI）
> 2. 前端替换不影响业务逻辑
> 3. 新增域只需遵循固定模式（`mod.rs` + `schemas.rs` + `rpc.rs`），不需要修改框架代码
>
> 与 [[lobechat-architecture|LobeChat]] 的纯 TypeScript 架构对比：OpenHuman 选择 Rust 换取性能和安全边界，但代价是更高的开发门槛和更复杂的调试链路。两者共通的是**域驱动组织 + 注册表暴露 + 事件解耦**。
