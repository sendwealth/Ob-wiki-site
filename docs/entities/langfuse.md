---
title: Langfuse
created: 2026-06-03
updated: 2026-06-03
type: entity
tags: [llm, observability, tracing, evaluation, prompt-management, open-source, ycombinator]
sources:
  - https://github.com/langfuse/langfuse
  - https://langfuse.com/docs
confidence: 0.9
---

# Langfuse

> 开源 LLM 工程平台 — Tracing 可观测性 + Prompt 管理 + 评估 + 数据集，LLM 应用从 PoC 到生产的一站式工程平台。YC W23。

---

## 一、项目定位

Langfuse 是开源 LLM 工程平台，帮助团队协作开发、监控、评估和调试 AI 应用。2023 年入选 Y Combinator Winter 批次。与 [[langchain]] 的 LangSmith 是直接竞品——Langfuse 开源自托管，LangSmith 是 SaaS 闭源。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 10k+ |
| 许可证 | MIT（核心）/ EE License（企业版） |
| 语言 | TypeScript (Next.js) + Python SDK + JS SDK |
| 创建者 | Marc Klingen, Max Deichmann |
| 公司 | Langfuse GmbH（YC W23） |
| 审网 | https://langfuse.com |

核心定位——LLM 应用的工程平台，不是编排框架：
1. **Tracing** — 追踪 LLM 调用链，调试复杂 Agent 逻辑
2. **Prompt Management** — 版本控制、协作迭代、零延迟部署
3. **Evaluation** — LLM-as-a-judge、代码评估器、人工标注、数据集实验
4. **Datasets** — 系统化测试用例管理

关键区别：Langfuse **不编排工作流**，它**观测和评估**工作流。你用 [[langchain]] / [[crew-ai]] / [[auto-gen]] 编排 Agent，用 Langfuse 追踪和评估 Agent 的执行。

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│              Langfuse Web UI（Next.js）                │
│   Traces · Sessions · Prompts · Evaluations · Datasets│
├─────────────────────────────────────────────────────┤
│              Langfuse Worker                         │
│   异步事件处理 · 评分计算 · LLM-as-a-judge 执行        │
├─────────────────────────────────────────────────────┤
│              Langfuse API                            │
│   REST + Streaming · Ingestion · Query               │
├─────────────────────────────────────────────────────┤
│              存储层                                   │
│   PostgreSQL（事务） · ClickHouse（OLAP/Trace）        │
│   Redis（缓存/队列） · S3/Blob（事件/多模态）          │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| Web 应用 | Next.js + TypeScript | UI + API |
| Worker | TypeScript | 异步事件处理 |
| 事务数据库 | PostgreSQL | 元数据、用户、项目 |
| OLAP 数据库 | ClickHouse | Trace、Observation、Score 存储 |
| 缓存/队列 | Redis / Valkey | 队列操作、缓存 |
| 对象存储 | S3 / Azure Blob / GCS | 事件持久化、多模态输入、大导出 |
| SDK | Python + JS/TS | 原生 SDK |

**ClickHouse 是关键差异化**——Trace 数据是高吞吐写入 + 分析查询场景，ClickHouse 的列式存储天然适合。PostgreSQL 处理事务性数据（用户、项目、Prompt 版本）。

## 三、核心架构

### 3.1 目录结构

```
langfuse/
  packages/
    core/                  — 共享核心逻辑
      src/
        server/
          services/          — 业务服务
          models/            — 数据模型
          repositories/      — 数据访问
        shared/
          constants/
          types/
    web/                   — Next.js Web 应用
      src/
        app/                — App Router 页面
          traces/             — Trace 页面
          sessions/           — Session 页面
          prompts/            — Prompt 管理页
          datasets/           — 数据集页
          evaluations/        — 评估页
        components/         — React 组件
        features/           — 功能模块
    worker/                — Worker 进程
      src/
        processors/         — 事件处理器
        evaluators/         — 评估执行器
  sdks/
    python/                — Python SDK
      langfuse/
        api/                 — API 客户端
        callback/            — LangChain/LlamaIndex 回调
        decorators/          — @observe 装饰器
        evaluation/          — 评估工具
    js/                    — JS/TS SDK
      src/
        api/
        tracing/
        evaluation/
```

