---
title: Multica
created: 2026-05-11
updated: 2026-06-28

type: entity
tags: [product, ai, platform, active, project]
sources: [~/Projects/multica]
confidence: high
---

# Multica

> AI 原生的任务管理平台 —— 像 Linear，但 AI Agent 是一等公民。开源，支持 11 种编码 Agent（Claude Code、Codex、Copilot、OpenClaw、Hermes 等），面向 2-10 人 AI-native 团队。

---

## 一、项目定位

Multica（**Mul**tiplexed **I**nformation and **C**omputing **A**gent）致敬 1960 年代的 Multics 操作系统——当时多用户共享一台机器，如今人类和 AI Agent 共享一个任务系统。

核心理念：**Agent 是团队的一等成员**，拥有头像、名称、技能，可以被分配 Issue、参与评论、主动报告阻塞。

- 官网：https://multica.ai
- 开源：github.com/multica-ai/multica
- 对标：Linear + AI Agent 管理
- 许可证：开源可自托管

## 二、技术栈总览

```
┌──────────────┐     ┌──────────────┐     ┌──────────────────┐
│   Next.js    │────>│  Go Backend  │────>│   PostgreSQL     │
│   Frontend   │<────│  (Chi + WS)  │<────│   (pgvector)     │
└──────────────┘     └──────┬───────┘     └──────────────────┘
                            │
                     ┌──────┴───────┐
                     │ Agent Daemon │  本地运行
                     └──────────────┘  (Claude Code, Codex, Copilot, OpenClaw, ...)
```

| 层 | 技术 |
|---|---|
| 前端 Web | Next.js 16 (App Router) |
| 前端桌面 | Electron (electron-vite) |
| 后端 | Go (Chi router, sqlc, gorilla/websocket) |
| 数据库 | PostgreSQL 17 + pgvector |
| 缓存 | Redis（可选，多节点生产环境） |
| 存储 | S3 或本地文件存储 |
| 包管理 | pnpm workspaces + Turborepo |
| CI | GitHub Actions (Node 22, Go 1.26.1) |
| 部署 | Docker Compose / GoReleaser CLI |

## 三、后端架构（Go）

### 3.1 路由与中间件

入口 `server/cmd/server/main.go` → `NewRouterWithOptions()` 构建完整 Chi 路由。

```
server/
  cmd/server/main.go      # 启动入口
  cmd/daemon/main.go      # 守护进程 CLI 入口
  internal/
    handler/              # HTTP handler（每个资源一个文件）
      issue.go, agent.go, runtime.go, comment.go,
      workspace.go, skill.go, chat.go, autopilot.go,
      auth.go, file.go, feedback.go, ...
    auth/                 # JWT 认证
    middleware/            # 中间件（CORS、workspace scope）
    daemonws/              # Daemon WebSocket Hub
      hub.go               # 连接管理、事件分发、去重
    realtime/              # 前端 WebSocket Hub
    events/                # 事件总线
    service/               # 业务逻辑层（邮件、任务唤醒）
    storage/               # 文件存储抽象（S3 / 本地）
    migrations/            # 数据库迁移
    analytics/             # PostHog 分析
    mention/               # @提及展开
    metrics/               # Prometheus HTTP 指标
```

中间件链：CORS → Recoveryer → RequestID → Logger → 认证 → Workspace scope。

### 3.2 数据库层（sqlc）

所有 SQL 查询手写在 `server/pkg/db/queries/*.sql`，通过 sqlc 生成类型安全的 Go 代码到 `server/pkg/db/generated/`。

**核心表：**
- `workspace` — 多租户隔离，slug 唯一标识，issue_counter 自增
- `user` — 用户，邮箱 + OAuth 登录
- `member` — workspace 成员关系
- `agent` — AI Agent 定义（name, runtime_id, instructions, custom_env, custom_args, mcp_config, model）
- `agent_runtime` — 运行时（daemon_id, provider, status, last_seen_at）
- `issue` — 任务（assignee_type + assignee_id 多态：member 或 agent）
- `comment` / `issue_reaction` — 评论和反应
- `skill` — 可复用技能（content 即 SKILL.md 正文）
- `agent_task_queue` — 任务队列（queued → dispatched → running → completed/failed/cancelled）
- `activity` — 活动流
- `inbox` / `notification_preference` — 通知
- `chat_session` / `task_message` — Agent 对话
- `project` / `label` / `subscriber` — 项目管理

### 3.3 WebSocket 协议

**前端 WS**（`realtime.Hub`）：服务端 → 浏览器的事件广播。

**Daemon WS**（`daemonws.Hub`）：服务端 ↔ Daemon 的双向通信，支持事件去重（128 条缓存）。

核心事件类型（`pkg/protocol/events.go`）：

| 类别 | 事件 |
|------|------|
| Issue | `issue:created/updated/deleted` |
| Task | `task:queued/dispatch/progress/completed/failed/cancelled/message` |
| Agent | `agent:status/created/archived/restored` |
| Comment | `comment:created/updated/deleted/resolved` |
| Chat | `chat:message/done/session_read/session_deleted` |
| Skill | `skill:created/updated/deleted` |
| Workspace | `workspace:updated/deleted` |

