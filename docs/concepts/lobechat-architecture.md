# LobeChat 架构分析

> LobeChat 是 LobeHub 开源的高质量 AI 对话应用，支持多种 LLM 提供商、插件系统、多平台部署（Web / Mobile / Desktop）。本文从架构层面分析其设计思路。

## 技术栈

| 层级 | 技术 | 说明 |
|------|------|------|
| 前端框架 | React 19 + Vite | SPA 构建，HMR |
| 后端框架 | Next.js 16 (App Router) | API 路由、SSR 认证页 |
| 类型安全 API | tRPC | 前后端端到端类型安全 |
| 状态管理 | Zustand | 轻量响应式 store |
| 数据获取 | SWR | 缓存 + 重新验证策略 |
| UI 组件 | @lobehub/ui + antd | 自有组件库 + antd 基础 |
| 样式 | antd-style (CSS-in-JS) | 优先 `createStaticStyles` 零运行时方案 |
| 数据库 | PostgreSQL + Drizzle ORM | 类型安全 SQL，自动迁移 |
| 国际化 | react-i18next | 16+ 语言 |
| 测试 | Vitest + Cucumber + Playwright | 单元 + E2E |
| 桌面端 | Electron + electron-vite | 独立构建流程 |
| 包管理 | pnpm monorepo | 74+ 共享包 |

## 整体架构：Next.js 后端 + Vite SPA 前端

LobeChat 最独特的架构决策是将 **Next.js 作为纯后端**，**Vite 作为纯前端**。两者不是传统的 Next.js SSR 模式，而是一种混合架构：

```
┌─────────────────────────────────────────────────┐
│  用户浏览器                                      │
│  ┌──────────────────────────────────────────┐   │
│  │  Vite SPA (React 19)                     │   │
│  │  ├── React Router (客户端路由)            │   │
│  │  ├── Zustand (状态管理)                   │   │
│  │  ├── SWR (数据获取)                       │   │
│  │  └── tRPC Client ←→ Next.js tRPC Server  │   │
│  └──────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
                    ↓ tRPC / REST
┌─────────────────────────────────────────────────┐
│  Next.js App Router (后端)                       │
│  ├── /api/trpc/*   → tRPC 路由                   │
│  ├── /api/webapi/* → Web API                     │
│  ├── /api/auth/*   → BetterAuth 认证             │
│  ├── /spa          → SPA HTML 模板服务            │
│  └── /public/_spa/ → Vite 构建产物               │
└─────────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────────┐
│  基础设施层                                       │
│  ├── PostgreSQL (Drizzle ORM)                    │
│  ├── Redis (缓存 + 队列)                         │
│  ├── S3 兼容存储 (RustFS / MinIO)               │
│  └── AI Providers (OpenAI, Anthropic, Google...) │
└─────────────────────────────────────────────────┘
```

### 为什么这样设计？

1. **前端性能**：Vite 的 HMR 速度远快于 Next.js 的 Webpack/Turbopack，开发体验更好
2. **灵活部署**：SPA 可以独立部署到 CDN，后端只需 Next.js 服务器
3. **类型安全**：tRPC 保证前后端 API 类型完全一致，无需手写 API 客户端
4. **认证兼容**：Next.js 保留 SSR 能力处理认证页面（需要服务端 session）

### 构建流程

```
bun run build
  → build:spa       (Vite 构建 SPA → dist/)
  → build:spa:copy  (复制到 public/_spa/)
  → build:next      (Next.js 构建，包含 SPA 产物)
```

## Monorepo 结构

