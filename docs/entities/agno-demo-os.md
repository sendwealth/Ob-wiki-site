---
title: AgentOS Demo (agno-demo-os)
created: 2026-05-28
updated: 2026-05-28
type: entity
tags: [project, ai, platform, saas]
sources: [~/Projects/agno-agi/demo-os]
confidence: high
---

# AgentOS Demo (demo-os)

> Agno 官方多 Agent 演示系统：14 Agent + 9 Team + 5 Workflow + 3 多框架 Agent，覆盖 50+ Agno 框架核心特性。Python 3.12+，137 个 Python 文件，Apache 2.0 许可。

---

## 核心价值主张

| 维度 | 说明 |
|------|------|
| 框架 showcase | 一个项目演示 Agno 框架 50+ 特性（Agent/Team/Workflow/RAG/HITL/Guardrail/Reasoning/Multimodal/MCP/…) |
| 生产级架构 | PostgreSQL + pgvector 持久化、AgentOS 运行时（调度/授权/追踪）、Docker + Railway 部署 |
| 多框架集成 | Claude Agent SDK / LangGraph / DSPy 三种外部框架 Agent 融入统一运行时 |
| 自评估闭环 | AgentAsJudgeEval post-hook 自动质量评分、Smoke/Reliability/Accuracy/Performance 四层 eval 体系 |

## 整体架构

```
                    ┌─────────────────────────────────────────────┐
                    │              AgentOS Runtime                 │
                    │  (FastAPI / Uvicorn / Scheduler / Auth)      │
                    └──────────────┬──────────────────────────────┘
                                   │
          ┌────────────────────────┼────────────────────────────┐
          │                        │                            │
    ┌─────▼─────┐          ┌──────▼──────┐            ┌────────▼───────┐
    │  Agents    │          │   Teams      │            │  Workflows     │
    │  (14+3)   │          │   (9)        │            │   (5)          │
    ├───────────┤          ├──────────────┤            ├────────────────┤
    │ Docs      │          │ Dash         │            │ Morning Brief  │
    │ MCP       │          │ Research ×4  │            │ AI Research    │
    │ Helpdesk  │          │ Investment×4 │            │ Content Pipeline│
    │ Feedback  │          └──────┬───────┘            │ Repo Walkthrough│
    │ Approvals │                 │                    │ Support Triage │
    │ Reasoner  │                 │                    └───────┬────────┘
    │ Reporter  │                 │                            │
    │ Contacts  │          ┌──────▼───────┐            ┌───────▼────────┐
    │ Studio    │          │ Multi-FW     │            │   Shared       │
    │ Scheduler │          │ (Claude/LG/  │            │   Layer        │
    │ Taskboard │          │  DSPy)       │            ├────────────────┤
    │ Compressor│          └──────────────┘            │ PostgreSQL     │
    │ Injector  │                                      │ (pgvector)     │
    │ Craftsman │                                      │ Registry       │
    └───────────┘                                      │ (Models+Tools) │
                                                       │ config.yaml    │
                                                       └────────────────┘
```

## Agent 详解（14 个原生 + 3 个多框架）

### 文档与搜索类

| Agent | 核心特性 | 工具 |
|-------|---------|------|
| **Docs** | LLMs.txt 动态文档获取、AgentAsJudge 自动评分 | `LLMsTxtTools(allowed_hosts=["docs.agno.com"])` |
| **MCP** | MCP 协议外部工具集成 | MCP live tools |

### HITL 与安全类

| Agent | 核心特性 | 工具 |
|-------|---------|------|
| **Helpdesk** | 4 重 Guardrail（OpenAI Moderation / PII 检测 / Prompt Injection / Output）、审计日志、HITL 确认 | 自定义运维工具 + `UserFeedbackTools` |
| **Feedback** | 用户反馈控制流（ask_user）、动态调整 | `UserFeedbackTools` |
| **Approvals** | 阻塞式审批流 + 审计追踪 | 审批工具 |

### 推理与输出类

| Agent | 核心特性 | 工具 |
|-------|---------|------|
| **Reasoner** | 原生 Reasoning Mode（2-8 步）、Model Fallback（→ Claude Sonnet 4.6）、Exa MCP | `ReasoningTools` + Parallel + Exa |
| **Reporter** | Pydantic 结构化输出、CSV/JSON/PDF 文件生成 | `FileGenerationTools` + Reporter tools |

### 记忆与状态类

| Agent | 核心特性 | 工具 |
|-------|---------|------|
| **Contacts** | Entity Memory（人/组织/关系）、User Profile、Session Planning | 实体记忆工具 |
| **Taskboard** | Session State + Agentic State（待办/完成/分类） | 状态管理工具 |

### 多媒体类

| Agent | 核心特性 | 工具 |
|-------|---------|------|
| **Studio** | DALL-E 图像生成、ElevenLabs TTS + 音效、FAL 图转图、Luma 视频生成 | `DalleTools` / `ElevenLabsTools` / `FalTools` / `LumaLabTools` |

### 基础设施类