消息格式：`{ "type": "task:completed", "payload": {...} }`

### 3.4 Agent 运行时管理

`server/pkg/agent/` 定义统一的 `Backend` 接口：

```go
type Backend interface {
    Execute(ctx context.Context, prompt string, opts ExecOptions) (*Session, error)
}
```

支持 11 种 Agent 实现：
- `claude.go` — Claude Code（stream-json 模式，SDK 协议）
- `codex.go` — OpenAI Codex（app-server 子命令）
- `copilot.go` — GitHub Copilot CLI（JSON 模式）
- `openclaw.go` — OpenClaw（JSON 模式）
- `opencode.go` — OpenCode（JSON 模式）
- `hermes.go` — Hermes Agent（ACP 协议）
- `gemini.go` — Gemini CLI（stream-json 模式）
- `pi.go` — Pi Agent
- `cursor.go` / `cursor_invocation.go` — Cursor Agent
- `kimi.go` — Kimi（ACP 协议）
- `kiro.go` — Kiro CLI（ACP 协议）

每种实现封装了 CLI 调用、stdout 解析、消息流转换。`Session` 提供两个 channel：
- `Messages` — 实时事件流（text、thinking、tool-use、tool-result、status、error）
- `Result` — 最终结果（success/failure/timeout + token 用量）

### 3.5 任务生命周期

```
Issue 分配给 Agent
    ↓
task:queued（入队，status=queued）
    ↓
task:dispatch（Daemon 认领，status=dispatched）
    ↓
Agent 开始执行（status=running）
    ↓ task:progress（实时进度）
    ↓ task:message（消息流）
    ↓
task:completed / task:failed / task:cancelled
```

Daemon 通过 WS 接收 `task:dispatch`，调用对应 Agent Backend 的 `Execute()`，实时发送 `task:message` 和 `task:progress`。

### 3.6 多租户

所有查询以 `workspace_id` 过滤。HTTP 请求通过 `X-Workspace-ID` header 或 URL slug 确定工作空间。成员关系（`member` 表）控制访问权限。

## 四、前端架构（TypeScript Monorepo）

### 4.1 包结构

```
packages/
  core/        — 无头业务逻辑（零 react-dom，跨平台复用）
    api/         API client + WS client + zod schema
    auth/        认证 store
    agents/      Agent queries + presence
    issues/      Issue queries + mutations
    inbox/       收件箱
    skills/      技能管理
    chat/        对话
    autopilots/  自动驾驶模式
    modals/      模态框 store
    onboarding/  引导流程
    platform/    CoreProvider + NavigationAdapter + StorageAdapter
    pins/        Pin 管理

  ui/          — 原子 UI 组件（shadcn/Base UI，零业务逻辑）
  views/       — 共享业务页面（零 next/*，零 react-router）
  tsconfig/    — 共享 TypeScript 配置

apps/
  web/         — Next.js App Router（唯一允许 next/* 的地方）
    app/         路由页面
    platform/    Next.js 平台适配（cookies, redirects, searchParams）

  desktop/     — Electron 桌面应用
    src/
      main/       主进程
      renderer/   渲染进程
      platform/   react-router-dom 导航适配
```

### 4.2 平台桥接模式

`CoreProvider`（`packages/core/platform/`）是跨平台的核心：
- 初始化 ApiClient、Auth Store、Chat Store、WS 连接、QueryClient
- 每个应用包裹 `<CoreProvider>` 并提供自己的 `NavigationAdapter`
- Web 用 Next.js `next/navigation`，Desktop 用 `react-router-dom`

### 4.3 状态管理（严格分层）

| 状态类型 | 管理方案 | 规则 |
|---------|---------|------|
| 服务端数据 | TanStack Query | WS 事件触发 invalidation，永不手动写入 store |
| 客户端 UI | Zustand | 存放在 `packages/core/`，两个 app 共享 |
| 跨切面 | React Context | 仅 WorkspaceIdProvider、NavigationProvider |

**硬性规则：**
- 永远不把服务端数据复制到 Zustand
- workspace 范围的 query 必须以 `wsId` 为 cache key
- Mutation 默认乐观更新（optimistic）
- WS 事件只做 invalidation，不直接写 store

### 4.4 包边界（硬约束）

- `packages/core/` — 零 react-dom、零 localStorage、零 process.env
- `packages/ui/` — 零 `@multica/core` 导入
- `packages/views/` — 零 `next/*`、零 react-router-dom，用 `NavigationAdapter` 路由
- `apps/web/platform/` — 唯一放 Next.js API 的地方
- `apps/desktop/platform/` — 唯一放 react-router-dom 的地方

## 五、Agent 集成机制

### 5.1 CLI 检测与 Runtime 发现

Daemon 启动时自动扫描 PATH 上的 Agent CLI（11 种 provider），检测版本后注册到服务端，再通过心跳保活。详细机制见 [[multica-runtime-discovery]]。

支持的 provider：claude, codex, copilot, opencode, openclaw, hermes, gemini, pi, cursor-agent, kimi, kiro-cli。