```
lobehub/
├── apps/
│   ├── desktop/              # Electron 桌面端
│   │   ├── src/main/         #   主进程 (独立 workspace)
│   │   ├── src/renderer/     #   渲染进程
│   │   └── src/common/       #   共享代码
│   └── cli/                  # CLI 工具
│
├── packages/                 # 74+ 共享包 (@lobechat/*)
│   ├── database/             #   数据库 schema + repository
│   ├── agent-runtime/        #   Agent 运行时核心
│   ├── model-runtime/        #   模型调用运行时
│   ├── tool-runtime/         #   工具执行运行时
│   ├── utils/                #   共享工具函数
│   ├── types/                #   TypeScript 类型
│   ├── const/                #   常量定义
│   ├── chat-adapter-*/       #   聊天平台适配器 (LINE, Slack, Telegram...)
│   ├── builtin-tool-*/       #   内置工具 (计算器, 网页浏览, 记忆...)
│   └── business/             #   业务逻辑包
│       ├── config/           #     业务配置
│       └── model-runtime/    #     模型运行时业务逻辑
│
├── src/                      # 主应用源码
│   ├── app/                  #   Next.js App Router (后端 API)
│   ├── spa/                  #   SPA 入口 + 路由配置
│   ├── routes/               #   SPA 页面组件 (路由树)
│   ├── features/             #   业务功能模块 (领域驱动)
│   ├── store/                #   Zustand 状态管理
│   ├── services/             #   客户端服务层
│   ├── server/               #   服务端逻辑
│   └── locales/              #   国际化翻译
│
├── locales/                  #   多语言 JSON 文件
├── e2e/                      #   E2E 测试
└── docker-compose/           #   Docker 配置
```

## SPA 路由架构

路由采用 **roots vs features** 分层模式：

- **`src/routes/` (roots)**：只放路由段文件（layout + page），不包含业务逻辑
- **`src/features/`**：按领域组织的业务组件，routes 从这里导入

```
src/spa/
├── entry.web.tsx             # Web 入口
├── entry.mobile.tsx          # Mobile 入口
├── entry.desktop.tsx         # Desktop 入口
├── entry.popup.tsx           # Popup 入口
└── router/
    ├── desktopRouter.config.tsx         # 桌面端路由
    ├── desktopRouter.config.desktop.tsx # 桌面 App 路由（必须同步）
    ├── mobileRouter.config.tsx          # 移动端路由
    └── popupRouter.config.tsx           # 弹窗路由
```

> 两个 desktop 路由配置必须保持同步（路径和嵌套），否则会导致白屏。有 `desktopRouter.sync.test.tsx` 测试守护这个约束。

## 状态管理

使用 Zustand，按领域划分 store：

```
src/store/
├── global/       # 全局状态（系统设置、客户端 DB）
├── page/         # 页面 CRUD、列表、选择
├── brief/        # 摘要相关
└── eval/         # 测试用例、基准测试
```

每个 store slice 遵循统一结构：
```
store-slice/
├── initialState.ts
├── action.ts
├── reducer.ts
└── selectors/
    └── index.ts
```

## 服务层

### 客户端服务 (`src/services/`)

按业务领域组织：

| 服务 | 职责 |
|------|------|
| `aiAgent/` | AI Agent 管理 |
| `aiChat/` | AI 对话 |
| `aiModel/` | 模型配置 |
| `aiProvider/` | LLM 提供商管理 |
| `chat/` | 聊天会话 |
| `message/` | 消息管理 |
| `file/` | 文件上传下载 |
| `skill/` | 技能/插件 |
| `topic/` | 话题管理 |
| `userMemory/` | 用户记忆 |

### 服务端 (`src/server/`)

```
src/server/
├── routers/
│   ├── lambda/    # 核心后端路由 (50+ 端点)
│   ├── mobile/    # 移动端子集
│   └── tools/     # 工具相关端点
└── modules/
    ├── AgentRuntime/   # Agent 运行时模块
    ├── Mecha/          # Mecha 模块
    ├── ModelRuntime/   # 模型运行时模块
    └── PluginStore/    # 插件商店模块
```

## 数据库层

```
packages/database/
├── src/
│   ├── schemas/        # Drizzle schema 定义
│   │   ├── aiInfra.ts
│   │   ├── chatGroup.ts
│   │   ├── userMemories/
│   │   └── relations.ts
│   └── repositories/   # Repository 模式
│       ├── agentGroup/
│       ├── dataExporter/
│       ├── dataImporter/
│       ├── userMemory/
│       └── compression/
└── migrations/         # 自动生成的迁移
```

## Agent 运行时

核心 Agent 系统位于 `packages/agent-runtime/`：

