---
title: Google Agents CLI
created: 2026-05-29
updated: 2026-05-29
type: entity
tags: [google, agent-framework, ai-agent, coding-agent, cli, adk, gemini, cloud-run, gke, terraform, evaluation, scaffold, mcp, a2a, rag, observability]
sources:
  - https://github.com/google/agents-cli
  - https://google.github.io/agents-cli/
  - https://pypi.org/project/google-agents-cli/
  - ~/Projects/agents-cli/
confidence: high
---

# Google Agents CLI

> Google 官方 CLI + Skills 工具链，为编码 Agent（Claude Code / Gemini CLI / Codex）提供在 Gemini Enterprise Agent Platform 上构建、评估和部署 ADK Agent 的完整生命周期支持。当前版本 v0.2.1（2026-05-28），Pre-GA。

---

## 1. 项目定位

`agents-cli` **不是编码 Agent**，而是**为编码 Agent 服务的工具**。它回答的核心问题是：

> "如何让 Claude Code / Gemini CLI / Codex 这样的编码 Agent 更擅长构建、评估和部署 AI Agent？"

**关键区分**：
- [ADK](https://adk.dev) 是 Agent **框架**（写 Agent 代码）
- `agents-cli` 是 Agent **工具链**（脚手架 → 开发 → 评估 → 部署 → 发布 → 可观测性）
- [Gemini CLI](https://github.com/google-gemini/gemini-cli) / [Claude Code](https://docs.anthropic.com/en/docs/claude-code) / [Codex](https://github.com/openai/codex) 是**编码 Agent**（用户交互层）

**开发者**: Google 官方团队 | **许可**: Apache-2.0 | **发布节奏**: ~1 周/版本

## 2. 架构概览

```
┌──────────────────────────────────────────────────────────┐
│                    编码 Agent 层                          │
│  Claude Code | Gemini CLI | Codex | Copilot | 任意 Agent  │
└──────────────┬───────────────────────────┬───────────────┘
               │  Skills 安装               │  CLI 调用
               ▼                           ▼
┌──────────────────────┐   ┌──────────────────────────────┐
│   7 个 Agent Skills   │   │     agents-cli 命令行工具     │
│  ┌─────────────────┐  │   │                              │
│  │ adk-code        │  │   │  setup / login               │
│  │ scaffold        │  │   │  scaffold / enhance / upgrade │
│  │ eval            │  │   │  run / install / lint        │
│  │ deploy          │  │   │  eval run / compare / optimize│
│  │ publish         │  │   │  deploy                      │
│  │ observability   │  │   │  publish gemini-enterprise    │
│  │ workflow        │  │   │  infra / data-ingestion       │
│  └─────────────────┘  │   │  info / update               │
└──────────────────────┘   └──────────────┬───────────────┘
                                          │
                           ┌──────────────▼───────────────┐
                           │   Google Cloud Agent Stack    │
                           │  Cloud Run / GKE / Agent      │
                           │  Runtime / BigQuery / Cloud   │
                           │  Trace / Terraform            │
                           └──────────────────────────────┘
```

## 3. Skills 体系（7 个技能包）

每个 Skill 是一组 Markdown 文件（SKILL.md + references/），安装到编码 Agent 的技能目录中，告诉 Agent 如何执行特定任务。

| Skill | 职责 | 核心文件 |
|-------|------|----------|
| `google-agents-cli-workflow` | 开发生命周期、代码保护规则、模型选择 | `internals.md` |
| `google-agents-cli-adk-code` | Python API 参考：Agent/Tool/Orchestration/Callback/State | `adk-python.md`, `adk-2.0.md` |
| `google-agents-cli-scaffold` | 项目脚手架：创建/增强/升级 | `flags.md` |
| `google-agents-cli-eval` | 评估方法论：metrics/evalsets/LLM-as-judge/trajectory | `criteria-guide.md`, `builtin-tools-eval.md`, `multimodal-eval.md`, `user-simulation.md` |
| `google-agents-cli-deploy` | 部署：Agent Runtime/Cloud Run/CI+CD/Secrets/GKE | `cloud-run.md`, `gke.md`, `cicd-pipeline.md`, `terraform-patterns.md`, `agent-runtime.md`, `batch-inference.md`, `testing-deployed-agents.md` |
| `google-agents-cli-publish` | Gemini Enterprise 注册 | `SKILL.md` |
| `google-agents-cli-observability` | 可观测性：Cloud Trace/Logging/BigQuery Analytics | `cloud-trace-and-logging.md`, `bigquery-agent-analytics.md` |

**技能安装方式**: `agents-cli setup` → 自动检测已安装的编码 Agent → 将 Skills 写入其技能目录。

## 4. CLI 命令全景

### 4.1 初始化与认证

| 命令 | 说明 |
|------|------|
| `agents-cli setup` | 安装 CLI + Skills 到所有检测到的编码 Agent |
| `agents-cli login` | 认证（Google Cloud ADC 或 AI Studio API Key） |
| `agents-cli login --status` | 查看认证状态 |

### 4.2 脚手架

| 命令 | 说明 |
|------|------|
| `agents-cli scaffold <name>` | 创建新 Agent 项目（3 种模板） |
| `agents-cli scaffold enhance` | 为已有项目添加部署/CI-CD/RAG |
| `agents-cli scaffold upgrade` | 升级到新版本 agents-cli 配置格式 |

### 4.3 开发

| 命令 | 说明 |
|------|------|
| `agents-cli run "prompt"` | 单次 prompt 运行 Agent |
| `agents-cli install` | 安装项目依赖 |
| `agents-cli lint` | Ruff 代码质量检查 |

### 4.4 评估

| 命令 | 说明 |
|------|------|
| `agents-cli eval run` | 运行评估（LLM-as-judge + trajectory scoring） |
| `agents-cli eval compare` | 比较两次评估结果 |
| `agents-cli eval optimize` | 自动优化（v0.2.0 新增） |

### 4.5 部署与发布

| 命令 | 说明 |
|------|------|
| `agents-cli deploy` | 部署到 Google Cloud（Cloud Run / GKE） |
| `agents-cli publish gemini-enterprise` | 注册到 Gemini Enterprise |
| `agents-cli infra single-project` | 单项目基础设施（Terraform plan） |
| `agents-cli infra cicd` | CI/CD 管线 + staging/prod 环境 |
| `agents-cli infra datastore` | RAG 数据存储基础设施 |
| `agents-cli data-ingestion` | 运行数据导入管线 |

## 5. 三种项目模板

| 模板 | 用途 | 特点 |
|------|------|------|
| `adk` | 单 Agent 项目 | 基础 Agent + Tools + evals |
| `adk_a2a` | 多 Agent A2A 协作 | Agent-to-Agent Protocol 协调 |
| `agentic_rag` | 检索增强 Agent | 内置数据存储 + 导入管线 |

### 生成的项目结构

```
my-agent/
├── app/
│   ├── __init__.py           # 导出 app
│   ├── agent.py              # Agent 定义（instruction + model + tools）
│   └── app_utils/
│       ├── telemetry.py      # OpenTelemetry → Cloud Trace
│       ├── typing.py         # Pydantic 请求/响应模型
│       └── gcs.py            # GCS 工具函数
├── tests/
│   ├── eval/evalsets/        # 评估数据集
│   ├── eval/eval_config.json # LLM-as-judge 评估标准
│   ├── integration/          # 集成测试
│   └── unit/                 # 单元测试
├── agents-cli-manifest.yaml  # 项目配置（v0.2.0 新格式）
├── GEMINI.md                 # 编码 Agent 指导文件
├── pyproject.toml            # 依赖
├── Makefile                  # 快捷命令
└── .env                      # 环境变量
```

## 6. 核心工作流

```
setup → scaffold → build → eval → deploy → observe → iterate
  │         │         │       │       │         │
  ▼         ▼         ▼       ▼       ▼         ▼
Skills    模板生成   ADK    LLM    Cloud     Trace
安装     3种模板    编码   judge   Run/GKE   BQ
```

1. **Setup**: `agents-cli setup` — 一键安装 Skills 到编码 Agent
2. **Scaffold**: 编码 Agent 用 `agents-cli scaffold` 创建项目
3. **Build**: 编码 Agent 按 ADK Skill 指导编写 Agent 代码
4. **Evaluate**: `agents-cli eval run` — LLM-as-judge + trajectory scoring
5. **Deploy**: `agents-cli deploy` — Cloud Run / GKE / Agent Runtime
6. **Observe**: Cloud Trace + BigQuery Analytics 监控 Agent 行为

## 7. 使用场景

### Beginner（单 Agent）
- **Daily News Bot**: RSS → LLM 摘要 → Google Chat（Cloud Scheduler 定时）
- **Industry Watch**: 追踪竞品文档/发布/招聘 → 趋势分析

### Intermediate（Agent + 反馈环/RAG）
- **Self-Tuning Support**: 每次对话后自动 eval → 草拟新 eval case → 覆盖度自适应
- **Technical Investigation**: "为什么支付延迟了？" → 日志+部署+历史事件 → 根因分析
- **Organizational Memory**: 索引 Chat/Email/设计文档 → 检索历史决策（`agentic_rag` 模板）

### Advanced（多 Agent 协作/A2A）
- **Incident Response**: 4 个专家 Agent 并行（变更定位/错误关联/历史搜索/客户通信）
- **Distributed Code Migration**: 数据模型/API/测试/验证 4 个 Agent 通过 A2A 协调
- **Due Diligence**: 索引 50 万行代码 → 技术债/安全/许可证/部署复杂度 → 风险报告

## 8. 版本演进

| 版本 | 日期 | 里程碑 |
|------|------|--------|
| v0.0.3 | 2026-04-15 | 初始公开版本 |
| v0.1.0 | 2026-04-21 | 功能完善 |
| v0.1.2 | 2026-04-29 | Windows 兼容、artifact 保存、auth 修复 |
| v0.1.3 | 2026-05-06 | Terraform plan 默认、Cloud Shell 兼容、OS info |
| v0.2.0 | 2026-05-15 | **重大更新**: manifest.yaml 独立配置、eval optimize、Claude/Gemini CLI plugin 支持、性能优化 |
| v0.2.1 | 2026-05-28 | 最新版本 |

## 9. 技术栈

| 层 | 技术 |
|----|------|
| CLI 框架 | Python (pyproject.toml + uvx 分发) |
| Agent 框架 | [Google ADK](https://adk.dev) (Python) |
| 默认模型 | Gemini Flash (`gemini-flash-latest`) |
| 基础设施 | Terraform (默认 plan 不 apply) |
| 容器运行时 | Cloud Run / GKE |
| CI/CD | GitHub Actions + Terraform |
| 可观测性 | OpenTelemetry → Cloud Trace + BigQuery |
| 评估 | LLM-as-judge + trajectory scoring + multimodal eval |
| 协议 | [[a2a-protocol]] (Agent-to-Agent) |
| 数据存储 | Cloud SQL + pgvector / Agent Platform Search |

## 10. 设计决策与权衡

### 优势
- **Skills-First 设计**: 把 Agent 构建知识编码为 Markdown 技能文件，编码 Agent 直接消费
- **本地开发免费**: scaffold/run/eval 只需 AI Studio API Key，不需要 Google Cloud
- **渐进式复杂度**: prototype → enhance → deploy，从简单到复杂平滑过渡
- **编码 Agent 无关**: 支持 Claude Code、Gemini CLI、Codex、Copilot 等任意编码 Agent
- **评估内置**: eval 不是事后补丁，而是核心工作流的一部分

### 局限
- **仅支持 Python Agent**: 暂不支持 Go/Java/TypeScript
- **Google Cloud 锁定**: 部署层绑定 GCP（Cloud Run/GKE/BigQuery）
- **Pre-GA**: 功能和 API 可能变化，支持有限
- **仅 Gemini 模型**: 默认使用 Gemini，其他 LLM 需要额外配置
- **不支持实时语音/视频**

## 11. 在生态中的位置

| 维度 | agents-cli | [[adk-python]] | [[ecc]] |
|------|-----------|---------------|---------|
| 定位 | Agent 工具链 | Agent 框架 | 编码 Agent 优化 |
| 用户 | 编码 Agent | 开发者 | 开发者 |
| 核心价值 | 生命周期管理 | Agent 代码编写 | 编码体验增强 |
| 协议 | A2A（通过模板） | A2A/MCP | MCP |
| 部署 | Cloud Run/GKE | 自行部署 | N/A |

## 12. 关联

- [[adk-python]] — agents-cli 构建在其上的 Agent 框架
- [[a2a-protocol]] — adk_a2a 模板使用的 Agent 间通信协议
- [[agentic-rag]] — agentic_rag 模板实现的检索增强模式
- [[ecc]] — 另一个为编码 Agent 提供技能的项目（通用 vs 专用于 Google Agent 平台）
- [[kagent]] — Kubernetes 原生 Agent 管理，类似的声明式 Agent 定义思路
- [[context-mode]] — 编码 Agent 上下文窗口优化工具，互补关系