### 5.2 A2A 协议支持

Daemon 即将支持 A2A（Agent-to-Agent）协议 v1.0（PR [#2613](https://github.com/multica-ai/multica/pull/2613) review 中），可通过 JSON-RPC 2.0 连接任何符合规范的远程 Agent，无需本地安装 CLI。支持配置文件发现、本地端口扫描、注册中心轮询三种发现模式，SSE 流式进度、任务取消、认证透传。详见 [[multica-a2a]]。

### 5.2 Agent 配置

每个 Agent 实体可配置：
- `runtime_id` — 绑定到哪个运行时
- `instructions` — 系统指令
- `custom_env` — 自定义环境变量
- `custom_args` — 追加到 CLI 的参数
- `mcp_config` — MCP 服务器配置（传给 `--mcp-config`）
- `model` — 指定模型
- `max_concurrent_tasks` — 最大并发任务数

### 5.3 技能系统（Skill）

Agent 执行任务后可将解决方案保存为可复用 Skill（`skill` 表），供整个团队使用。Skill 内容为 SKILL.md 格式，包含 YAML frontmatter + 步骤说明。

## 六、CLI 工具

`multica` CLI（Go 编写，GoReleaser 多平台构建）：

| 命令 | 功能 |
|------|------|
| `multica setup` | 一键配置 + 登录 + 启动 daemon |
| `multica setup self-host` | 自托管部署版 |
| `multica daemon start` | 启动本地 Agent 运行时 |
| `multica daemon status` | 查看 daemon 状态 |
| `multica login` | 浏览器认证 |
| `multica issue list/create` | Issue 管理 |
| `multica update` | 升级到最新版本 |

## 七、关键设计决策

1. **Internal Packages 模式** — 共享包导出原始 .ts/.tsx 文件（不预编译），消费方的 bundler 直接编译，零配置 HMR + 即时跳转定义。

2. **API 响应兼容性** — 桌面端版本永远落后于服务端。所有 API 响应用 `parseWithFallback`（zod schema + fallback）解析，验证失败返回 fallback 而非崩溃。每个 switch 必须有 default 分支。

3. **Worktree 支持** — 所有 checkout 共享一个 PostgreSQL 容器，隔离在数据库层面（每个 worktree 独立 DB + 端口）。

4. **去中心化 Agent 执行** — Daemon 在用户机器上运行 Agent CLI，服务端只做调度和状态管理。

5. **Reserved Slug 单一来源** — `server/internal/handler/reserved_slugs.json` 是唯一真实来源，TS 端自动生成，CI 校验 drift。

## 八、开发命令速查

```bash
make dev              # 一键启动（环境 + DB + 迁移 + 服务）
make check            # 完整验证流水线
pnpm typecheck        # TypeScript 类型检查
pnpm test             # TS 单元测试（Vitest）
make test             # Go 测试
make server           # 仅启动后端（:8080）
pnpm dev:web          # 仅启动前端（:3000）
pnpm dev:desktop      # Electron 开发
make sqlc             # 重新生成 sqlc 代码
make db-reset         # 重置数据库
```

---

## 最新动态（截至 2026-06-28）

> [!note] 2026 年主线：从"任务管理"进化为"Agent 自动化平台"
> 2026 changelog 显示 Multica 在补齐 Autopilot（自动化）能力，让 Agent 不只是被分配任务，而是能自己跑流程。

### 2026 新增能力

1. **CLI Autopilot** — 管理 scheduled 和 triggered 自动化，Agent 可按计划/事件自动执行任务（对应 [[multica-loop-agent]] 的全闭环实践）
2. **GitHub Copilot CLI 内建** — 把 Copilot CLI 作为内置 daemon 管理，扩大支持的编码 Agent 范围
3. **Immersive Mode** — 沉浸式模式，减少干扰，专注单任务流
4. **Auto-update Autopilot** — Autopilot 自身支持自动更新（呼应社区 issue #2410 对"频繁发布"的反馈）

### 生态扩展信号

- **Runtime 扩展**：社区 issue #3480 请求增加 kilo CLI 作为 runtime，说明 Multica 的 runtime 抽象层在吸引新 agent 接入
- **发布节奏加快**：issue #2410 反映"release cadence 太频繁"，侧面证明项目活跃度高
- **定位演进**：tagline 更新为 "Turn coding agents into real teammates — assign tasks, track progress, compound skills"，强调 **compound skills（技能复利）** 这一新叙事

### 与原始调研（2026-05）的差异

- 原调研聚焦"11 种编码 Agent + 任务管理"，2026 版重心转向**自动化编排 + 技能复利**
- A2A / Runtime 发现等机制已落地为生产特性（详见 [[multica-a2a]]、[[multica-runtime-discovery]]）

## 相关链接

- [[multica-runtime-discovery]] — Runtime 发现、注册、心跳、健康状态机制
- [[multica-a2a]] — A2A 协议支持：远程 Agent 接入
- [[heuristic-learning]] — coding agent 学习范式
- [[context-mode]] — AI 编码 Agent 上下文优化
- [[agentic-rag]] — Agentic RAG 架构
