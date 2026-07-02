---
title: Agno 文档管理体系
created: 2026-05-28
updated: 2026-05-28
type: concept
tags: [ai, documentation, knowledge-management, open-source, agent]
sources:
  - https://github.com/agno-agi/agno
  - ~/Projects/agno source code analysis
confidence: high
---

# Agno 文档管理体系

> Agno 的文档系统是一个**五层架构**：外部文档站（docs.agno.com，私有）、README 面板、Cookbook 可运行示例系统（20+ 主题目录 + 强制风格指南 + 自动化检查脚本）、AI Agent 指令层（CLAUDE.md / AGENTS.md / .cursorrules 三件套）、CI/CD 强制门禁（PR 标题 lint + Claude Opus 自动 Review）。其中 Cookbook 系统是核心亮点 — 可运行、可测试、可审计。

---

## 文档架构总览

```
┌─────────────────────────────────────────────────────────────┐
│  第 1 层：外部文档站（私有，不在仓库内）                        │
│  docs.agno.com  →  symlinked to ~/code/docs                 │
│  MCP Server: docs.agno.com/mcp                              │
│  llms-full.txt 索引（供 Cursor/VSCode/Windsurf 等编码工具）    │
├─────────────────────────────────────────────────────────────┤
│  第 2 层：README.md — 公众入口                               │
│  Introduction → Features → Get started → Community          │
├─────────────────────────────────────────────────────────────┤
│  第 3 层：Cookbook 系统 — 可运行示例（核心亮点）               │
│  20+ 主题目录 | STYLE_GUIDE.md | 自动化检查脚本               │
│  README.md + TEST_LOG.md + TEST_PROMPT.md（每目录标配）       │
├─────────────────────────────────────────────────────────────┤
│  第 4 层：AI Agent 指令层                                    │
│  CLAUDE.md (Claude Code) | AGENTS.md (通用) | .cursorrules  │
├─────────────────────────────────────────────────────────────┤
│  第 5 层：CI/CD 强制门禁                                     │
│  PR Lint | Claude Opus Auto-Review | Issue Templates        │
│  PR Template Checklist | Stale Issues Bot                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 第 1 层：外部文档站

文档站为**私有**，通过 symlink 引入（`docs/ → ~/code/docs`），不在仓库中。

对外提供的接入方式：

| 接入方式 | 用途 |
|---------|------|
| `docs.agno.com` | 人类可读文档 |
| `docs.agno.com/llms-full.txt` | 编码工具索引源（Cursor、VSCode、Windsurf） |
| `docs.agno.com/mcp` | MCP Server 供 AI Agent 实时查询 |

同样，`specs/`（设计文档）也通过 symlink 引入（`specs/ → ~/code/specs`），实现设计文档与代码分离。

## 第 2 层：README.md

标准开源项目 README 结构：

- **Introduction** — 一句话定位 + 核心价值
- **What you can build** — 使用场景展示
- **Features** — 10 大特性列表（生产 API、存储、集成、上下文、审批、可观测、安全、接口、调度、部署）
- **Get started** — 快速安装 + 第一个 Agent 示例
- **Community** — 社区链接
- **Telemetry** — 遥测说明（`AGNO_TELEMETRY=false` 可关闭）

## 第 3 层：Cookbook 系统（核心亮点）

### 目录组织

Cookbook 是 Agno 文档体系的核心，按**主题/能力**组织，编号目录 + 专题目录并存：

```
cookbook/
├── 00_quickstart/        # 快速开始
├── 01_demo/              # 完整演示
├── 02_agents/            # 单 Agent 模式
├── 03_teams/             # 多 Agent Team
├── 04_workflows/         # Workflow 编排
├── 05_agent_os/          # 生产运行时（Agno OS）
├── 06_storage/           # 存储层
├── 07_knowledge/         # 知识库 / RAG
├── 08_learning/          # 学习系统（Golden Standard ⭐）
├── 09_evals/             # 评估框架
├── 10_reasoning/         # 推理能力
├── 11_memory/            # 记忆管理
├── 12_context/           # 上下文管理
├── 90_models/            # 40+ 模型供应商示例
├── 91_tools/             # 100+ 工具集成
├── 92_integrations/      # 第三方集成
├── 93_components/        # 组件配置
├── 99_docs/              # 文档相关
├── data_labeling/        # 数据标注专题
├── frameworks/           # 框架集成专题
├── gemini_3/             # Gemini 3 专题
├── levels_of_agentic_software/  # Agentic 层级专题
├── scripts/              # Cookbook 工具脚本
├── README.md             # Cookbook 总索引
└── STYLE_GUIDE.md        # Python 风格指南（强制）
```

### 每目录标配文件（Quality Standard）

每个 Cookbook 目录必须包含：

| 文件 | 作用 |
|------|------|
| `README.md` | 意图说明 + 前置条件 + 运行命令 |
| `TEST_LOG.md` | 运行状态记录（PASS/FAIL + 观察） |
| `TEST_PROMPT.md` | Agent 驱动测试的提示词 |
| `*.py` | 可运行的 Python 示例 |

### Cookbook Python 风格指南（STYLE_GUIDE.md）

强制执行的代码结构：

```python
"""
<Title>
<What this demonstrates>
"""