| Agent | 核心特性 | 工具 |
|-------|---------|------|
| **Scheduler** | SchedulerTools CRUD（创建/列表/启用/禁用/删除 cron 任务） | `SchedulerTools` |
| **Compressor** | `CompressionManager` 工具结果压缩 | `CompressionManager` |
| **Injector** | `RunContext` 依赖注入 | `RunContext` |
| **Craftsman** | `LocalSkills` 技能系统加载 | `LocalSkills` |

### 多框架 Agent（3 个）

| Agent | 框架 | 架构 |
|-------|------|------|
| **Repo Explainer** | Claude Agent SDK | WebSearch + WebFetch 解释 GitHub 仓库 |
| **Debate Bot** | LangGraph | `START → pro → con → judge → END` StateGraph，共享 `DebateState` |
| **Math Solver** | DSPy | `ChainOfThought` typed signature 解数学应用题 |

## Team 详解（9 个）

| Team | 模式 | 成员 | 亮点 |
|------|------|------|------|
| **Dash** | `coordinate` | Analyst + Engineer | SQL 工具 + RAG 知识库 + Learning + AgentAsJudge |
| **Research ×4** | `coordinate` / `route` / `broadcast` / `tasks` | 4 个研究员 | 同一团队 4 种编排模式对比 |
| **Investment ×4** | `coordinate` / `route` / `broadcast` / `tasks` | 7 个投资 Agent | YFinance + 知识库 + Learning |

4 种 Team 模式：
- **coordinate**: Leader 分配任务给成员，汇总结果
- **route**: Leader 选择最合适的成员处理
- **broadcast**: 所有成员并行处理同一请求
- **tasks**: Leader 将请求拆解为独立任务分配

## Workflow 详解（5 个）

```
Morning Brief:
  Parallel(日历扫描, 邮件处理, 新闻聚合) → 综合简报

AI Research:
  Parallel(4个研究员并行) → 综合报告

Content Pipeline:
  Router(分类) → Parallel(写作+配图) → Loop(质量检查) → HITL(审核)

Repo Walkthrough:
  代码分析 → 脚本生成 → 语音旁白

Support Triage:
  Router(分类器→3个专家) → Condition(高严重度→升级)
```

## 数据流

1. **用户请求** → AgentOS FastAPI 端点 → 路由到 Agent/Team/Workflow
2. **Agent 处理** → 加载上下文（datetime + history + memory + knowledge）→ LLM 调用
3. **工具执行** → 工具调用（搜索/数据库/API/文件）→ 结果返回 Agent
4. **Guardrail 检查** → Pre-hook（Moderation/PII/Injection）→ Post-hook（Output/审计/评分）
5. **Team 协作** → Leader 分配 → 成员执行 → 汇总 → 返回
6. **Workflow 编排** → Step/Parallel/Router/Condition/Loop → 逐步执行
7. **持久化** → 会话存 PostgreSQL、向量存 PgVector、知识库检索 hybrid search

## 持久化层

| 存储 | 技术 | 用途 |
|------|------|------|
| 会话历史 | PostgreSQL + `PostgresDb` | Agent 对话记录、Agentic Memory |
| 向量检索 | PgVector + `text-embedding-3-small` | Dash/Investment 知识库 hybrid search |
| 知识内容 | PostgreSQL + `contents_db` | 知识库原始内容存储 |
| 调度任务 | AgentOS Scheduler | Cron 定时任务（Morning Brief / AI Research） |

## 项目结构

