---
title: Open WebUI
created: 2026-07-25
updated: 2026-07-25
type: entity
tags: [llmops, chat-ui, self-hosted, rag, mcp, open-source]
sources: [https://github.com/open-webui/open-webui, https://docs.openwebui.com/]
confidence: high
---

# Open WebUI

> 可扩展、功能丰富、用户友好的自托管 AI 平台，主打完全离线运行。支持 Ollama、OpenAI 兼容 API 等多种 LLM runner，内置 RAG 推理引擎，定位是「强大的 AI 部署解决方案」。当前版本 v0.10.2（2026-07-01）。

## 定位与一句话总结

Open WebUI 不是又一个 ChatGPT 客户端，而是面向个人/团队/企业的**自托管 AI 中枢**：聊天、RAG、Agent、工具、自动化、频道协作、日历、记忆、终端、评估等能力全部集成在一个可离线部署的 Python + Svelte 应用中。它的核心护城河是**「一个界面把本地模型、远程 API、知识库、工具生态和团队协作串起来」**。

## 核心能力

| 能力 | 说明 |
|---|---|
| 多模型接入 | Ollama + OpenAI 兼容 API（OpenAI、Anthropic、Gemini、Groq、Mistral、OpenRouter、vLLM、LMStudio 等） |
| 自定义模型/Agent | 给基础模型包装 system prompt、工具、知识库，生成专用模型或 Agent |
| 插件扩展 | Filters / Actions / Pipes / Tools / Skills；支持 MCP、MCPO、OpenAPI 工具服务器 |
| 本地 RAG | 9 种向量库、混合搜索（BM25 + vector）、重排序、全上下文模式、多文档解析引擎 |
| 网络搜索 | 20+ 搜索源（SearXNG、Brave、Tavily、Firecrawl、Jina、Exa、Bing 等） |
| 持久记忆 | 跨会话记住用户事实，可注入 system prompt |
| 频道/协作 | 类似 Slack 的实时共享空间，AI 模型可被 @ 并协作 |
| 日历与自动化 | 内置日历 + 定时 prompt 自动化，运行结果回到日历 |
| 终端/代码执行 | 集成 Jupyter 代码执行、终端服务器（Open Terminal / Terminals Enterprise） |
| 企业功能 | RBAC、用户组、LDAP/SSO/SCIM、审计日志、OpenTelemetry、水平扩展 |
| 多模态 | 语音/视频通话、TTS/STT、图像生成与编辑（DALL·E、Gemini、ComfyUI、A1111） |

## 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                     SvelteKit 前端                          │
│  (Svelte 5 + Vite + Tailwind + TipTap + Socket.IO 客户端)   │
└───────────────────────┬─────────────────────────────────────┘
                        │ REST / WebSocket
┌───────────────────────▼─────────────────────────────────────┐
│                     FastAPI 后端                            │
│  routers/   → 30+ 路由模块（chats/models/openai/retrieval/   │
│              tools/skills/automations/channels/...）         │
│  models/    → SQLAlchemy 数据层（users/chats/knowledge/...） │
│  utils/     → 聊天编排、RAG、工具、权限、审计、任务等        │
│  retrieval/ → 文档解析、向量库、网络搜索                    │
│  socket/    → Socket.IO 实时层（Redis 可选）                │
└───────────────────────┬─────────────────────────────────────┘
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   SQLite/PostgreSQL  Redis          外部模型/Ollama
   (元数据)          (会话/任务/WS)  (OpenAI/Ollama API)
```

关键设计特点：
- **单一代码库**：前后端在同一仓库，构建时前端静态资源被复制到 `backend/open_webui/static`
- **配置数据库化**：大量运行时配置存在 `config` 表，通过 `Config.get_many()` 批量读取
- **模型统一抽象**：Ollama、OpenAI 兼容 API、Function Pipes 在 `utils/models.py` 合并为统一模型列表
- **插件热加载**：Functions/Tools 从数据库读取 Python 代码，用 `exec()` 动态加载模块
- **水平扩展**：Redis-backed WebSocket、任务管理、会话池

## 核心模块详解

### 1. 后端入口与生命周期

- `backend/open_webui/__init__.py`：CLI 入口（`open-webui serve`），负责生成/读取 `WEBUI_SECRET_KEY`
- `backend/open_webui/main.py`：FastAPI 应用组装，注册 30+ routers、中间件、静态文件、 lifespan
- `backend/open_webui/config.py`：运行配置中心，从环境变量 + `Config` 表读取，含模型连接、存储、OAuth、RAG 等
- `backend/open_webui/env.py`：环境/版本/日志初始化，解析 `package.json` 版本、加载 `.env`

### 2. 数据模型层

目录 `backend/open_webui/models/`，30 张表左右，核心实体：

| 表 | 作用 |
|---|---|
| `user` | 用户、角色、profile、OAuth、SCIM |
| `chat` | 聊天记录（JSON 大字段存消息树） |
| `chat_message` | 单条消息独立表 |
| `model` | 自定义模型/Agent 定义 |
| `knowledge` / `file` | 知识库与文件元数据 |
| `tool` / `function` / `skill` | 可插拔代码能力 |
| `config` | 运行时键值配置 |
| `access_grant` / `group` | 权限与访问控制 |
| `automation` / `automation_run` | 定时自动化 |
| `channel` / `note` | 协作频道与笔记 |
| `memory` | 持久化记忆 |
| `oauth_session` | OAuth 会话 |

使用 **SQLAlchemy 2.0 async** + Alembic 迁移（`migrations/versions/` 约 48 个版本）。支持 SQLite 与 PostgreSQL。

### 3. 聊天与模型路由

- `routers/chats.py`：聊天 CRUD、搜索、统计、导入导出、上下文压缩
- `routers/models.py`：自定义模型管理、访问控制
- `routers/openai.py`：OpenAI 兼容 API 代理，负责模型列表、chat completion、audio、images
- `routers/ollama.py`：Ollama API 代理
- `utils/chat.py`：`generate_chat_completion()` 核心调度，处理 Arena 模型、direct connection、过滤、流式
- `utils/models.py`：`get_all_models()` 聚合 function pipes + OpenAI + Ollama + Arena 模型

### 4. RAG 与检索

- `routers/retrieval.py`：RAG 主入口，文档上传、切分、嵌入、查询
- `retrieval/loaders/main.py`：文档解析器集合（PDF、Office、HTML、YouTube、Tika、Docling、MinerU、Mistral OCR、PaddleOCR 等）
- `retrieval/vector/main.py`：向量库抽象基类 `VectorDBBase`
- `retrieval/vector/`：ChromaDB、PGVector、Qdrant、Milvus、Elasticsearch、OpenSearch、Pinecone、S3Vector、Oracle 23ai 等实现
- `retrieval/web/`：20+ 网络搜索 provider
- `retrieval/utils.py`：embedding、reranking、hybrid search 封装

### 5. 插件与扩展

- **Functions** (`functions.py`, `models/functions.py`)：可写 `pipe`、`filter`、`action`、`stream` 四种钩子，支持 `Valves` 配置与 `UserValves`
- **Tools** (`utils/tools.py`, `tools/builtin.py`)：暴露给模型 function calling 的能力；内置 40+ 工具（搜索、记忆、日历、文件、知识库、图像生成、代码执行等）
- **Skills** (`routers/skills.py`, `models/skills.py`)：可复用的 Agent 技能定义，可被模型引用
- **Pipelines** (`routers/pipelines.py`)：Open WebUI Pipelines 协议， inlet/outlet filter 链
- **MCP** (`utils/mcp/client.py`)：MCP 客户端，支持 streamable HTTP + OAuth，用于连接 MCP 工具服务器

插件加载方式：`utils/plugin.py` 用 `types.ModuleType` + `exec()` 热加载数据库里的 Python 代码，并支持 frontmatter `requirements:` 自动 `pip install`。**这是把服务器 root 交给管理员的明确设计**。

### 6. 工具调用与 Agent 能力

`utils/tools.py` 核心职责：
- 把内置 Tool 函数或外部 MCP/OpenAPI server 转成 OpenAI function spec
- 处理 auth（bearer / session / system_oauth / oauth_2.1）
- 通过 `get_async_tool_function_and_apply_extra_params` 注入 `__user__`、`__event_emitter__` 等上下文

内置工具示例：`search_web`、`query_knowledge_bases`、`add_memory`、`create_automation`、`execute_code`、`generate_image`、`edit_image`、`fetch_url` 等。

### 7. 实时协作

`socket/main.py`：
- 基于 `python-socketio` + `pycrdt` 的 Ydoc 协同
- 可选 Redis 作为 backend 实现多实例 WebSocket
- 会话池 `SESSION_POOL`、使用池 `USAGE_POOL`、模型在线状态
- 支持频道、笔记的实时同步

### 8. 认证与安全

`utils/auth.py`：
- JWT（HS256）+ bcrypt/argon2 密码
- OAuth 2.0 / OIDC 登录，`utils/oauth.py` 支持角色/群组映射
- API Key、`WEBUI_AUTH_TRUSTED_EMAIL_HEADER`、SCIM 2.0

`utils/access_control/__init__.py`：
- 基于 `user_group` + `access_grant` 的细粒度权限
- 资源类型覆盖 model、tool、skill、knowledge、channel、note 等

`utils/audit.py`：ASGI 审计中间件，记录请求/响应（可配置级别）。

`utils/rate_limit.py`：Redis 滚动窗口限流 + 内存 fallback。

### 9. 任务与自动化

- `tasks.py`：全局 asyncio task 注册表，Redis pub/sub 实现分布式停止
- `utils/automations.py`：RRULE 解析与执行
- `routers/automations.py`：自动化 CRUD、权限、限制

### 10. 可观测性

`utils/telemetry/`：OpenTelemetry traces/metrics/logs 初始化，支持 OTLP gRPC/HTTP + basic auth。

## 技术栈

| 层 | 技术 |
|---|---|
| 后端 | Python 3.11、FastAPI 0.136、Pydantic 2、SQLAlchemy 2 async、Alembic |
| 前端 | SvelteKit 2、Svelte 5、Vite 5、Tailwind CSS 4、TipTap、Socket.IO client |
| 数据库 | SQLite（默认）/ PostgreSQL |
| 缓存/实时 | Redis（可选） |
| 模型协议 | OpenAI API、Ollama API |
| 向量 | ChromaDB、PGVector、Qdrant、Milvus、Elasticsearch、OpenSearch、Pinecone、S3Vector、Oracle 23ai |
| 文档解析 | LangChain loaders、Tika、Docling、MinerU、Mistral OCR、PaddleOCR、pypdf、unstructured |
| 工具协议 | MCP、MCPO、OpenAPI |
| 部署 | pip/uv、Docker/Docker Compose、Kubernetes（kubectl/kustomize/helm） |

## 代码规模（v0.10.2）

- 后端 Python 文件：~235 个（`backend/open_webui` 下约 111 个模块）
- 后端路由器总行数：~30,000 行
- 前端 TS/Svelte 文件：~666 个
- 前端源码文件总数：~738 个
- Alembic 迁移：48 个版本

## 生态项目

- **Open Terminal**：自托管计算环境，让 AI 在聊天里写代码、运行、调试
- **Terminals Enterprise**：每用户隔离容器，Docker/K8s 生命周期管理
- **cptr**：移动优先的计算机/编码 Agent，可连接 Open WebUI 作为模型
- **oikb**：45+ 数据源持续同步知识库
- **Native Desktop App**：macOS/Windows/Linux 原生应用，内置 Spotlight 聊天栏与 llama.cpp 本地推理

## 安全模型要点

Open WebUI 明确把自身定位为**自托管、单租户、管理员可信**的系统：

1. **Tools/Functions 等于服务器 root**：创建 Tools 的权限默认关闭，文档明确说「给某人 Tools 权限等于给 shell 访问」
2. **管理员行为不在漏洞范围**：添加恶意外部服务器、粘贴不可信代码被定义为管理员职责
3. **默认配置测试**：漏洞报告需在默认配置下复现
4. **透明安全流程**：通过 GitHub Security Advisories 处理，接受后公开 advisory

## 与相关项目的关系

| 项目 | 关系 |
|---|---|
| [[ollama]] | 本地模型运行时首选伙伴，Open WebUI 原生支持 |
| [[lobechat-architecture]] | 功能类似的开源 Chat UI 竞品，LobeChat 更偏前端组件生态 |
| [[dify]] | 低代码 LLMOps 平台，Open WebUI 更偏「聊天中枢」而非可视化工作流 |
| [[flowise]] | 低代码 LLM 应用构建器，Open WebUI 不主打节点编排 |
| [[firecrawl]] / [[browser-use]] | Open WebUI 可把它们作为 RAG/搜索/工具接入 |
| [[mcp-protocol]] | Open WebUI 通过 MCP client 连接外部工具服务器 |
| [[a2a-protocol]] | 目前 Open WebUI 主要用 OpenAI/MCP，A2A 非原生 |
| [[langchain]] | RAG 文档解析与切分大量复用 LangChain 生态 |

## 关键设计洞察

1. **「自托管优先」不是功能，是架构假设**：所有设计围绕离线、单租户、管理员可信展开，插件热加载、function calling、代码执行都是在此假设下才合理。
2. **数据库即配置中心**：大量功能通过 `Config` 表 + 环境变量双轨驱动，避免每次改配置都重启。
3. **模型统一层是核心抽象**：`utils/models.py` 把 Ollama、OpenAI、Function Pipes、Arena 统一成同样的模型对象，让前端和聊天调度无感知切换。
4. **插件=信任边界内的高自由度**：Functions/Tools 用 `exec()` 热加载，本质是把后端变成可扩展运行时，但也要求管理员严格隔离。
5. **RAG 走「全链路可替换」路线**：从文档解析、向量库、重排序到搜索源，每个环节都提供多种可插拔实现。
6. **实时协作是差异化**：频道 + 笔记 + 日历 + Ydoc 让 Open WebUI 从「个人聊天工具」扩展到「团队 AI workspace」。

## 适用场景

- 个人本地 AI 聊天客户端（配合 Ollama）
- 团队/企业内部 AI 门户（多模型、RBAC、知识库、审计）
- 需要完全离线/私有部署的合规场景
- 想在一个界面里同时管理聊天、Agent、RAG、工具、自动化的组织

## 局限与注意事项

- **资源占用不低**：默认包含 embedding、reranking、TTS/STT、Whisper 等本地模型
- **插件安全风险**：Tools/Functions 可执行任意代码，必须严格限制创建权限
- **单仓库前后端耦合**：大型定制可能需同时改 Python 和 Svelte
- **配置项极多**：大量开关分散在环境变量和 UI 设置中，初次部署需要仔细阅读文档
- **版本迭代快**：CHANGELOG 很长，升级前需确认迁移和破坏性变更

## 相关页面

- [[ollama]]
- [[lobechat-architecture]]
- [[dify]]
- [[flowise]]
- [[mcp-protocol]]
- [[a2a-protocol]]
- [[langchain]]
- [[firecrawl]]
- [[browser-use]]
- [[ai-workflow-landscape]]
- [[ai-agent-ecosystem]]