### 3.2 Trace 数据模型

Langfuse 的核心数据模型围绕 Trace 构建：

```
┌──────────────────────────────────────────────────┐
│                   Trace                           │
│   id · name · userId · sessionId · metadata       │
│   input · output · tags · timestamp               │
│                                                  │
│   ┌─────────────────────────────────────────┐    │
│   │           Span（Observation）             │    │
│   │   id · name · type · startTime · endTime │    │
│   │   input · output · model · usage          │    │
│   │                                          │    │
│   │   ┌─────────────────────────────────┐    │    │
│   │   │     Span（子 Observation）        │    │    │
│   │   │   如：LLM 调用、工具调用、检索    │    │    │
│   │   └─────────────────────────────────┘    │    │
│   └─────────────────────────────────────────┘    │
│                                                  │
│   ┌─────────────────────────────────────────┐    │
│   │           Score（评分）                   │    │
│   │   name · value · source · comment        │    │
│   └─────────────────────────────────────────┘    │
└──────────────────────────────────────────────────┘
```

核心概念：
- **Trace** — 一次完整请求的追踪（如一次 Agent 对话）
- **Span / Observation** — Trace 内的步骤（LLM 调用、工具调用、检索等）
- **Score** — 对 Trace 或 Span 的评分（人工/自动/LLM-as-a-judge）
- **Session** — 多轮对话的聚合（多个 Trace 组成一个 Session）
- **Event** — 不可变事件记录（Ingestion → ClickHouse）

### 3.3 SDK 集成方式

**1. 原生 SDK（手动埋点）**：
```python
from langfuse import Langfuse

langfuse = Langfuse()

# 创建 Trace
trace = langfuse.trace(
    name="my-agent",
    user_id="user-123",
    session_id="session-456",
    metadata={"env": "production"},
)

# 创建 Span
generation = trace.generation(
    name="llm-call",
    model="gpt-4o",
    input={"prompt": "Hello"},
)

# 记录输出
generation.end(
    output={"response": "Hi there!"},
    usage={"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
)
```

**2. @observe 装饰器（Python SDK）**：
```python
from langfuse.decorators import observe

@observe()
def my_agent(query: str):
    # 自动创建 Trace，函数内 LLM 调用自动追踪
    docs = retriever(query)
    answer = llm(query, docs)
    return answer
```

**3. LangChain 回调（自动埋点）**：
```python
from langfuse.callback import CallbackHandler

langfuse_handler = CallbackHandler()

# 传给 LangChain Agent
agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
)
result = agent.run("Hello", callbacks=[langfuse_handler])
```

**4. OpenAI SDK 替换（零代码改动）**：
```python
# 替换 import 即可
from langfuse.openai import OpenAI  # 替代 from openai import OpenAI

client = OpenAI()
response = client.chat.completions.create(
    model="gpt-4o",
    messages=[{"role": "user", "content": "Hello"}],
)
# 自动追踪到 Langfuse
```

### 3.4 50+ 集成

| 集成 | 方式 | 语言 |
|------|------|------|
| LangChain | Callback Handler | Python + JS/TS |
| LlamaIndex | Callback Handler | Python |
| OpenAI SDK | Drop-in Replacement | Python + JS/TS |
| LiteLLM | Proxy 集成 | Python + JS/TS |
| Haystack | Content Tracing | Python |
| Vercel AI SDK | 原生集成 | JS/TS |
| Mastra | 原生集成 | JS/TS |
| OpenTelemetry | OTLP Export | 任意语言 |
| API | REST 直接调用 | 任意语言 |

## 四、关键特性

### 4.1 Tracing 可观测性