```
demo-os/
├── agents/                 # 14 个原生 Agent
│   ├── docs/              # LLMs.txt 文档查询
│   ├── mcp/               # MCP 协议外部工具
│   ├── helpdesk/          # HITL + 4 重 Guardrail
│   ├── feedback/          # 用户反馈控制流
│   ├── approvals/         # 审批流 + 审计
│   ├── reasoner/          # Reasoning + Fallback
│   ├── reporter/          # 结构化输出 + 文件生成
│   ├── contacts/          # 实体记忆 + 关系
│   ├── studio/            # 多媒体（DALL-E/TTS/FAL/Luma）
│   ├── scheduler/         # 调度管理 CRUD
│   ├── taskboard/         # Session State + Agentic State
│   ├── compressor/        # 工具结果压缩
│   ├── injector/          # 依赖注入 RunContext
│   ├── craftsman/         # LocalSkills 技能系统
│   └── dash/              # 数据分析团队（Analyst + Engineer）
├── frameworks/             # 3 个多框架 Agent
│   ├── claude_repo/       # Claude Agent SDK
│   ├── langgraph_debate/  # LangGraph StateGraph
│   └── dspy_math/         # DSPy ChainOfThought
├── teams/                  # 8 个 Team 配置
│   ├── research/          # 4 模式（coordinate/route/broadcast/tasks）
│   └── investment/        # 4 模式 + YFinance
├── workflows/              # 5 个 Workflow
│   ├── morning_brief/     # 并行情报收集
│   ├── ai_research/       # 并行研究
│   ├── content_pipeline/  # 路由+并行+循环+HITL
│   ├── repo_walkthrough/  # 代码→脚本→语音
│   └── support_triage/    # 分类→路由→升级
├── app/                    # 应用核心
│   ├── main.py            # AgentOS 入口
│   ├── settings.py        # 模型/DB/环境配置
│   ├── registry.py        # 共享 Models + Tools 注册表
│   └── config.yaml        # Quick prompts
├── db/                     # 数据库层
│   ├── session.py         # PostgresDb + Knowledge 工厂
│   └── url.py             # 环境变量构建 DB URL
├── evals/                  # 四层评估体系
│   ├── smoke.py           # Smoke 测试（无 LLM 成本）
│   ├── reliability.py     # 工具调用验证
│   ├── cases/             # 测试用例
│   ├── performance.py     # 性能基线
│   └── improve.py         # 自动改进循环
├── scripts/                # 运维脚本
├── .github/workflows/      # CI（validate + smoke + promote-to-prod）
├── Dockerfile              # 非 root 多阶段构建
├── compose.yaml            # 本地开发（pgvector + api）
└── pyproject.toml          # 依赖管理
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Python 3.12+ |
| 框架 | Agno `agno[os]`（含 AgentOS 运行时） |
| 数据库 | PostgreSQL 17 + pgvector（hybrid search） |
| LLM 默认 | OpenAI GPT-5.5（Responses API） |
| LLM 可选 | Claude Opus 4.7 / Sonnet 4.6 / Haiku 4.5、Gemini 3.1 Pro / 3 Flash |
| 外部框架 | Claude Agent SDK、LangGraph、DSPy |
| 多媒体 | DALL-E 3 / ElevenLabs / FAL / LumaLab |
| 工具 | Exa / YFinance / DuckDuckGo / Arxiv / PubMed / HackerNews / YouTube |
| 部署 | Docker + Railway（3 replicas, 4 vCPU, 8Gi） |
| CI | GitHub Actions（validate + smoke-testing + promote-to-prod） |
| 代码质量 | Ruff（lint/format）+ mypy（类型检查） |
| 许可 | Apache 2.0 |

## 构建与测试

```bash
# 本地开发
./scripts/venv_setup.sh && source .venv/bin/activate
docker compose up -d --build

# 格式化 & 验证
./scripts/format.sh && ./scripts/validate.sh

# Smoke 测试（无 LLM 成本）
python -m evals smoke
python -m evals smoke --group agents --group security

# Reliability 测试
python -m evals reliability --entity helpdesk

# 完整 evals（有 LLM 成本）
python -m evals --category accuracy

# 性能基线
python -m evals perf --update-baselines

# 自动改进循环
python -m evals improve --entity docs
```

## 设计权衡

1. **单 DB 全共享** — 所有 Agent 共用同一 PostgreSQL。权衡：简化部署但缺少租户隔离（生产环境通过 `AuthorizationConfig(user_isolation=True)` 弥补）
2. **API key 门控** — Models/Tools 注册表按 env var 动态加载。权衡：缺少 key 时代码仍可导入，但部分 Agent 功能受限
3. **SSRF 防护** — Docs Agent 的 `LLMsTxtTools(allowed_hosts=["docs.agno.com"])`。权衡：严格域名白名单，无法查询其他文档站
4. **AgentAsJudge 自动评分** — Docs/Dash Agent 的 post-hook。权衡：每次对话额外 LLM 调用（成本 + 延迟），但建立质量闭环
5. **多框架 Agent 类型忽略** — Claude/LangGraph/DSPy Agent 用 `# type: ignore[list-item]` 绕过类型检查。权衡：Agno Agent 类型系统暂不覆盖外部框架
6. **Quick prompts 配置化** — `config.yaml` 为每个 Agent 提供 3 个预设 prompt。权衡：降低试用门槛但非核心功能

## 评估体系

| 层级 | 类型 | 成本 | 说明 |
|------|------|------|------|
| **Smoke** | 结构断言 | 无 LLM | 验证 Agent 响应格式、Guardrail 触发、工具调用结构 |
| **Reliability** | 工具调用验证 | 无 LLM | 验证特定工具被正确调用 |
| **Accuracy** | AgentAsJudgeEval | 有 LLM | LLM 裁判评估回答质量 |
| **Performance** | 基线对比 | 有 LLM | 延迟/Token 消耗基线追踪 |
| **Improve** | 自动改进 | 有 LLM | `--entity` 循环改进特定 Agent |

## 部署

- **Docker Compose** — 本地开发（`demo-os-db` + `demo-os-api`）
- **Railway** — 生产部署（3 replicas, 4 vCPU, 8Gi）
  - `railway_up.sh` / `railway_redeploy.sh` / `railway_env.sh`
  - `promote-to-prod.yml` — main → release 一键发布，带 tag 回滚
  - staging 环境降配（reduced resources）
- **Dockerfile** — 多阶段构建，非 root `app` 用户，只读代码卷

## 相关链接

- 源码：`~/Projects/agno-agi/demo-os`（私有仓库）
- [[agno]] — 底层 Agno 框架 SDK
- [[agno-documentation-system]] — Agno 五层文档体系