| 组件 | 职责 |
|------|------|
| `runtime.ts` | 主运行时逻辑 |
| `InterventionChecker.ts` | Agent 干预检查 |
| `UsageCounter.ts` | 用量追踪 |
| `event.ts` | 事件系统 |
| `generalAgent.ts` | 通用 Agent 实现 |
| `instruction.ts` | 指令系统 |
| `state.ts` | Agent 状态管理 |
| `hooks.ts` | 生命周期钩子 |

## 多平台支持

| 平台 | 入口 | 路由配置 | 构建工具 |
|------|------|----------|----------|
| Web | `entry.web.tsx` | `desktopRouter.config.tsx` | Vite |
| Mobile | `entry.mobile.tsx` | `mobileRouter.config.tsx` | Vite |
| Desktop App | `entry.desktop.tsx` | `desktopRouter.config.desktop.tsx` | electron-vite |
| Popup | `entry.popup.tsx` | `popupRouter.config.tsx` | Vite |

### Electron 桌面端

```
apps/desktop/
├── src/main/       # 主进程（独立 workspace）
│   ├── core/App.ts
│   └── index.ts
├── src/renderer/   # 渲染进程
└── src/common/     # 共享（路由定义等）
```

特性：多窗口支持、IPC 通信、文件系统集成、网络代理。

## 开发模式

```bash
# SPA 开发（前端 only，代理 API 到 localhost:3010）
bun run dev:spa

# 全栈开发（Next.js + Vite 并行）
bun run dev
```

`dev:spa` 启动后提供 Debug Proxy URL，可以在本地 Vite 开发服务器和线上后端之间建立代理，实现 HMR + 真实后端数据。

## 国际化

- 翻译文件：`src/locales/default/`（默认语言 key）
- 多语言 JSON：`locales/{zh-CN,en-US,...}/`
- 工具：`@lobehub/i18n-cli`，支持 JSON 和 Markdown 翻译
- 支持 16+ 语言

## 测试策略

| 类型 | 工具 | 位置 |
|------|------|------|
| 单元测试 | Vitest | 与源码同目录 |
| E2E 测试 | Cucumber + Playwright | `e2e/` |
| 类型检查 | TypeScript | `bun run type-check` |

> 注意：不要运行 `bun run test`（全量测试约 10 分钟），应运行特定文件。

## 部署

- **Docker**：多阶段构建，`docker-compose/` 下有不同环境配置
- **Vercel**：原生支持，`next.config.ts` 有 Vercel 优化
- **基础设施**：PostgreSQL + Redis + S3 兼容存储 + SearXNG（搜索）

## 架构亮点总结

1. **Next.js 后端 + Vite 前端**：兼顾 Next.js 生态（认证、API）和 Vite 开发体验
2. **tRPC 端到端类型安全**：前后端共享 API 类型，编译期发现错误
3. **Monorepo + 74+ 包**：极致的模块化，清晰的职责边界
4. **Roots vs Features**：路由层只做路由，业务逻辑在 features 中
5. **Repository 模式**：数据库访问通过 Repository 抽象，易于测试和替换
6. **Agent 运行时**：可扩展的 Agent 框架，支持多种工具和模型
7. **多平台统一**：Web/Mobile/Desktop/Popup 共享核心代码，平台差异在入口和路由层处理

## 关键学习点

### 何时参考这个项目

- 需要设计 **Next.js + Vite 混合架构**时
- 需要实现 **tRPC 全栈类型安全**时
- 需要设计 **多平台 SPA 路由系统**时
- 需要参考 **大型 React 项目 monorepo 组织**时
- 需要实现 **AI Agent 运行时框架**时
- 需要参考 **Electron + Web 共存的多平台架构**时

### 架构模式

| 模式 | 应用场景 |
|------|----------|
| Monorepo Workspace | 多包共享、独立版本 |
| Repository Pattern | 数据库访问抽象 |
| Feature-Based Organization | 业务模块隔离 |
| Adapter Pattern | 聊天平台适配（LINE, Slack, Telegram） |
| Event-Driven | Agent 运行时事件系统 |
| Zero-Runtime CSS | `createStaticStyles` 性能优化 |

---

*源码：[github.com/lobehub/lobe-chat](https://github.com/lobehub/lobe-chat)*
*分析日期：2025-05-15*
*版本：v2.1.57*