- **Trace 详情** — 每步输入/输出/Latency/Token/Model
- **Session 追踪** — 多轮对话聚合视图
- **Timeline 视图** — Latency 瓶颈可视化
- **Agent Graph** — Agent 执行图可视化
- **User 追踪** — 按 userId 聚合成本和使用量
- **Dashboard** — 自定义指标面板
- **多模态** — 支持图片等非文本 Trace

### 4.2 Prompt 管理

```python
from langfuse import Langfuse

langfuse = Langfuse()

# 从 Langfuse 获取 Prompt（带缓存）
prompt = langfuse.get_prompt("my-prompt")

# 编译为 LangChain ChatPromptTemplate
chat_prompt = prompt.get_langchain_prompt()

# 或直接获取
compiled = prompt.compile(variable1="value1", variable2="value2")
```

Prompt 管理特性：
- **版本控制** — 每次修改自动创建新版本
- **标签部署** — production / staging / canary 标签，零代码切换
- **Playground** — 交互式测试 Prompt
- **Trace 关联** — Prompt 版本与 Trace 自动关联，追踪效果
- **服务端缓存** — 零延迟 Prompt 获取
- **实验** — 在数据集上对比不同 Prompt 版本

### 4.3 评估系统

Langfuse 的评估系统是其最强大的功能，支持 5 种评估方法：

| 方法 | 说明 | 适用场景 |
|------|------|---------|
| LLM-as-a-judge | 用 LLM 评估输出质量 | 自动化质量评估 |
| Code Evaluator | Python 代码评估 | 确定性检查（格式、长度等） |
| Human Annotation | 人工标注队列 | 高质量标注 |
| User Feedback | 用户反馈收集 | 生产环境实时反馈 |
| Custom Pipeline | 自定义评估管线 | 复杂评估逻辑 |

**LLM-as-a-judge**：
```python
from langfuse import Langfuse

langfuse = Langfuse()

# 对生产 Trace 自动运行评估
langfuse.score_trace(
    trace_id=trace.id,
    name="helpfulness",
    value=0.9,  # LLM 评估分数
    data_type="numeric",
)
```

**Annotation Queue**（人工标注）：
- 创建标注队列，分配给标注员
- 标注员在 UI 中查看 Trace 并打分
- 支持多标注员、一致性检查

**数据集 + 实验**：
```python
# 创建数据集
dataset = langfuse.create_dataset(name="qa-eval")

# 添加测试项
dataset.create_item(
    input={"question": "What is AI?"},
    expected_output="AI is...",
)

# 运行实验
from langfuse.decorators import observe

@observe()
def my_app(question):
    return llm(question)

# 对数据集运行实验
experiment = dataset.run(my_app)
```

### 4.4 Session 和 User 追踪

- **Session** — 多轮对话聚合，跨 Trace 追踪用户会话
- **User** — 按 userId 聚合成本、Token 用量、满意度
- **Metadata** — 自定义元数据附加到 Trace

### 4.5 OpenTelemetry 兼容

Langfuse 基于 OpenTelemetry 协议，意味着：
- 可与任何 OTLP 兼容的追踪系统集成
- 减少厂商锁定
- 可导出 Trace 到 Jaeger、Zipkin 等

## 五、关键设计决策

1. **ClickHouse for OLAP** — Trace 数据是高吞吐写入 + 分析查询，ClickHouse 列式存储天然适合，PostgreSQL 做事务
2. **不可变事件** — Ingestion 事件不可变，写入 ClickHouse 后只读，保证数据完整性
3. **异步 Worker** — 事件处理、评分计算异步执行，不阻塞 API 响应
4. **SDK 优先** — 原生 Python + JS SDK，而非仅依赖 OpenTelemetry
5. **Drop-in Replacement** — OpenAI SDK 替换方式，零代码改动即可追踪
6. **开源 + EE 双模式** — MIT 核心功能，EE License 企业功能（SSO、RBAC、审计日志）

## 六、部署方式

### 6.1 Langfuse Cloud（SaaS）

