---
title: Archon
created: 2026-06-01
updated: 2026-06-01
type: entity
tags: [ai, agent, workflow, open-source, platform, bun, typescript]
sources:
  - https://github.com/coleam00/Archon
  - https://archon.diy
confidence: high
---

# Archon

> 开源 AI 编码确定性编排平台：将 AI 编码助手（Claude Code SDK、Codex SDK）通过 YAML 工作流定义为可重复、可隔离、可组合的确定性流水线，从 Slack/Telegram/GitHub/Web/CLI 多平台远程驱动。

---

## 一句话定位

"The first open-source harness builder for AI coding." 解决的核心问题：AI 编码助手每次运行行为不确定（跳过规划、忘记测试、PR 描述不符合模板）。Archon 把开发流程编码为工作流，AI 填充智能，结构由用户掌控。

## 基本信息

| 属性 | 值 |
|------|-----|
| **版本** | 0.4.1 |
| **协议** | MIT |
| **语言** | TypeScript（~157K 行） |
| **运行时** | Bun |
| **数据库** | SQLite（默认）/ PostgreSQL（可选） |
| **前端** | React + Vite + Tailwind v4 + shadcn/ui |
| **API 框架** | Hono（OpenAPI + Zod 自动生成规范） |
| **主要贡献者** | Cole Medin（创始人）、Rasmus Widing（1013 commits） |
| **社区规模** | 10+ 核心贡献者，GitHub Trending 项目 |

## 核心架构

### 包依赖图（Monorepo，11 个包）

```
@archon/paths (零内部依赖)
    ↑
@archon/git → @archon/paths
    ↑
@archon/isolation → @archon/git + @archon/paths
    ↑
@archon/providers/types (零 SDK 依赖的契约层)
    ↑
@archon/workflows → @archon/git + @archon/paths + @archon/providers/types
    ↑
@archon/core → @archon/providers (运行时)
    ↑
@archon/adapters → @archon/core
    ↑
@archon/server → @archon/adapters
@archon/cli → @archon/server + @archon/adapters
@archon/web (独立前端，通过 OpenAPI spec 生成类型)
```

### 关键接口（ISP — 接口隔离原则）

| 接口 | 职责 | 位置 |
|------|------|------|
| `IAgentProvider` | AI 代理统一抽象：`sendQuery()` 流式返回 | `@archon/providers/types` |
| `IPlatformAdapter` | 平台适配器：`onMessage()` + `sendMessage()` | `@archon/core/types` |
| `IWorkflowStore` | 工作流数据库操作（运行生命周期、节点输出、会话持久化） | `@archon/workflows/store` |
| `IIsolationStore` | 隔离环境存储 | `@archon/isolation` |

### 数据流（用户消息 → AI 响应）

```
用户消息 (Slack/Telegram/GitHub/Web/CLI)
  → IPlatformAdapter.onMessage()
  → CommandHandler (斜杠命令，确定性)
  → Orchestrator (AI 会话管理)
    → IAgentProvider.sendQuery() (流式)
    → Git Worktree 隔离
  ← SSE / 批量消息回传平台
```

### 工作流引擎

工作流是 Archon 的核心差异化能力：

- **DAG 格式**：节点声明 `depends_on`，独立节点并行执行
- **6 种节点类型**：`command`（命名命令）、`prompt`（AI 提示）、`bash`（Shell 脚本）、`loop`（迭代 AI）、`approval`（人工审批门）、`script`（TypeScript/Python 内联脚本）
- **变量替换**：`$nodeId.output`、`$ARGUMENTS`、`$ARTIFACTS_DIR`、`$WORKFLOW_ID`、`$LOOP_PREV_OUTPUT` 等
- **Provider 无关**：Claude、Codex、Pi（社区）可互换，YAML 只声明 `provider:` 字段
- **Resume 能力**：失败工作流可从断点恢复（跳过已完成节点）
- **持久化会话**：`persist_session` 跨运行保留 AI 上下文

### 数据库（11 张表，`remote_agent_` 前缀）

