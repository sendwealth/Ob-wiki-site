---
title: ECC (Everything Claude Code)
created: 2026-05-29
updated: 2026-05-29
type: entity
tags: [product, ai, developer-tools, active, mcp]
sources:
  - https://github.com/affaan-m/ECC
  - https://ecc.tools
confidence: high
---

# ECC (Everything Claude Code)

> 197K⭐ 跨 harness 的 AI 代理性能优化系统。提供 63 agents、249 skills、79 commands、12 语言生态，覆盖 Claude Code / Codex / Cursor / OpenCode / Gemini / Zed / GitHub Copilot 等多种 AI 编程工具。MIT 协议，2026-01 创建，核心贡献者 affaan-m（1423 commits）。

---

## 概览

ECC 全称 **Everything Claude Code**，定位为 "harness-native operator system for agentic work"。它不是简单的配置文件集合，而是一套完整的开发操作系统：技能（skills）、本能（instincts）、记忆优化、持续学习、安全扫描、研究优先开发。

核心理念：将 10+ 个月日常高强度使用中积累的工程工作流，提炼成可复用的 agents / skills / hooks / rules / MCP 配置。

## 规模与指标

| 指标 | 数值 |
|------|------|
| GitHub Stars | ~197K |
| Forks | ~30K |
| Contributors | 170+ |
| Agents | 63 |
| Skills | 249 |
| Legacy Commands | 79 |
| 支持语言生态 | 12+ (TS/Python/Go/Java/Rust/C++/Kotlin/Swift/Perl/PHP/React/...) |
| 最新版本 | v2.0.0-rc.1 (2026-05-25) |
| 许可证 | MIT |

## 架构

```
ECC/
├── agents/          # 63 个专用子代理（planner, code-reviewer, tdd-guide 等）
├── skills/          # 249 个工作流定义与领域知识
├── commands/        # 79 个斜杠命令（/tdd, /plan, /e2e, /code-review 等）
├── hooks/           # 触发式自动化（session 持久化、pre/post-tool hooks）
├── rules/           # 始终遵循的准则（安全、编码风格、测试要求）
│   ├── common/      # 语言无关通用规则
│   ├── zh/          # 中文翻译版本
│   ├── typescript/  # TS 特定规则
│   ├── python/      # Python 特定规则
│   └── ...          # Go, Java, Rust, C++, Kotlin, Swift, PHP, Perl
├── mcp-configs/     # MCP 服务器配置
├── scripts/         # 跨平台 Node.js 工具（hooks, 安装器）
├── tests/           # 测试套件（978+ 内部测试）
├── ecc2/            # Rust 控制平面原型（v2.0 alpha）
└── docs/            # 文档、发布说明、架构设计
```

## 核心组件

### Agents（代理）
专用子代理，可被主会话委派执行特定任务。包括：
- **planner** — 实现规划
- **code-reviewer** — 代码审查
- **tdd-guide** — 测试驱动开发
- **security-reviewer** — 安全分析
- **build-error-resolver** — 构建错误修复
- **architect** — 系统设计
- 语言特定审查器：typescript-reviewer, python-reviewer, go-reviewer, rust-reviewer, java-reviewer, kotlin-reviewer, cpp-reviewer, flutter-reviewer

### Skills（技能）
工作流定义与领域知识。覆盖：
- 开发流程：tdd-workflow, code-review, security-review
- 语言模式：python-patterns, golang-patterns, rust-patterns, cpp-coding-standards
- API 设计：api-design, mcp-server-patterns, claude-api
- 部署：deployment-patterns, docker-patterns, database-migrations
- 研究：deep-research, exa-search, search-first

### Rules（规则）
始终遵循的开发准则，按语言分层：
- **common/** — 通用原则（编码风格、测试、安全、Git 工作流）
- **语言目录** — 扩展通用规则，加入特定语言习惯

### Hooks（钩子）
- PreToolUse / PostToolUse / Stop 三种触发类型
- 自动格式化、安全检查、会话持久化
- 通过 `run-with-flags.js` 统一封装，支持运行时门控

## 版本演进

| 版本 | 日期 | 亮点 |
|------|------|------|
| v1.2.0 | 2026-02 | Python/Django、Java Spring Boot 支持；持续学习 v2 |
| v1.4.0 | 2026-02 | 多语言规则架构；安装向导；PM2 多代理编排；中文翻译 |
| v1.6.0 | 2026-02 | Codex CLI 支持；AgentShield；GitHub Marketplace |
| v1.8.0 | 2026-03 | Harness 性能系统 |
| v1.9.0 | 2026-03 | 选择性安装；12 语言生态；ECC Tools Pro |
| v2.0.0-rc.1 | 2026-05 | Dashboard GUI；Rust 控制平面；Hermes operator；Itō 预测市场技能包 |

## 安装方式

```bash
# 方式 1：Claude Code 插件（推荐）
# 在 Claude Code 中运行 /plugin install ecc

# 方式 2：npx 安装器
npx ecc install --profile full --target claude

# 方式 3：手动安装
git clone https://github.com/affaan-m/ECC.git
./install.sh typescript python

# 组件咨询
npx ecc consult "security reviews" --target claude
```

⚠️ 不要叠加多种安装方式，否则会导致文件重复。

## 跨 Harness 支持

ECC 不仅限于 Claude Code，还支持：
- **OpenAI Codex** — 通过 `codex.md` 兼容
- **Cursor** — 规则和技能可适配
- **OpenCode** — 插件系统支持
- **Gemini CLI** — 自动映射
- **Zed** — IDE 集成
- **GitHub Copilot** — 通过 GitHub App

## 与竞品的关系

- [[gstack]] — Garry Tan 的 AI 软件工厂，18 人虚拟工程团队，ECC 的部分技能受其启发
- [[ruflo]] — 48.9K⭐ 多 Agent 编排平台，100+ Agent + 300+ MCP 工具，更偏向基础设施层
- [[kagent]] — Kubernetes 原生 AI Agent 框架，使用 CRD 管理 Agent，与 ECC 的技能体系互补
- [[swarmclaw]] — 开源自托管 Agent 运行时，23+ LLM 支持，与 ECC 的跨 harness 策略类似

## 技术栈

| 层 | 技术 |
|----|------|
| 运行时 | Node.js >=18 (CommonJS) |
| 测试 | `node tests/run-all.js`, c8 覆盖率 |
| Lint | ESLint (flat config), markdownlint-cli |
| 脚本 | Shell + Node.js (跨平台) |
| v2 控制平面 | Rust (ecc2/) |
| Dashboard | Python Tkinter |
| 包管理 | npm (ecc-universal, ecc-agentshield) |
| CI | GitHub Actions |

## 关键观察

1. **规模惊人** — 197K stars 在 AI 开发工具领域属于顶级，社区活跃度高
2. **跨 harness 策略** — 不绑定单一 AI 工具，而是构建通用的代理工作流层
3. **分层架构** — agents → skills → hooks → rules 从具体到抽象，可按需安装
4. **v2 转型** — Rust 控制平面 + Dashboard GUI，从纯配置集向独立产品演进
5. **商业化路径** — ECC Tools Pro / Enterprise tiers，GitHub Marketplace 150+ 安装
6. **本地项目关系** — 当前项目 `everything-claude-code` 正是 ECC 仓库本身

---

**相关页面**: [[gstack]] | [[ruflo]] | [[kagent]] | [[swarmclaw]] | [[codegraph]]