- 免费层：每月 50k Observation
- Pro：$0.005/Observation
- Team/Enterprise：自定义定价

### 6.2 自托管

**Docker Compose（本地/VM）**：
```bash
git clone --depth=1 https://github.com/langfuse/langfuse.git
cd langfuse
docker compose up
```

**Kubernetes Helm（生产推荐）**：
```bash
helm install langfuse langfuse/langfuse
```

**Terraform**：
- AWS（ECS + RDS + ClickHouse + S3）
- Azure（AKS + PostgreSQL + ClickHouse + Blob）
- GCP（GKE + Cloud SQL + ClickHouse + GCS）

### 6.3 架构要求

| 组件 | 用途 | 必需 |
|------|------|------|
| Langfuse Web | UI + API | 是 |
| Langfuse Worker | 异步处理 | 是 |
| PostgreSQL | 事务数据 | 是 |
| ClickHouse | Trace 存储 | 是 |
| Redis | 缓存/队列 | 是 |
| S3/Blob | 事件/多模态 | 推荐 |
| LLM API | LLM-as-a-judge | 评估功能需要 |

## 七、与竞品对比

| 维度 | Langfuse | LangSmith | [[mlflow]] Tracing | Arize Phoenix |
|------|----------|-----------|-------------------|---------------|
| 开源 | MIT | 闭源 | Apache 2.0 | MIT |
| 自托管 | 支持 | 不支持 | 支持 | 支持 |
| Trace 存储 | ClickHouse（OLAP） | 自有 | SQL Store | SQLite/ClickHouse |
| Prompt 管理 | 完整 | 完整 | 基础 | 无 |
| 评估 | 5 种方法 | 3 种方法 | LLM Evaluate | 基础 |
| 数据集+实验 | 原生 | 原生 | 无 | 无 |
| LangChain 集成 | Callback | 原生 | Fluent API | Callback |
| OpenAI 集成 | Drop-in | 原生 | 无 | 无 |
| OpenTelemetry | 原生 | 无 | 无 | 原生 |
| 定价 | 开源/Cloud | SaaS only | 开源 | 开源 |
| YC | W23 | LangChain 公司 | Databricks | Arize AI |

**Langfuse vs LangSmith** 是核心对比：

- Langfuse 优势：**开源自托管**、ClickHouse OLAP 性能、OpenTelemetry 兼容、不绑定 LangChain
- LangSmith 优势：**LangChain 深度集成**、更早进入市场、LangChain 公司官方支持

选 Langfuse 如果：需要自托管、数据合规要求、使用多种框架（不只 LangChain）、需要 OpenTelemetry 兼容。
选 LangSmith 如果：深度使用 LangChain 生态、不需要自托管、优先官方集成体验。

## 八、开发命令速查

```bash
# Python SDK
pip install langfuse

# JS/TS SDK
npm install langfuse

# 环境变量
export LANGFUSE_PUBLIC_KEY="pk-..."
export LANGFUSE_SECRET_KEY="sk-..."
export LANGFUSE_HOST="https://cloud.langfuse.com"  # 或自托管地址

# 自托管 - Docker Compose
git clone --depth=1 https://github.com/langfuse/langfuse.git
cd langfuse && docker compose up

# 自托管 - Kubernetes Helm
helm install langfuse langfuse/langfuse

# LangChain 集成
from langfuse.callback import CallbackHandler
handler = CallbackHandler()

# OpenAI 集成（零代码改动）
from langfuse.openai import OpenAI  # 替换 import

# 装饰器
from langfuse.decorators import observe
@observe()
def my_function(): ...
```

---

## 相关

- [[langchain]] — LLM 应用框架（Langfuse 主要集成目标）
- [[llama-index]] — 数据 Agent 框架（Langfuse 支持）
- [[mlflow]] — ML 生命周期管理（Tracing 竞品）
- [[dify]] — LLMOps 平台（可搭配 Langfuse 做可观测性）
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
- [[ai-workflow-deep-comparison]] — AI Workflow 深度对比分析