# ---------------------------------------------------------------------------
# <Config / Setup>
# ---------------------------------------------------------------------------

# ---------------------------------------------------------------------------
# Agent Instructions
# ---------------------------------------------------------------------------
instructions = """..."""

# ---------------------------------------------------------------------------
# Create the Agent
# ---------------------------------------------------------------------------
example_agent = Agent(...)

# ---------------------------------------------------------------------------
# Run the Agent
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    example_agent.print_response("...", stream=True)
```

核心规则：
1. 模块 docstring 置顶（说明 + 关键概念 + 建议输入）
2. Banner comment 分区：Config → Instructions → Create → Run
3. `if __name__ == "__main__":` 执行门
4. **禁止 emoji**（所有 cookbook Python 文件）
5. Imports 在 docstring 和第一个 banner 之间

### 自动化检查脚本

| 脚本 | 作用 |
|------|------|
| `check_cookbook_pattern.py --base-dir <dir>` | 检查 Python 文件结构合规 |
| `audit_cookbook_metadata.py --scope direct --fail-on-missing` | 审计 README/TEST_LOG 是否齐全 |
| `cookbook_runner.py <dir> --batch` | 批量运行 cookbook |
| `cookbook_runner.py <dir> --batch --json-report` | 生成机器可读报告 |

### Golden Standard：`08_learning/`

被项目指定为"黄金标准" cookbook，内含 10 个子目录：

```
08_learning/
├── 00_quickstart/
├── 01_basics/
├── 02_user_profile/
├── 03_session_context/
├── 04_entity_memory/
├── 05_learned_knowledge/
├── 06_quick_tests/
├── 07_patterns/
├── 08_custom_stores/
├── 09_decision_logs/
├── README.md          # 详细概念说明 + Quick Start
├── TEST_LOG.md        # 按优先级分组的测试结果
├── TEST_PROMPT.md     # 完整的 agent 测试指令
└── requirements.txt   # 独立依赖
```

TEST_PROMPT.md 是一份精心设计的**Agent 驱动测试指令**：
- 先读取所有 .py 文件理解内容
- 为每个子目录启动并行 agent
- 每个 agent 运行检查脚本 → 运行 Python → 验证风格合规 → 更新 TEST_LOG
- 最终合并结果

## 第 4 层：AI Agent 指令层

三份互补的 AI 指令文档：

| 文件 | 目标 Agent | 内容侧重点 |
|------|-----------|-----------|
| `CLAUDE.md` | Claude Code | 完整项目指南（结构、环境、测试、代码规范、PR 格式、CI Review） |
| `AGENTS.md` | 通用 AI Agent | 同 CLAUDE.md 的简化版（结构、环境、Cookbook 测试） |
| `.cursorrules` | Cursor | 编码模式速查（Agent/Team/Workflow 模式 + 常见错误 + 生产建议） |

### CLAUDE.md / AGENTS.md 关键内容

- **Repository Structure** — 代码位置速查表
- **Virtual Environments** — `.venv/`（开发）+ `.venvs/demo/`（Cookbook）
- **Testing Cookbooks** — 完整测试工作流（环境 → 运行 → 更新 TEST_LOG）
- **Coding Patterns** — 核心编码约定（见下）
- **PR Format** — 标题格式 + 描述模板 + 提交前检查
- **Don't** — 禁止事项清单

### .cursorrules 关键编码规则

```
Core Rules:
- NEVER create agents in loops（性能杀手）
- Always use output_schema（结构化输出）
- PostgreSQL in production, SQLite for dev only
- Start with single agent, scale up only when needed

