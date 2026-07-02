---
title: Dify
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [llmops, workflow, platform, python, typescript, low-code]
sources:
  - https://github.com/langgenius/dify
confidence: 0.9
---

# Dify

> 开源 LLMOps 平台 — 可视化工作流编排 + RAG Pipeline + Agent 模式 + 100+ 模型兼容，AI 应用的全栈开发平台。

---

## 一、项目定位

Dify 由国内团队 LangGenius 开发，定位为 AI 应用的全栈开发平台。核心特点是将 LLM 应用开发从代码级抽象提升到可视化编排级，同时保留代码级灵活性。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 50k+ |
| 许可证 | Apache 2.0（附加条款） |
| 语言 | Python + TypeScript |
| 创建者 | LangGenius 团队 |
| 官网 | https://dify.ai |

核心能力：
1. **可视化 Workflow 编排** — 拖拽式构建 AI 工作流
2. **RAG Pipeline** — 内置文档解析、Embedding、向量检索全流程
3. **Agent 模式** — ReAct、Function Call 等策略
4. **100+ 模型兼容** — OpenAI、Claude、Llama、通义千问等
5. **私有化部署** — Docker 一键部署

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                  前端（Next.js）                       │
│   Workflow Editor · App Builder · Knowledge Base     │
│   Agent Config · Explore Market                      │
├─────────────────────────────────────────────────────┤
│                  API 层（Flask）                       │
│   REST API · SSE Streaming · WebSocket               │
│   Auth · Tenant · Billing                            │
├─────────────────────────────────────────────────────┤
│                  核心引擎                              │
│   Workflow Engine · RAG Engine · Agent Engine         │
│   Model Provider · Tool Provider · Memory            │
├─────────────────────────────────────────────────────┤
│                  存储层                                │
│   PostgreSQL · Redis · Weaviate/Qdrant/Chroma        │
│   S3/OSS · Celery                                    │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | Next.js + React + TailwindCSS | App Router，TypeScript |
| 后端 API | Flask + SQLAlchemy | REST + SSE |
| 工作流引擎 | Python 自研 | DAG 执行引擎 |
| 向量数据库 | Weaviate / Qdrant / Chroma / Milvus / Pgvector | 可选 |
| 关系数据库 | PostgreSQL | 主存储 |
| 缓存 | Redis | 会话、限流 |
| 任务队列 | Celery + Redis | 异步任务 |
| 对象存储 | S3 / Azure Blob / 阿里 OSS | 文件存储 |
| 部署 | Docker Compose / K8s Helm | 一键部署 |

## 三、核心架构

### 3.1 后端目录结构

```
api/
  app.py                    — Flask 入口
  configs/                  — 配置
  controllers/              — API 控制器
    console/                  — 控制台 API
      app/                     — 应用管理
      workflow/                — 工作流 API
      knowledge/              — 知识库 API
      agent/                  — Agent API
    service/                  — 服务端 API
  models/                   — SQLAlchemy 模型
    model_provider.py         — 模型供应商
    workflow.py               — 工作流
    knowledge.py              — 知识库
    dataset.py                — 数据集
    app.py                    — 应用
  services/                  — 业务逻辑
    workflow_engine/          — 工作流引擎
      runner.py                — 执行器
      nodes/                   — 节点实现
        llm_node.py
        tool_node.py
        code_node.py
        if_else_node.py
        iteration_node.py
        variable_assigner_node.py
        ...
    feature_service/          — 功能服务
    model_provider_service/   — 模型供应商
    knowledge_service/        — 知识库
    app_service/              — 应用
  core/                     — 核心抽象
    model_runtime/             — 模型运行时
      model_providers/           — 100+ 模型供应商
    tools/                     — 工具系统
      provider/                  — 工具供应商
    workflow/                  — 工作流核心
      nodes/                     — 节点类型
      graph_engine/              — 图执行引擎
    agent/                     — Agent 引擎
    rag/                       — RAG 引擎
      retrieval/                 — 检索
      splitter/                  — 分片
      embedding/                 — 向量化
```

### 3.2 前端目录结构

```
web/
  app/                      — Next.js App Router
    (commonLayout)/           — 通用布局
      apps/                    — 应用管理页
      workflows/               — 工作流编辑器
      knowledge/              — 知识库页
      explore/                 — 探索市场
    install/                  — 安装引导
  components/               — React 组件
    workflow/                 — 工作流编辑器组件
      nodes/                    — 节点组件
      panel/                    — 配置面板
    base/                     — 基础组件
    app/                      — 应用组件
  hooks/                    — React Hooks
  i18n/                     — 国际化
  context/                  — React Context
  service/                  — API 调用
```

### 3.3 工作流引擎

Dify 的核心是自研的 DAG 工作流引擎：

