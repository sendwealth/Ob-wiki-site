---
title: Agno
created: 2026-05-28
updated: 2026-05-28
type: entity
tags: [ai, platform, agent, framework, python, open-source, agentic, product]
sources:
  - https://github.com/agno-agi/agno
  - libs/agno/agno/ source code analysis
confidence: high
---

# Agno

> 全栈 AI Agent 平台 SDK（Python）：构建、运行、管理 Agent。40.4K GitHub Stars，55+ 模型供应商，100+ 工具集成，20+ 向量数据库。从单 Agent 原型到多 Agent 生产系统的完整路径。

---

## 一句话定位

Agno 是一个 **Agent 平台 SDK**，不只是 Agent 框架 — 它覆盖从 Agent 定义、多 Agent 编排、知识库/RAG、工具调用、到生产部署（API 服务、调度、安全、可观测性）的全链路。

## 关键数据

| 指标 | 值 |
|------|-----|
| GitHub Stars | 40.4K |
| Forks | 5.4K |
| 版本 | 2.6.9 |
| Python 文件数 | 855 |
| 模型供应商 | 50+ (OpenAI, Anthropic, Google, AWS, Azure, DeepSeek, Ollama, vLLM, Groq, Together, Fireworks, Cerebras, Mistral, Cohere, HuggingFace, IBM, NVIDIA, xAI, Perplexity, Cloudflare, etc.) |
| 工具集成 | 100+ (GitHub, Slack, Discord, Docker, E2B, Daytona, Notion, Jira, Linear, Shopify, Salesforce, etc.) |
| 向量数据库 | 20+ (PgVector, Pinecone, Qdrant, Milvus, Weaviate, Chroma, LanceDB, Redis, MongoDB, ClickHouse, Cassandra, etc.) |
| Embedder 供应商 | 17+ |
| 许可证 | Apache 2.0 |
| 作者 | Ashpreet Bedi |

## 架构

```
┌─────────────────────────────────────────────────────────┐
│                     Agno OS (生产运行时)                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ REST API  │  │ Scheduling│  │ Security │  │Tracing  │ │
│  │ SSE/WS   │  │ Cron Jobs │  │ JWT RBAC │  │OTel     │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │Interfaces│  │ Approval │  │ Storage  │  │Context  │ │
│  │Slack/TG/ │  │ Human-in │  │ Sessions │  │Providers│ │
│  │WA/Discord│  │ -the-loop│  │ Memory   │  │MCP/Drive│ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
├─────────────────────────────────────────────────────────┤
│                   编排层                                   │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐              │
│  │  Agent   │  │   Team   │  │ Workflow │              │
│  │ (single) │  │(multi-   │  │ (DAG/    │              │
│  │          │  │ agent)   │  │  steps)  │              │
│  └──────────┘  └──────────┘  └──────────┘              │
├─────────────────────────────────────────────────────────┤
│                   能力层                                   │
│  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌──────┐ │
│  │Knowledge│ │ Memory │ │ Tools │ │Reasoning│ │Guard │ │
│  │  /RAG  │ │Manager │ │100+   │ │Multi-  │ │rails │ │
│  │20+ VDB │ │        │ │       │ │provider│ │PII/  │ │
│  └────────┘ └────────┘ └────────┘ └────────┘ │inject│ │
│  ┌────────┐ ┌────────┐ ┌────────┐            └──────┘ │
│  │ Skills │ │ Learn  │ │ Eval  │                      │
│  └────────┘ └────────┘ └────────┘                      │
├─────────────────────────────────────────────────────────┤
│                   模型层                                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │ 50+ Model Providers + Fallback + Router          │  │
│  │ OpenAI / Anthropic / Google / AWS / Azure / ...  │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

## 核心模块详解

### Agent（单 Agent）

`Agent` 类是核心原语，dataclass 实现，字段包括：

- **model**: 任意模型供应商实例，支持 `fallback_models` + `FallbackConfig`（错误特定路由）
- **tools**: Function / Toolkit 列表，支持 MCP 工具
- **knowledge**: RAG 知识库，支持 20+ 向量数据库
- **memory**: `MemoryManager` 管理会话记忆
- **guardrails**: 输入/输出护栏（PII 检测、注入检测、OpenAI moderation）
- **reasoning**: 推理能力（支持 Anthropic/OpenAI/Gemini/DeepSeek/Groq/Ollama 等 10+ 供应商的推理模式）
- **skills**: 内置技能系统
- **eval**: 内置评估框架
- **compression**: 上下文压缩管理器
- **culture**: 文化知识管理

所有公共方法提供 **同步 + 异步** 双变体（`run` / `arun`）。

### Team（多 Agent 编排）

- 多种编排模式（通过 `mode.py`）
- Task 分配（`task.py` / `_task_tools.py`）
- 支持 `parser_model` 做任务路由
- 远程 Team 支持（`remote.py`）

### Workflow（工作流）

- Step-based 工作流（`step.py` / `steps.py`）
- 条件分支（`condition.py`）
- 并行执行（`parallel.py`）
- 循环（`loop.py`）
- 路由（`router.py`）
- Celery 集成（`cel.py`）
- 装饰器 API（`decorators.py`）

### Knowledge / RAG

```
knowledge/
  ├── chunking/      — 文本分块策略
  ├── document/      — 文档模型
  ├── embedder/      — 17+ 嵌入供应商
  ├── reader/        — 文档读取器（CSV, PDF, URL, etc.）
  ├── loaders/       — 数据加载器
  ├── reranker/      — 重排序（Cohere, SentenceTransformer, AWS Bedrock, Infinity）
  └── remote_knowledge.py — 远程知识库