禁止项:
- f-strings for print lines（无变量时）
- emoji in examples
- 跳过 async variants
- 不运行 format.sh + validate.sh 就 push
- 使用 OpenAIChat（用 OpenAIResponses 替代）
- 使用 gpt-4o（用 gpt-5.4 替代）
```

## 第 5 层：CI/CD 强制门禁

### PR 标题 Lint（`pr-lint.yml`）

自动检查 PR 标题格式，三种合法格式：

```
[type] description        # 如 [feat] Add user authentication
type: description         # 如 fix: validation
type-kebab-case           # 如 feat-workflow-serialization
```

合法类型：`feat`, `fix`, `cookbook`, `test`, `refactor`, `chore`, `style`, `revert`, `release`

### Claude Opus 自动 Review（`claude.yml`）

每个非 draft PR 自动触发：

| 配置 | 值 |
|------|-----|
| 触发 | `@claude` 关键词（评论/Review/Issue） |
| 模型 | `claude-opus-4-6` |
| 插件 | `code-review` + `pr-review-toolkit`（10 个专用 Agent） |
| 超时 | 15 分钟 |
| 输出 | Sticky comment |
| 模式 | Review 模式（含 `review` 关键词）或 Assistant 模式 |

### PR 模板 Checklist

```
必填项:
- [ ] 代码符合风格指南
- [ ] 运行 format.sh + validate.sh
- [ ] 自审完成
- [ ] 文档更新（注释、docstring）
- [ ] Cookbook 示例更新
- [ ] 干净环境测试
- [ ] 测试添加/更新

AI 生成声明:
- [ ] 确认是否完全 AI 生成
- [ ] 确认无重复 PR
```

### 其他 CI 工作流

| 工作流 | 作用 |
|--------|------|
| `test.yml` | PR 测试 |
| `test_on_release.yml` | Release 测试 |
| `release.yml` | 发布流程 |
| `performance.yml` | 性能测试 |
| `pr-triage.yml` | PR 自动分类 |
| `stale-issues.yml` | 过期 Issue 清理 |

### Issue 模板

| 模板 | 格式 |
|------|------|
| `bug-report.yml` | Bug 报告（结构化表单） |
| `feature-request.yml` | 功能请求（结构化表单） |
| `config.yml` | 模板配置 |

---

## 设计特点分析

### 亮点

1. **Cookbook 即文档** — 可运行、可测试、可审计，远超静态文档
2. **Agent 驱动测试** — TEST_PROMPT.md 让 AI Agent 自动执行 cookbook 测试
3. **多层 Agent 指令** — CLAUDE.md / AGENTS.md / .cursorrules 覆盖不同编码 Agent
4. **CI 自动 Review** — Claude Opus + 10 个专用 Review Agent，零人工触发
5. **风格自动化** — check_cookbook_pattern.py + audit_cookbook_metadata.py 机器强制
6. **外部文档 MCP** — docs.agno.com/mcp 让 Agent 实时查询最新文档
7. **私有/公开分离** — specs/ 和 docs/ symlink 外置，敏感设计文档不出仓库

### 不足

1. **外部文档不可审计** — docs/ 和 specs/ 为 symlink 私有目录，社区无法看到设计决策过程
2. **Cookbook 覆盖不均** — 编号目录（00-12, 90-99）规范，但专题目录（data_labeling, frameworks）无统一标准
3. **三份 Agent 指令有重叠** — CLAUDE.md 和 AGENTS.md 内容高度相似，维护成本高
4. **无 CHANGELOG.md** — 版本变更历史依赖 git log 和 GitHub Releases
5. **贡献者文档偏薄** — CONTRIBUTING.md 主要是 fork-PR 流程，缺少架构导览和贡献场景指南

---

**相关概念**: [[superpowers]] | [[codegraph]] | [[context-mode]] | [[agentic-rag]]

**相关实体**: [[agno]] | [[zed-documentation-system]] | [[orloj-documentation-system]] | [[openshell-documentation-system]]
