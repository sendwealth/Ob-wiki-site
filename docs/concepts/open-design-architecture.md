---
title: Open Design 项目架构分析
created: 2026-05-20
updated: 2026-05-20
type: concept
tags: [architecture, typescript, nextjs, electron, monorepo, ai, design, local-first, agent, skill-system]
sources:
  - https://github.com/nicepkg/open-design
  - ~/Projects/open-design
  - docs/architecture.md
  - docs/spec.md
  - docs/skills-protocol.md
confidence: high
related:
  - "[[opensource-practices-from-open-design]]"
  - "[[design-md-spec]]"
  - "[[langflow-architecture]]"
---

# Open Design 项目架构分析

> Open Design (OD) 是一个本地优先的开源 AI 设计工具，检测用户已安装的 coding agent CLI（Claude Code、Codex、Gemini CLI 等），运行设计技能 + 设计系统，将生成的设计作品流式推送到沙箱预览中。本文从系统拓扑、组件架构、数据流、部署模型和安全模型五个维度分析其架构设计。

---

## 1. 项目定位与设计哲学

OD 的核心定位是对标 Anthropic 的 Claude Design，但**开源、本地优先、不限模型**。核心理念：

- **不造 agent**：最强 coding agent 已经在用户机器上了，OD 只负责将它们接入设计工作流
- **BYOK（Bring Your Own Key）**：每一层都支持用户自带 API key
- **Skill-driven**：设计能力通过可组合的 Skill 文件定义，而非硬编码
- **本地优先**：所有数据在本地 SQLite，不出站遥测，不出站分析

项目站在四个开源肩膀上：
- `alchaincyf/huashu-design` — 设计哲学指南针
- `VoltAgent/awesome-design-md` — 70+ 品牌设计系统来源
- `badlogic/pi-mono` — 交互式 UI 设计（Agent 面板、导出格式）
- `multica-ai/multica` — daemon-and-runtime 架构（PATH-scan agent 检测）

---

## 2. 三种部署拓扑

OD 支持三种部署模式，从完全本地到纯云端：

### Topology A — 完全本地（默认）

```
Browser → Daemon (localhost:7456) → Agent CLI (本地进程)
```

Daemon + Web 都在本地运行，通过 `pnpm tools-dev` 一键启动。所有数据在 `~/.od/` 或项目目录 `.od/`。

### Topology B — Web on Vercel + Daemon 本地

```
Browser → Vercel (Web SPA) → Daemon (localhost:7456) → Agent CLI
```

Web 前端部署到 Vercel，通过 CORS 连接本地 Daemon。适合团队共享同一套 UI。

### Topology C — Web on Vercel + Direct API（无 Daemon）

```
Browser → Vercel (Web SPA) → Anthropic/OpenAI API (BYOK)
```

纯浏览器模式，无本地进程。功能有限（无 agent 工具调用、无文件系统），但零安装。

---

## 3. 组件架构图

```
┌─────────────────────────────── Web App ─────────────────────────────┐
│                                                                     │
│  ┌──────────┐  ┌─────────────┐  ┌───────────┐  ┌────────────────┐  │
│  │ chat pane│  │ artifact    │  │ preview   │  │ comment /      │  │
│  │          │  │ tree        │  │ iframe    │  │ slider overlay │  │
│  └────┬─────┘  └──────┬──────┘  └─────┬─────┘  └────────┬───────┘  │
│       └─────────── session bus (in-memory) ──────────────┘           │
│                           │                                          │
│              Transport layer (daemon SSE | api-direct | browser)      │
└──────────────────────────┬──────────────────────────────────────────┘
                           │
┌──────────────────────────┴─────────────────────────────────────────┐
│                        Local Daemon                                │
│  session manager      skill registry                              │
│  agent adapter pool   design-system resolver                      │
│  artifact store       preview compile pipeline                    │
│  export pipeline      detection service                           │
└──────┬──────────────────────────────────────────┬─────────────────┘
       │                                          │
┌──────┴──────────┐                       ┌───────┴──────────┐
│  Agent CLIs     │                       │   filesystem     │
│  claude         │                       │   ./.od/         │
│  codex          │                       │   ~/.od/         │
│  cursor-agent   │                       │   skills/         │
│  gemini         │                       │   DESIGN.md       │
│  opencode       │                       └──────────────────┘
│  qwen           │
└─────────────────┘
```