```

### Tools（工具系统）

100+ 预构建工具，关键类别：

| 类别 | 工具举例 |
|------|---------|
| 开发工具 | Python, Shell, Docker, E2B, Daytona, File |
| 通信 | Slack, Discord, Telegram, WhatsApp, Email, Gmail, Zoom |
| 项目管理 | Jira, Linear, Trello, ClickUp, Todoist, Notion, Confluence |
| 数据搜索 | Exa, Brave Search, Tavily, Serper, DuckDuckGo, PubMed, ArXiv |
| 云/AWS | Lambda, SES, BigQuery, Redshift |
| 金融 | YFinance, Financial Datasets |
| AI/ML | DALL-E, Replicate, Fal, Cartesia, ElevenLabs |
| 代码托管 | GitHub, GitLab, Bitbucket |
| 数据处理 | DuckDB, Pandas, CSV Toolkit, SQL, Neo4j |
| MCP | MCP 工具协议原生支持 |
| 浏览器 | BrowserBase, Crawl4AI, Firecrawl, Spider, Jina |

### Agno OS（生产运行时）

`agno.os` 模块提供完整的 **AgentOS**：

- **Production API**: 50+ 端点，SSE + WebSocket
- **Storage**: 会话/记忆/知识/追踪持久化
- **Scheduling**: Cron 调度，无需外部基础设施
- **Security**: JWT RBAC，多租户隔离
- **Observability**: OpenTelemetry 追踪，运行历史，审计日志
- **Human Approval**: 运行暂停等待确认，工具级审批控制
- **Interfaces**: Slack, Telegram, WhatsApp, Discord, AG-UI, A2A
- **Context Providers**: 实时数据接入（Slack, Drive, Wiki, MCP, 自定义）

### Guardrails（护栏）

- `openai.py` — OpenAI moderation
- `pii.py` — 个人身份信息检测
- `prompt_injection.py` — 提示注入检测

### Reasoning（推理）

按供应商优化：Anthropic, Azure AI Foundry, DeepSeek, Gemini, Groq, Ollama, OpenAI, VertexAI + 默认推理管理器。

## 技术栈

| 层面 | 技术 |
|------|------|
| 语言 | Python 3.7+ |
| 数据模型 | Pydantic + dataclass |
| HTTP | httpx (HTTP/2) |
| CLI | Typer + Rich |
| 配置 | pydantic-settings + python-dotenv |
| API 服务器 | FastAPI + Uvicorn (可选) |
| 数据库 | SQLAlchemy (可选) |
| 追踪 | OpenTelemetry (可选) |
| 格式化/校验 | Ruff (format + check), mypy |

## 数据流

```
用户输入
  │
  ▼
Agent.run() / Agent.arun()
  │
  ├── 1. Guardrails 检查（输入）
  ├── 2. 加载 Memory / Context
  ├── 3. Knowledge RAG 检索（如配置）
  ├── 4. 组装 Prompt（system + user + context + knowledge）
  ├── 5. 调用 Model（带 Fallback）
  ├── 6. 解析 Response
  │     ├── 纯文本 → 返回
  │     └── Tool Call → 执行 Tool → 回到 4（循环）
  ├── 7. Guardrails 检查（输出）
  ├── 8. 更新 Memory / Session
  └── 9. 返回 RunOutput
```

## 设计哲学

1. **自有 Agent 栈** — 数据、上下文、工具、权限、记忆、人工审核全部可控
2. **从简单开始** — 单 Agent → Team → Workflow，按需扩展
3. **生产就绪** — 内置安全、可观测性、调度、多租户
4. **供应商无关** — 50+ 模型供应商可互换，工具系统统一接口
5. **同步 + 异步** — 所有公共 API 双变体

## 与同类框架对比

| 维度 | Agno | LangChain/LangGraph | CrewAI | Google ADK |
|------|------|---------------------|--------|------------|
| 定位 | Agent 平台 SDK | LLM 编排框架 | 多 Agent 框架 | Agent 开发工具 |
| 生产运行时 | 内置 (Agno OS) | LangServe (独立) | 无 | 无 |
| 模型供应商 | 50+ | 50+ | ~10 | Google 为主 |
| 工具集成 | 100+ | 100+ | ~20 | ~30 |
| 多 Agent | Team + Workflow | LangGraph | 原生 | 原生 |
| 向量数据库 | 20+ | 20+ | ~5 | ~5 |
| 安全/RBAC | 内置 | 无 | 无 | 无 |
| 调度 | 内置 | 无 | 无 | 无 |

## 适用场景

- 需要**从原型到生产**全路径的 Agent 项目
- 需要**多 Agent 编排**（Team 模式、Workflow DAG）
- 需要**RAG 知识库** + 灵活向量数据库选择
- 需要**生产级 API** + 安全 + 可观测性
- 需要**多模型供应商**灵活切换和 Fallback
- 需要**定时调度**和**人工审批**流程

## 相关链接

- GitHub: https://github.com/agno-agi/agno
- 文档: https://docs.agno.com
- MCP 服务器: https://docs.agno.com/mcp

---

**相关概念**: [[agentic-rag]] | [[a2a-protocol]] | [[codegraph]] | [[superpowers]]

**相关实体**: [[adk-python]] | [[ruflo]] | [[swarmclaw]] | [[orloj]]
