---
title: Superpowers — AI 编码 Agent 的行为塑造技能系统
created: 2026-05-18
updated: 2026-06-28
type: entity
tags: [agent, skills, tdd, debugging, collaboration, open-source, ai-tooling, claude-code]
sources: [README.md, CLAUDE.md, skills/*]
confidence: high
---

# Superpowers

> 一套零依赖的 Agent 技能插件，通过 SessionStart Hook 自动注入，让 AI 编码 Agent 遵循 TDD、系统化调试、协作式设计等工程最佳实践——不是建议，是强制流程

*项目路径: ~/Projects/superpowers | 版本: v5.1.0 | 许可: MIT | 作者: Jesse Vincent | GitHub: obra/superpowers*

## 核心问题

AI 编码 Agent（Claude Code、Copilot CLI、Gemini CLI 等）能力强大但行为不可控：

| 问题 | 表现 |
|------|------|
| 跳过设计直接写码 | 没理解需求就开始实现，返工率高 |
| 不写测试 | 先写实现再补测试（或根本不写） |
| 调试靠猜 | 改改试试，改改试试，无系统方法 |
| 不做 Code Review | 代码写完就提交，质量无保障 |
| 忽视已有方案 | 不搜索就从头实现，重复造轮子 |

**Superpowers 的解法**：通过技能系统在 Agent 执行前注入行为约束，把工程流程变成不可跳过的强制检查点。

## 工作原理

### 架构：Hook → 注入 → 技能触发

```
SessionStart Hook (hooks/session-start)
    ↓ 读取 using-superpowers/SKILL.md
    ↓ 注入到 Agent 上下文
    ↓
Agent 收到用户消息
    ↓ 检查是否有相关技能（哪怕 1% 可能性）
    ↓ 调用 Skill tool 加载技能内容
    ↓ 严格按技能流程执行
```

关键机制：

1. **SessionStart Hook**：在 `startup|clear|compact` 事件时触发，把 `using-superpowers` 技能注入 Agent 上下文
2. **技能发现**：`using-superpowers` 技能列出所有可用技能及其触发条件
3. **前置检查**：Agent 在任何响应前必须先检查是否有技能适用
4. **强制执行**：技能定义的是工作流，不是建议

### 技能加载格式

每个技能是一个 `SKILL.md` 文件，包含 frontmatter 元数据和内容：

```yaml
---
name: brainstorming
description: "You MUST use this before any creative work..."
---

（技能内容：流程、检查清单、行为约束）
```

## 核心技能体系

### 基本工作流（完整开发周期）

```
brainstorming → using-git-worktrees → writing-plans
    → subagent-driven-development / executing-plans
    → test-driven-development → requesting-code-review
    → finishing-a-development-branch
```

| 阶段 | 技能 | 作用 |
|------|------|------|
| 设计 | **brainstorming** | 苏格拉底式提问，理解需求，提出 2-3 方案，分段呈现设计 |
| 隔离 | **using-git-worktrees** | 创建隔离工作区，新分支，验证测试基线 |
| 规划 | **writing-plans** | 拆成 2-5 分钟小任务，含文件路径、完整代码、验证步骤 |
| 实现 | **subagent-driven-development** | 每个任务派发独立子 Agent，双阶段审查（规格合规 + 代码质量） |
| 测试 | **test-driven-development** | RED-GREEN-REFACTOR 循环，先写失败测试，再写最小实现 |
| 审查 | **requesting-code-review** | 按严重级别报告问题，Critical 阻塞进度 |
| 收尾 | **finishing-a-development-branch** | 验证测试，决定 merge/PR/keep/discard |

### 调试技能

- **systematic-debugging**：4 阶段根因分析（观察 → 假设 → 实验 → 修复），而非盲目猜测
- **verification-before-completion**：确认 Bug 真的修好了

### 协作技能

- **receiving-code-review**：收到审查反馈后的处理流程，强调技术严谨性而非盲目同意
- **dispatching-parallel-agents**：并发派发独立子 Agent

### 元技能

- **writing-skills**：用 TDD 方法写新技能——先构造失败场景，写技能，验证通过
- **using-superpowers**：技能系统入口，教 Agent 如何发现和使用技能

## 设计哲学

Superpowers 有明确的工程哲学，不是通用建议：

1. **测试驱动开发** — 先写测试，永远是先写测试
2. **系统化胜过即兴** — 流程胜过猜测
3. **复杂性降低** — 简洁是首要目标
4. **证据胜过断言** — 验证后再宣布完成

### 关键设计决策

- **零依赖**：不依赖任何第三方包，纯 Markdown 技能文件 + Bash Hook
- **强制而非建议**：技能是"不可跳过的工作流"，不是"可选建议"
- **跨平台**：支持 Claude Code、Copilot CLI、Gemini CLI、Cursor、Codex、OpenCode
- **前置检查**："哪怕只有 1% 可能性，也必须先调用技能"

### 红旗机制

`using-superpowers` 技能包含一张红旗表，防止 Agent 自我合理化跳过技能：

| Agent 的想法 | 现实 |
|-------------|------|
| "这只是个简单问题" | 问题也是任务，要检查技能 |
| "先探索代码库再说" | 技能告诉你如何探索，先查技能 |
| "这不需要正式技能" | 如果技能存在，就用它 |
| "我记得这个技能" | 技能会更新，读当前版本 |

## 项目结构

```
superpowers/
├── skills/                         # 技能库（核心）
│   ├── using-superpowers/          # 入口技能 + 跨平台工具映射
│   │   ├── SKILL.md
│   │   └── references/             # Copilot/Codex/Gemini 工具映射
│   ├── brainstorming/              # 设计阶段
│   ├── writing-plans/              # 规划阶段
│   ├── executing-plans/            # 执行阶段
│   ├── test-driven-development/    # TDD（含反模式参考）
│   ├── systematic-debugging/       # 系统化调试（4 子文档）
│   ├── requesting-code-review/     # 代码审查
│   ├── receiving-code-review/      # 审查反馈处理
│   ├── using-git-worktrees/        # Git 工作树隔离
│   ├── finishing-a-development-branch/  # 分支收尾
│   ├── dispatching-parallel-agents/     # 并行 Agent 派发
│   ├── subagent-driven-development/     # 子 Agent 驱动开发
│   ├── verification-before-completion/  # 完成前验证
│   └── writing-skills/             # 元技能：如何写技能
├── hooks/                          # Hook 脚本
│   ├── hooks.json                  # Claude Code Hook 配置
│   ├── hooks-cursor.json           # Cursor Hook 配置
│   ├── session-start               # SessionStart 脚本
│   └── run-hook.cmd                # Hook 入口
├── .claude-plugin/                 # Claude Code 插件清单
├── .codex-plugin/                  # Codex 插件配置
├── .cursor-plugin/                 # Cursor 插件配置
├── gemini-extension.json           # Gemini CLI 扩展
├── .opencode/                      # OpenCode 配置
├── tests/                          # 测试
│   ├── skill-triggering/           # 技能触发测试
│   └── explicit-skill-requests/    # 显式技能请求测试
├── docs/                           # 设计文档和规格
├── scripts/                        # 辅助脚本
└── CLAUDE.md                       # 贡献者指南
```

## 技能的 TDD 开发方法

Superpowers 独创了"技能即代码"的开发方法——用 TDD 写技能文档：

1. **RED**：构造压力场景，用子 Agent 测试，观察失败行为（没有技能时的表现）
2. **GREEN**：编写技能文档，指导 Agent 正确行为
3. **REFACTOR**：寻找漏洞，关闭逃生路径

核心原则：**如果你没有看到 Agent 在没有技能时失败，你就不知道技能教的是否正确。**

## 对 AI 编码的意义

Superpowers 代表了一种新思路：**通过文档塑造 Agent 行为**。

传统方式是用代码约束 Agent（工具限制、系统提示），Superpowers 用精心设计的 Markdown 文档 + 自动注入机制，在不修改 Agent 本身的情况下，改变 Agent 的工作方式。

这解决了一个核心矛盾：Agent 能力越来越强，但工程纪律不会自动产生。Superpowers 把"写代码前先设计"、"先写测试再写实现"这些人类工程经验，变成了 Agent 的内置行为。

## 与相关项目的对比

| 项目 | 方向 | 机制 |
|------|------|------|
| **Superpowers** | 行为塑造 | Markdown 技能 + Hook 注入，跨平台 |
| **CLAUDE.md / GEMINI.md** | 项目指令 | 文件放在项目根目录，Agent 启动时读取 |
| **Cursor Rules** | 编辑器约束 | .cursorrules 文件 |
| **MCP Server** | 工具扩展 | 新增 Agent 可调用的工具 |
| **Agent Harness** | 运行时控制 | 框架级别的 Agent 编排 |

Superpowers 的独特定位：不增加工具能力，不限制工具范围，而是**改变 Agent 使用现有能力的方式**。

## 安装

```bash
# Claude Code（官方市场）
/plugin install superpowers@claude-plugins-official

# 或从 GitHub 安装
/plugin install github:obra/superpowers
```

其他平台（Copilot CLI、Gemini CLI、Cursor、Codex、OpenCode）各有对应安装方式。

## 最新动态（截至 2026-06-28）

> [!note] 2026 年主线：成为 Claude Code Skill 生态的标杆
> Superpowers 采用 marketplace 动态更新（非传统版本号），通过 `/plugin marketplace add obra/superpowers-marketplace` 安装、`/plugin update superpowers@superpowers-marketplace` 更新。2026 年它被多份评测列为"最完整的多 Agent 开发工作流 Skill"。

### 2026 生态信号

- **评测认可**：Firecrawl、Generative AI、DevelopersDigest 等 2026 年度 Claude Code Skill 盘点中，Superpowers 稳居编码向推荐榜首，被描述为"包含 20+ 子模块的工作流框架"（TDD / 系统化调试 / 计划编写 / 代码评审 / 并行 Agent 分发 / Git Worktree 管理等）
- **跨平台扩展**：继续维护对 Copilot CLI、Gemini CLI、Cursor、Codex、OpenCode 的适配，是少数真正跨 harness 的行为塑造框架
- **范式验证**：其"用 Markdown 文档塑造 Agent 行为 + Hook 自动注入"的范式被后续项目广泛借鉴（如 [[claude-code-game-studios]] 把它扩展成 49-agent 游戏工作室）

### 仍待观察

- 无语义化版本号（走 marketplace 滚动更新），难以追踪具体里程碑
- 重型技能集（20+ 子模块）对轻量场景仍是负担——这也是 [[claude-code-game-studios]] 类垂直特化项目出现的空间

## 关键文件速查

| 想了解... | 看这个文件 |
|-----------|-----------|
| 技能如何自动触发 | `hooks/session-start` |
| 技能发现机制 | `skills/using-superpowers/SKILL.md` |
| 设计阶段流程 | `skills/brainstorming/SKILL.md` |
| 调试方法论 | `skills/systematic-debugging/SKILL.md` |
| 如何写新技能 | `skills/writing-skills/SKILL.md` |
| 贡献指南 | `CLAUDE.md` |
| 测试如何验证技能 | `tests/skill-triggering/` |

---

*来源: 项目 README、CLAUDE.md、skills 目录，2026-05-18 分析*