---

## 4. 关键组件详解

### 4.1 Web App（Next.js 16 App Router + React 18）

- **为什么用 Next.js 而非 Vite SPA？** SSR 用于营销落地页 + Vercel 部署是首要公民
- **状态管理**：React/browser state 管理 UI 配置，projects/conversations/files 从 daemon API 获取
- **iframe 预览**：内嵌 React 18 + Babel standalone 用于 JSX 作品渲染
- **评论模式**：点击捕获 `[data-od-id]` DOM 元素，打开浮层，发送精确编辑指令给 agent
- **Slider UI**：agent 输出 "tweak parameter" 工具调用时，Web 渲染实时更新控件

### 4.2 Local Daemon（`od daemon`）

Daemon 是核心枢纽，职责包括：

- 监听 `http://localhost:7456`，接受 `/api/*` REST/SSE 路由
- 维护每个 Web Tab 的 **session**（活跃 agent、skill、artifact、设计系统引用）
- 运行 **agent adapter pool**：检测到的每个 CLI 对应一个 adapter 实例，跨 session 复用
- 扫描和索引 **skills**（`~/.claude/skills/`、`./skills/`、`./.claude/skills/`），启动时 + FS-watch
- 管理 **artifact store**（文件写入磁盘，不存内存）
- 运行 **preview compile pipeline**（Babel 转换 JSX、CSS 内联 HTML 导出）
- 提供导出钩子：HTML / PDF / ZIP / PPTX / Markdown

### 4.3 Agent Adapter Pool

每个支持的 CLI 有一个 adapter，负责：

- **路径扫描**：检测用户机器上安装了哪些 coding agent
- **协议适配**：将 OD 的统一接口翻译为各 CLI 的调用方式
  - Claude Code → 原生 tool loop，精确编辑
  - Codex → 重生成文件 + "只修改元素 X" 约束
  - API fallback → 同 Codex 路径

### 4.4 Skill Registry

Skills 是 OD 的核心扩展机制：

```
发现优先级（高 → 低）:
1. ./.claude/skills/    → 项目私有，不提交 git
2. ./skills/            → 项目提交
3. ~/.claude/skills/    → 用户全局
```

支持 symlink 策略（借鉴 `cc-switch`）：一个 skill 安装到 `~/.open-design/skills/`，自动链接到各 agent 的目录。

### 4.5 Design-System Resolver

加载活跃的 `DESIGN.md` 文件，注入为 skill 上下文。内置 **129 个设计系统**（Linear、Stripe、Apple、Tesla、小红书等）。

### 4.6 Artifact Store

项目范围的文件夹（默认 `./.od/`），存储：
- 生成的文件
- 版本快照（git-friendly）
- 每个 artifact 的元数据

### 4.7 Export Pipeline

支持五种格式导出：HTML（内联）、PDF、PPTX、ZIP、Markdown。

---

## 5. 核心数据流：一次 "生成原型" 的完整流程

```
1. 用户在 Web 聊天框输入 prompt
2. Web 发送 POST /api/chat (SSE) 到 Daemon

3. Daemon：
   a. 选择活跃 skill（如 prototype-skill）
   b. 加载 design-system（DESIGN.md）
   c. 在 ./.od/artifacts/<slug>/ 创建 artifact 目录
   d. 调用 agent adapter：
        - system: SKILL.md 内容 + DESIGN.md
        - user: 原始 prompt
        - cwd: 新 artifact 目录
   e. 流式返回 agent 事件：
        - "tool_call"（编辑/写入/读取文件）
        - "text_delta"
        - "thinking"

4. Web 展示：
   - 侧面板运行中的 tool-call
   - artifact tree 随文件生成实时更新
   - preview iframe 加载主要输出文件
   - slider/comment overlay 激活

5. 完成后 Daemon 追加 history.jsonl

6. 用户评论元素 → Web 发送 refine 请求
   → Daemon 重新调用 agent 执行精确编辑
```

---

## 6. HTTP API 设计

Daemon 暴露统一的 HTTP + SSE 接口：