```
┌──────────────────────────────────────────────┐
│              Workflow Graph                    │
│                                              │
│  ┌────────┐    ┌────────┐    ┌────────┐     │
│  │ Start  │───>│  LLM   │───>│  Tool  │     │
│  │ Node   │    │  Node  │    │  Node  │     │
│  └────────┘    └───┬────┘    └───┬────┘     │
│                    │              │           │
│               ┌────▼────┐   ┌────▼────┐     │
│               │If-Else  │   │ Code    │     │
│               │ Node    │   │ Node    │     │
│               └──┬───┬──┘   └─────────┘     │
│                  │   │                       │
│           ┌──────┘   └──────┐               │
│      ┌────▼───┐      ┌─────▼──┐             │
│      │ LLM B  │      │  End   │             │
│      └────────┘      │  Node  │             │
│                      └────────┘             │
└──────────────────────────────────────────────┘
```

节点类型：
- **LLM Node** — 调用 LLM，支持流式输出
- **Tool Node** — 调用内置/自定义工具
- **Code Node** — 执行 Python/JavaScript 代码
- **If-Else Node** — 条件分支
- **Iteration Node** — 循环迭代
- **Variable Assigner** — 变量聚合
- **HTTP Request** — 外部 API 调用
- **Knowledge Retrieval** — RAG 检索
- **Question Classifier** — 意图分类
- **Template Transform** — 模板转换
- **Parameter Extractor** — 参数提取

### 3.4 RAG Pipeline

```
文档上传 → 格式解析 → 文本分片 → Embedding → 向量存储
                                                    ↓
用户查询 → Query 改写 → 向量检索 → 重排序 → 上下文注入 → LLM 生成
```

支持的文档格式：PDF、TXT、Markdown、DOCX、HTML、XLSX、CSV、PPTX 等

检索模式：
- 向量检索（语义相似度）
- 全文检索（关键词匹配）
- 混合检索（向量 + 全文）

重排序：Cohere Rerank、bge-reranker 等

### 3.5 Agent 模式

- **ReAct** — 推理+行动循环
- **Function Calling** — 原生工具调用
- **Chatflow** — 对话流（带工作流）

### 3.6 模型供应商（100+）

| 类别 | 供应商 |
|------|--------|
| 国际 | OpenAI、Anthropic、Google、AWS Bedrock、Azure、Mistral、Cohere、DeepSeek |
| 国产 | 通义千问、文心一言、智谱、MiniMax、百川、讯飞、月之暗面 |
| 本地 | Ollama、Xinference、LocalAI、OpenLLM |
| 代理 | OpenAI-API-Compatible（兼容任何 OpenAI 格式 API） |

## 四、关键特性

### 4.1 多租户

- Workspace 隔离
- 成员角色管理（Owner / Admin / Editor / Viewer）
- API Key 管理
- 用量统计和限流

### 4.2 应用类型

| 类型 | 说明 |
|------|------|
| Chat App | 对话应用 |
| Completion App | 文本生成应用 |
| Workflow App | 工作流应用 |
| Agent App | Agent 应用 |

### 4.3 知识库管理

- 多格式文档导入
- 自动分片策略（自动/自定义）
- 多种 Embedding 模型
- 向量数据库可选
- 增量更新

### 4.4 工具市场

- 内置工具：Google Search、Wikipedia、Weather、Calculator 等
- 自定义工具：OpenAPI Schema 定义
- API 工具：HTTP 请求封装

### 4.5 部署方式

```bash
# Docker Compose（推荐）
git clone https://github.com/langgenius/dify.git
cd dify/docker
docker compose up -d

# Helm（K8s）
helm install dify ./helm
```

## 五、关键设计决策

1. **可视化优先** — 工作流编辑器是核心入口，代码是补充
2. **自研工作流引擎** — 不依赖 Airflow/Prefect，轻量 DAG 引擎
3. **模型无关** — 100+ 供应商统一抽象，切换零成本
4. **多租户原生** — 从第一天就支持 SaaS 和私有化双模式
5. **前后端分离** — Next.js 前端 + Flask 后端，独立部署

## 六、开发命令速查

```bash
# Docker 部署
cd docker && docker compose up -d

# 本地开发 - 后端
cd api
flask run --host 0.0.0.0 --port 5001
celery -A app.celery worker

# 本地开发 - 前端
cd web
pnpm install
pnpm dev

# 环境变量
cp .env.example .env
```

## 七、与竞品对比

| 维度 | Dify | [[fast-gpt]] | [[flowise]] | [[langflow]] |
|------|------|-------------|-------------|--------------|
| 定位 | 全栈 AI 平台 | 知识库问答 | 轻量原型 | 开发者工具 |
| 工作流 | 可视化 DAG | 可视化 | 拖拽节点 | 拖拽+导出代码 |
| RAG | 内置完整 | 内置完整 | 需配置 | 需配置 |
| 模型数 | 100+ | 10+ | LangChain 生态 | LangChain 生态 |
| 多租户 | 原生 | 原生 | 无 | 无 |
| 部署 | Docker/K8s | Docker | Docker | Docker |
| 代码导出 | 无 | 无 | 无 | Python/JSON |

---

## 相关

- [[fast-gpt]] — 国产知识库问答平台
- [[flowise]] — 低代码 LLM 应用构建器
- [[langflow]] — 可视化 LangChain 工作流编辑器
- [[n8n]] — 开源自动化工作流工具
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
