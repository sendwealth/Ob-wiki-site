---
title: Zed — 高性能多人协作代码编辑器
created: 2026-05-22
updated: 2026-06-28
type: entity
tags: [product, editor, rust, ai-coding, collaboration, open-source, platform, active]
sources: [~/Projects/zed/, https://zed.dev/, https://en.wikipedia.org/wiki/Zed_(text_editor)]
confidence: high
---

# Zed

> 由 Atom 和 Tree-sitter 创始人打造的 Rust 代码编辑器：GPU 加速渲染、实时多人协作、内置 AI Agent 系统、236 个 crate 模块化架构

---

## 基本信息

| 属性 | 值 |
|------|-----|
| **创建者** | Nathan Sobo（Atom 联合创建者） |
| **公司** | Zed Industries |
| **语言** | Rust（100%） |
| **许可** | GPL-3.0-or-later（crates）、AGPL（编辑器主体） |
| **平台** | macOS、Linux、Windows |
| **仓库** | github.com/zed-industries/zed |
| **官网** | zed.dev |
| **Slogan** | "Your last next editor" |

## 产品定位

Zed 是一个高性能、多人协作的代码编辑器，从零开始用 Rust 编写，目标是成为 VS Code 的下一代替代品。核心差异化：

1. **GPU 加速渲染** — 自研 GPUI 框架，利用 GPU 实现极低延迟渲染
2. **实时协作** — 内置多人编辑、语音通话、Channel 频道
3. **AI 原生** — 内置 Agent 系统（NativeAgent + 外部 Agent ACP 集成）、内联补全、Copilot 集成
4. **极速体验** — 多核 CPU 利用 + 零延迟交互，2026 年被认为"第一个重新让人感到原生"的编辑器

## 核心架构

### 236 个 Crate 模块化设计

Zed 采用极致的模块化设计，236 个 workspace crate 各司其职：

```
zed/
├── crates/
│   ├── gpui/              # 自研 GPU UI 框架（核心）
│   ├── editor/             # 编辑器核心
│   ├── language/           # 语言服务抽象层
│   ├── project/            # 项目管理
│   ├── workspace/          # 工作区管理
│   ├── agent/              # 内置 AI Agent
│   ├── agent_servers/      # Agent 服务端抽象
│   ├── acp_thread/         # ACP 协议线程
│   ├── agent_ui/           # Agent 面板 UI
│   ├── context_server/     # MCP 客户端
│   ├── collab/             # 实时协作
│   ├── dap/                # 调试适配器协议
│   ├── copilot/            # GitHub Copilot 集成
│   ├── extension/          # 扩展系统
│   ├── edit_prediction/    # 内联补全
│   └── ...（236 crates total）
├── docs/                   # 文档
└── assets/                 # 资源文件
```

### GPUI — 自研 UI 框架

GPUI 不仅是 UI 框架，还提供状态管理和并发原语：
- 单前台线程渲染 + 后台线程异步工作
- `Entity<T>` 句柄模式（类似 React ref + state）
- `Context<T>` 提供全局状态访问
- `cx.spawn` / `cx.background_spawn` 并发模型
- Flexbox 布局 + 类 Tailwind CSS 样式 API

### Agent 系统架构

Zed 的 AI Agent 系统是其核心差异化功能（详见 [[zed-agent-architecture]]）：

```
用户输入 → AgentPanel(UI) → AcpThread → AgentConnection → 后端
                                                        ├─ NativeAgent（内置，LLM 直连）
                                                        └─ AcpConnection（外部 Agent，ACP JSON-RPC）
```

- **内置 Agent**（"Zed Agent"）— 直接调用语言模型，17+ 内置工具
- **外部 Agent** — 通过 ACP 协议连接 Claude、Gemini、Codex 等
- **MCP 集成** — Context Server 注册链，扩展可用工具

## 关键功能

### 编辑器核心
- Tree-sitter 语法高亮（29+ 语言）
- LSP 集成（自动安装 language server）
- 多缓冲区（Multibuffer）— 跨文件编辑
- 诊断面板、代码操作、重命名、引用跳转
- Vim / Helix 键绑定支持
- Git 集成（diff、blame、历史）

### AI 功能
- Agent 面板 — 与 AI Agent 对话式编程
- 内联补全（Copilot / Supermaven / 自研模型）
- Agent Profile 系统 — 按场景定制工具集
- Skill 系统 — `.agents/skills/` 加载自定义技能
- 工具权限审批 — 允许一次/总是允许/拒绝

### 协作功能
- 实时多人编辑（CRDT-free，基于 OT）
- 语音通话（WebRTC）
- Channel 频道
- 共享项目

### 调试
- DAP（Debug Adapter Protocol）集成
- 断点、变量查看、调用栈
- Dev Container 支持

### 扩展系统
- WASM 扩展沙箱
- 语言扩展、主题扩展、Icon 主题
- Slash 命令
- Context Server（MCP）注册

## 强项语言

Rust、Go、TypeScript、Python — 对这些语言提供一流的智能补全和诊断支持。

## 技术栈

| 层级 | 技术 |
|------|------|
| UI 框架 | GPUI（自研，GPU 加速） |
| 编辑器 | 自研（非 Electron） |
| 语法 | Tree-sitter |
| LSP | Language Server Protocol |
| AI Agent | ACP (Agent Client Protocol) |
| AI Tools | MCP (Model Context Protocol) |
| 调试 | DAP (Debug Adapter Protocol) |
| 协作 | 自研（WebSocket + OT） |
| 扩展 | WASM 沙箱 |
| 语言模型 | Anthropic / Google / OpenAI / Azure 等 |

## 历史与定位

| 时间 | 事件 |
|------|------|
| 2017 | Atom 达到巅峰，Nathan Sobo 开始构思下一代编辑器 |
| 2022 | Zed 项目公开，Zed Industries 成立 |
| 2024 | macOS 公开发布，获 YC 支持 |
| 2025 | Linux / Windows 版本发布，开源 |
| 2026 | AI Agent 系统成熟，ACP 协议成为行业标准（与 JetBrains 合作） |

## 与竞品对比

| 特性 | Zed | VS Code | Cursor |
|------|-----|---------|--------|
| 渲染 | GPU（原生） | Electron（Chromium） | Electron |
| 语言 | Rust | TypeScript | TypeScript |
| AI Agent | 内置 Native + ACP 外部 | 扩展 | 内置 |
| 协作 | 内置实时 | Live Share 扩展 | 无 |
| 扩展 | WASM（安全沙箱） | Node.js（完全权限） | 同 VS Code |
| 启动速度 | 极快（<100ms） | 较慢（~2s） | 较慢 |
| 内存占用 | 低 | 高 | 高 |

## 数据

- 236 个 workspace crate
- 活跃开发（每日多个 PR 合并）
- 支持 29+ 语言的语法高亮
- 内置 Agent 工具：文件读写、搜索、LSP 操作、终端、Web、子 Agent

## 局限与争议

- 扩展生态远不如 VS Code（WASM 沙箱限制能力）
- Electron 迁移成本高（现有 VS Code 用户粘性）
- 部分高级功能（如远程开发）仍在完善
- 商业模式依赖 Zed Business（团队协作功能）
- AGPL 许可对商业使用有约束

---

## 最新动态（截至 2026-06-28）

> [!note] ACP 从"Zed 协议"升级为"编辑器↔Agent 开放标准"
> Zed 主推的 **Agent Client Protocol (ACP)** 在 2025 下半年获得 **Google + JetBrains** 双背书，正成为把 AI agent 从 VS Code 锁定中解放出来的开放标准。2026 年 Zed stable 持续加 agentic 特性。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| ACP 支持方 | Zed 单一 | **Zed + Google + JetBrains**（2025-10 联合声明）|
| 产品定位 | 高性能编辑器 | **"AI code editor built for agentic workflows"** |
| 新特性 | — | 自动 context compaction、`/compact` 命令、UI 优化 |

### ACP 成为行业事件
- **Google 联合推动**：The Register 报道 Google 和 Zed 共推 ACP，目标"把 AI agent 从 VS Code 的锁定中撬出来"
- **JetBrains 加入**：2025-10 JetBrains × Zed 联合声明，让 ACP agent 可在 JetBrains IDE 内运行——对 [[acp-protocol]] 生态的重大扩张
- **自托管 agent**：社区教程涌现"用 ACP 在 Zed 内跑本地 agent"

### 战略意义
ACP 让 Zed 不再只是"快编辑器"，而是 **agent-native IDE 标准的制定者**。与 [[claude-code-game-studios]]（agent 文件塑造行为）、[[superpowers]]（技能注入）形成对照——Zed 选的是"协议层"路线。

### 仍待观察
- ACP 能否真正撼动 VS Code + Copilot 的统治地位
- 自动 compaction 的质量与 token 效率

关联：[[zed-agent-architecture]] — Zed Agent 系统深度分析 | [[acp-protocol]] — ACP 协议参考 | [[context-mode]] — AI 编码上下文优化 | [[heuristic-learning]] — Agent 学习范式

Sources:
- [Zed Official Site](https://zed.dev/)
- [Zed Wikipedia](https://en.wikipedia.org/wiki/Zed_(text_editor))
- [Graphite: Zed vs VS Code](https://graphite.com/guides/zed-editor-next-gen-vs-code-alternative)