```
GET  /api/health
GET  /api/agents                    # 检测到的 agent 列表
GET  /api/skills                    # 可用 skills
GET  /api/design-systems            # 可用设计系统
GET  /api/projects                  # 项目列表
POST /api/projects                  # 创建项目
POST /api/import/folder             # 文件夹导入
GET  /api/projects/:id/files        # 项目文件
POST /api/projects/:id/upload       # 上传文件
POST /api/chat                      # → text/event-stream（核心聊天接口）
POST /api/artifacts/save            # 保存 artifact
POST /api/runs/:id/tool-result      # 向运行中的 agent 反馈 tool_result
POST /api/proxy/{anthropic,openai,azure,google}/stream  # API 代理
```

所有 API DTO 定义在 `packages/contracts`，Web 和 Daemon 共享。

---

## 7. Monorepo 结构

```
open-design/
├── apps/
│   ├── web/              # Next.js 16 前端
│   ├── daemon/           # 本地守护进程 + od CLI
│   ├── desktop/          # Electron 桌面壳
│   ├── packaged/         # 打包发行版入口
│   ├── landing-page/     # 营销落地页
│   └── telemetry-worker/ # 遥测 worker
├── packages/
│   ├── contracts/        # Web/Daemon 共享 DTO（纯 TS）
│   ├── sidecar-proto/    # Sidecar 协议定义
│   ├── sidecar/          # 通用 Sidecar 运行时
│   ├── platform/         # 通用 OS 进程原语
│   ├── plugin-runtime/   # 插件运行时
│   ├── registry-protocol/# 注册表协议
│   └── agui-adapter/     # AG-UI 适配器
├── tools/
│   ├── dev/              # 开发生命周期控制面板
│   ├── pack/             # 打包/发布控制面板
│   ├── pr/               # PR 管理控制面板
│   └── serve/            # 本地 fixture 服务
├── skills/               # 31 个内置设计技能
├── design-systems/       # 129 个品牌设计系统
├── design-templates/     # 渲染模板目录
├── craft/                # 通用品牌无关工艺规则
├── assets/               # 设备边框、prompt 模板等
├── e2e/                  # E2E 测试（Playwright + Vitest）
└── docs/                 # 文档
```

技术栈：Node ~24 + pnpm 10.33.2 + TypeScript 5.9 + Hono HTTP。

---

## 8. 安全模型

- **无出站遥测**：OD 是 local-first，唯一的出站调用是用户明确配置的 provider
- **API 代理**：内部 IP/SSRF 在 daemon 边缘阻断
- **Desktop 文件夹导入**：HMAC-SHA256 token 认证，单次使用，60s TTL
  - 桌面启动时生成 32-byte secret，注册到 daemon
  - 文件夹选择时铸造 HMAC token，daemon 验证后放行
  - fail-closed 设计：一旦注册过 secret，gate 永不放松
- **沙箱 iframe**：预览在 sandboxed iframe 中运行，限制 scripts + same-origin

---

## 9. 性能设计

- **文件在磁盘**：artifact store 写入真实文件，不占内存
- **SSE 流式**：chat 通过 SSE 流式返回，用户实时看到 agent 进度
- **chokidar 监听**：skill 变更实时检测，无需重启
- **sidecar IPC**：desktop 通过 IPC 发现 web URL，不猜端口
- **并行 typecheck**：`pnpm typecheck` 以 workspace-concurrency=4 并行执行

---

## 10. 架构亮点与可借鉴模式

| 模式 | 说明 | 适用场景 |
|------|------|---------|
| **Agent Adapter Pool** | 统一接口适配多种 CLI agent | 需要对接多个异构外部工具时 |
| **Skill Registry + 三级优先级** | 项目级 > 项目提交 > 全局 | 可扩展的能力注册机制 |
| **Daemon as Single Privileged Process** | 唯一有特权的本地进程 | 本地优先应用的安全模型 |
| **BYOK at Every Layer** | 每层都支持用户自带 key | 不锁定 provider 的商业模式 |
| **Topology A/B/C** | 三种部署拓扑覆盖从本地到云端 | 渐进式部署策略 |
| **contracts 包** | 纯 TS DTO 层，前后端共享 | monorepo 中的类型安全通信 |
| **tools/ 控制面板模式** | dev/pack/pr/serve 各自独立 CLI | 开发工具链的组织方式 |
