---
title: Open Design 项目亮点分析
created: 2026-05-21
updated: 2026-06-28
type: entity
tags: [ai, platform, open-source, multi-agent, design-tools]
sources: [https://github.com/nexu-io/open-design]
confidence: high
---

# Open Design

> Open Design 是一个创新的 AI 驱动设计工具平台，将多个 AI 编码助手统一到协作环境中，专注于设计原型、演示文稿和模板的快速生成。采用多 Agent 适配器架构、Sidecar 进程隔离、双轨能力暴露（UI+CLI）等创新设计。

---

## 项目概述

Open Design 是一个创新的 AI 驱动设计工具平台，它将多个 AI 编码助手（Claude Code、Codex、Cursor Agent 等）统一到一个协作环境中，专注于设计原型、演示文稿和模板的快速生成。

## 核心亮点

### 1. 多 Agent 适配器架构

**统一接口，多样选择**

Open Design 最突出的创新是其 Agent 适配器池（Agent Adapter Pool）架构。它不是绑定单一 AI 模型，而是提供了一个统一的适配器接口，支持多种主流 AI 编码助手：

- **Claude Code**（参考实现）
- **Codex**（OpenAI）
- **Cursor Agent**
- **GitHub Copilot CLI**
- **Gemini CLI**
- **Qoder CLI**
- **DeepSeek TUI**
- **Devin for Terminal**

**能力驱动的 UI**

系统根据检测到的 Agent 能力动态调整 UI。例如：
- 如果 Agent 支持原生技能加载，优先使用
- 如果不支持，降级到提示词注入
- 如果都不支持，使用文件放置工作流

这种设计让用户可以根据任务特性、成本考虑或个人偏好灵活切换 Agent，而不需要改变工作流程。

### 2. Skills 协议与设计系统

**可扩展的技能生态**

Open Design 定义了一套 Skills Protocol，将设计知识和工作流封装为可复用的技能模块：

```yaml
---
name: guizang-ppt-skill
description: Generate presentation decks using Guizang design system
od:
  modes: [deck]
  design-system: guizang
  craft:
    requires: [typography, color-theory]
  capabilities:
    required: [file_write, web_search]
---
```

**三层内容架构**

1. **skills/** - 功能性技能（工具、简报、打包器）
2. **design-templates/** - 渲染目录（演示文稿、原型、媒体模板）
3. **design-systems/** - 品牌 DESIGN.md 文件
4. **craft/** - 通用品牌无关的设计规则

这种分层让设计系统可以独立演进，技能可以跨品牌复用，大大提高了可维护性。

### 3. Sidecar 进程隔离架构

**安全的多实例运行**

Open Design 使用 Sidecar 模式实现进程隔离：

```typescript
// 进程标记包含五个字段
{
  app: 'daemon' | 'web' | 'desktop',
  mode: 'dev' | 'packaged',
  namespace: string,  // 隔离边界
  ipc: string,        // IPC 路径
  source: string      // 启动来源
}
```

**命名空间隔离**

- 每个命名空间有独立的数据目录、日志路径、IPC socket
- 支持同时运行多个实例而不冲突
- 测试环境与开发环境完全隔离
- POSIX IPC sockets 固定在 `/tmp/open-design/ipc/<namespace>/<app>.sock`

这种设计让 Playwright E2E 测试可以在不影响开发环境的情况下运行，也支持未来的多租户场景。

### 4. 双轨能力暴露（UI + CLI）

**强制的可组合性**

Open Design 有一个独特的设计原则：每个用户功能必须同时通过 Web UI 和 CLI 暴露。

```bash
# CLI 示例
od automation list --json
od plugin install design-system-guizang
od project create --name "My Deck" --mode deck
od media generate --prompt "Hero image" --style modern
```

**为什么这很重要？**

- **可嵌入性**：外部 Agent（hermes-agent、openclaw、自定义 Slack/Discord bot）可以通过 CLI 驱动 Open Design
- **自动化友好**：支持 `--json` 输出和 `--prompt-file` 输入，可以无缝集成到 shell 管道
- **测试覆盖**：CLI 和 UI 调用相同的 `/api/*` 端点，确保测试覆盖真实的用户路径

这种设计让 Open Design 不仅是一个 GUI 工具，更是一个可编程的设计平台。

### 5. 三种部署拓扑

**灵活的部署选择**

Open Design 支持三种部署模式：

**拓扑 A — 完全本地（默认）**
```
用户浏览器 → Next.js (localhost:3000) → Express daemon (localhost:7456)
                                        ↓
                                   Agent 进程池
```

**拓扑 B — Web 在 Vercel + daemon 在本地**
```
用户浏览器 → Vercel (Next.js) → 本地 daemon (通过 ngrok/Cloudflare Tunnel)
```

**拓扑 C — 完全云端（无 daemon）**
```
用户浏览器 → Vercel (Next.js) → 直接调用 Claude API
```

这种灵活性让用户可以根据隐私需求、性能要求和成本考虑选择最合适的部署方式。

### 6. 流式交互与工具调用

**实时的 Agent 交互**

Open Design 实现了复杂的流式协议来支持 Agent 的交互式工具调用：

```typescript
// Claude 使用 stream-json 格式
promptInputFormat: 'stream-json'

// 支持 AskUserQuestion 等交互工具
run.pendingHostAnswers.add(toolUseId)
// stdin 保持打开直到所有工具调用完成
```

**关键创新**

- `promptInputFormat: 'stream-json'` 让 daemon 可以在 Agent 运行时注入新消息
- `POST /api/runs/:id/tool-result` 端点用于回传工具结果
- `turn_end` 事件只在所有待处理工具调用完成后才关闭 stdin
- 支持 `AskUserQuestion` 的多选、单选、预览等复杂交互

这让 Open Design 的 Agent 可以像真实的协作伙伴一样与用户对话，而不是简单的单向生成。

### 7. 严格的质量保障体系

**多层验证策略**

Open Design 建立了完善的质量保障流程：

**代码守卫**
```bash
pnpm guard  # 检查禁止的 .js 文件、边界违规
pnpm typecheck  # 全工作区类型检查
```

**PR 审查流程**
- 使用 `tools/pr` 工具自动分类 PR 到不同审查通道
- 每个通道有专门的检查清单
- 阻塞性评论仅限于正确性、安全、数据完整性问题

**测试策略**
- 技能测试：使用轻量模型（Haiku 4.5）运行技能，断言 manifest 和正则
- 合约测试：生产者和消费者都必须有类型/测试覆盖
- 集成测试：数据库测试必须使用真实数据库，不使用 mock

### 8. 卓越的开发者体验

**统一的工具链**

```bash
pnpm tools-dev      # 本地开发生命周期控制
pnpm tools-pack     # 打包构建控制
pnpm tools-pr       # PR 审查工作流
pnpm tools-serve    # 本地 fixture 服务
```

**清晰的文档结构**

- `AGENTS.md` - Agent 行为规范（根目录 + 各子目录）
- `CONTRIBUTING.md` - 贡献者指南
- `docs/code-review-guidelines.md` - 代码审查标准
- `docs/skills-protocol.md` - 技能协议规范

**快速反馈循环**

- 本地开发使用 `tools-dev` 统一管理端口、命名空间、日志
- 桌面应用通过 sidecar IPC 自动发现 web URL
- E2E 测试使用独立命名空间，不干扰开发环境

## 技术栈

**前端**
- Next.js 16 (App Router)
- React 18
- TypeScript
- Tailwind CSS

**后端**
- Express.js (daemon)
- SQLite (better-sqlite3)
- Node.js 24

**桌面**
- Electron
- Sidecar IPC

**工具链**
- pnpm (workspace)
- Playwright (E2E)
- Vitest (单元测试)

## 创新的设计决策

### 1. 不可变性优先

```typescript
// 错误：就地修改
modify(original, field, value)

// 正确：返回新副本
update(original, field, value)
```

所有数据操作都创建新对象，避免隐藏的副作用。

### 2. 多小文件 > 少大文件

- 典型文件 200-400 行，最多 800 行
- 按功能/领域组织，而非按类型
- 高内聚，低耦合

### 3. 边界强制

- `apps/web` 不能导入 `apps/daemon/src`
- 共享契约必须在 `packages/contracts`
- `packages/contracts` 保持纯 TypeScript（无 Node/浏览器 API）

### 4. TypeScript 优先

- 新代码默认使用 TypeScript
- JavaScript 仅限于生成输出、供应商依赖、兼容性构建
- `pnpm guard` 强制执行这一规则

## 国际化支持

Open Design 支持 18 种语言：

- 英语 (en)
- 简体中文 (zh-CN)
- 繁体中文 (zh-TW)
- 日语 (ja)
- 韩语 (ko)
- 阿拉伯语 (ar)
- 德语 (de)
- 西班牙语 (es-ES)
- 法语 (fr)
- 波斯语 (fa)
- 匈牙利语 (hu)
- 印尼语 (id)
- 波兰语 (pl)
- 葡萄牙语 (pt-BR)
- 俄语 (ru)
- 泰语 (th)
- 土耳其语 (tr)
- 乌克兰语 (uk)

所有 i18n 键都有类型检查，缺失翻译会产生编译错误。

## 总结

Open Design 的亮点不仅在于它的功能，更在于它的架构设计：

1. **可扩展性** - Agent 适配器、Skills 协议、设计系统分层
2. **可组合性** - CLI + UI 双轨、命名空间隔离、进程边界清晰
3. **可维护性** - 严格的边界、类型安全、自动化验证
4. **开发者友好** - 统一工具链、清晰文档、快速反馈循环

这些设计决策让 Open Design 不仅是一个产品，更是一个可以长期演进的平台。它展示了如何在快速迭代的 AI 工具领域建立稳定的技术基础。

## 最新动态（截至 2026-06-28）

> [!note] 爆发增长：57.4K stars，Claude Design 开源替代的事实标杆
> Open Design 2026-04 发布后，v0.9.0（2026-06-02）已是第 10 个 release，累计 1,837 commits / 310 contributors。它定义了"Claude Design 开源替代"这个品类。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| 版本 | 早期 | **v0.9.0**（2026-06-02，第 10 个 release）|
| Star | 增长中 | **57.4K** |
| 贡献者 | 少量 | **310 contributors** |
| 定位 | 开源设计工具 | **"local-first, open-source Claude Design alternative"** |

### 品类确立
- **DESIGN.md 范式爆发**：与 [[awesome-design-md]]（93K stars）共同推动 DESIGN.md 成为 AI 设计的标准文件
- **竞品涌现**：Open CoDesign（open-codesign）、Open Pencil（Figma 开源替代）等 adjacent 项目出现，说明"AI-native 开源设计工具"品类成立
- **多 AI CLI 兼容**：Claude Code / Codex CLI / ChatGPT 均可驱动，BYOK 模式

### 战略意义
Open Design 把"设计系统 → DESIGN.md → AI 生成 UI"的闭环做成了本地优先的桌面应用。这与 [[claude-code-game-studios]]（agent 塑造行为）、[[superpowers]]（技能注入）形成对照——Open Design 选的是"设计资产可移植"路线。

### 仍待观察
- 与 Anthropic 官方 Claude Design 的功能差距
- 310 contributors 的协作治理成熟度

## 相关页面

- [[open-design-architecture]] - 架构与 Agent 运行机制深度解析
- [[opensource-practices-from-open-design]] - 开源实践方法论