```
codebases → codebase_env_vars (1:N)
conversations → messages (1:N)
conversations → sessions (1:N)
codebases → isolation_environments (1:N)
workflow_runs → workflow_events (1:N)
users → user_identities (1:N, 平台映射)
workflow_node_sessions (节点级 AI 会话持久化)
```

## 技术亮点

### 1. Git Worktree 原生隔离

每次工作流运行自动创建独立 Git Worktree，实现：
- 5 个修复并行无冲突
- 自动端口分配（3190-4089，基于路径哈希）
- 完成后分支合并 + Worktree 清理

### 2. 确定性 × AI 的边界

| 确定性部分（用户控制） | AI 部分（模型填充） |
|------------------------|---------------------|
| 工作流阶段顺序 | 每步的具体代码实现 |
| 验证门禁（测试必须通过） | PR 描述撰写 |
| Bash/Script 节点 | 规划和代码审查 |
| Git 操作（分支、合并） | 代码生成 |

### 3. 多 Provider 能力矩阵

| 能力 | Claude | Codex | Pi (社区) |
|------|--------|-------|-----------|
| 会话恢复 | ✅ | — | — |
| MCP 工具 | ✅ | — | ✅ |
| Skills 预加载 | ✅ | — | — |
| 工具限制 | ✅ | — | — |
| 结构化输出 | ✅ | ✅ | 最佳努力 |
| 沙箱 | ✅ | — | — |

### 4. 平台适配器模式

5 个平台共享 `IPlatformAdapter` 接口：
- **Web**：SSE 流式
- **Slack**：SDK 轮询（thread_ts）
- **Telegram**：Bot API 轮询（chat_id）
- **GitHub**：Webhooks + CLI（owner/repo#number）
- **Discord**（社区）：WebSocket（channel ID）

认证检查封装在适配器内部（白名单机制），未授权用户静默拒绝。

## 设计哲学

- **KISS**：直接控制流优于元编程，显式分支优于隐式动态行为
- **YAGNI**：不为假设用例添加配置/接口/功能标志
- **Fail Fast**：不安全状态立即抛出清晰错误，不做静默降级
- **不可变数据**：Session 是不可变的，转换创建新的链接记录
- **不跨进程自治变更**：无法区分"正在运行"和"崩溃遗留"时，不自动标记失败

## 与相关项目的关系

- `[[claude-code-workflow]]` — Archon 的工作流引擎实现了类似的确定性编排理念，但以 Bun/TypeScript 实现并通过 YAML 定义
- `[[temporal]]` — Temporal 提供持久化执行平台，Archon 的 DAG 执行器理念类似但更轻量（单进程，SQLite/Postgres）
- `[[codegraph]]` — Archon 项目使用 CodeGraph MCP Server 进行代码导航
- `[[slack]]` — Slack 是 Archon 支持的核心平台之一
- `[[kagent]]` — Kagent 是 K8s 原生 AI Agent 框架，Archon 则是轻量级单开发者工具

## 开发工作流

```bash
bun run dev          # 启动 server + web（热重载）
bun run test         # 按包隔离测试（避免 mock.module 污染）
bun run validate     # PR 前完整校验（7 项检查）
bun run cli workflow run plan "Add dark mode"  # CLI 运行工作流
```

关键约定：
- 不从 repo 根运行 `bun test`（~135 个 mock 污染失败）
- Zod schema 从 `@hono/zod-openapi` 导入 `z`
- 所有 API 路由使用 `registerOpenApiRoute()` 包装
- ESLint 零容忍策略（`--max-warnings 0`）

## 版本历史要点

| 版本 | 日期 | 重点 |
|------|------|------|
| 0.4.0 | 2026-05-28 | 社区 Provider（Pi）、DAG Builder Web UI、全局工作流/命令、Script 节点、per-node 会话持久化 |
| 0.4.1 | 2026-05-28 | Bug 修复（流式连续性、DAG Builder 渲染、Webhook 克隆路径） |
