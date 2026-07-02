---
title: LangChain / LangGraph
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [llm, agent, workflow, framework, python, javascript]
sources:
  - https://github.com/langchain-ai/langchain
  - https://github.com/langchain-ai/langgraph
confidence: 0.9
---

# LangChain / LangGraph

> The agent engineering platform — 构建 Agent 和 LLM 应用的框架，帮助开发者将可互操作组件与第三方集成链接在一起，简化 AI 应用开发。

---

## 一、项目定位

LangChain 由 Harrison Chase 于 2022 年 10 月创建，是当前最主流的 LLM 应用开发框架。2023 年成立 LangChain 公司进行商业化运营。

核心定位演进：
- **v0.1** — Chain + Agent + Tool + Memory 的链式调用框架
- **v0.2** — 模块化重构，LangChain Core / Community / Partner 独立包
- **v0.3** — 与 LangGraph 深度集成，Agent 优先
- **2025** — 定位升级为 "Agent Engineering Platform"，推出 Deep Agents

生态全景：
- **LangChain** — 核心框架（Python + JS/TS 双语言）
- **LangGraph** — 低级 Agent 编排框架（有状态图工作流）
- **Deep Agents** — 高层 Agent 包（内置规划、子 Agent、文件系统）
- **LangSmith** — 开发调试部署平台（商业）
- **LangServe** — 部署为 REST API
- **LangGraph Cloud** — 托管式 Agent 运行时（商业）

| 指标 | 数据 |
|------|------|
| GitHub Stars | 90k+ |
| 许可证 | MIT |
| 语言 | Python + TypeScript |
| 创建者 | Harrison Chase |
| 公司 | LangChain, Inc. |

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                   应用层                              │
│   Deep Agents（高层） / 自定义 Agent                  │
├─────────────────────────────────────────────────────┤
│               LangGraph（编排层）                      │
│   Stateful Graph · 条件分支 · 循环 · 并行 · 持久化     │
├─────────────────────────────────────────────────────┤
│              LangChain Core（基础层）                   │
│   Chat Models · Embeddings · Vector Stores · Tools   │
│   Output Parsers · Retrievers · Document Loaders     │
├─────────────────────────────────────────────────────┤
│              Integrations（集成层）                     │
│   700+ 组件：OpenAI · Anthropic · Google · AWS · ...  │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 核心框架 | `langchain-core` | 基础抽象：Runnable、ChatModel、Embeddings 等 |
| 社区集成 | `langchain-community` | 第三方集成（无重依赖） |
| Partner 包 | `langchain-openai` 等 | 各供应商独立包，可独立安装 |
| 编排引擎 | `langgraph` | 有状态图工作流，Pregel 模型 |
| 高层封装 | `langchain-deep-agents` | 内置规划、子 Agent、文件系统 |
| 可观测性 | LangSmith | Trace、评估、Prompt 管理 |

## 三、核心架构

### 3.1 LangChain 核心抽象

```
langchain/
  libs/
    core/              — 基础抽象层
      langchain_core/
        language_models/   — BaseLanguageModel
        chat_models/       — BaseChatModel → init_chat_model()
        embeddings/        — BaseEmbeddings
        vectorstores/      — BaseVectorStore
        tools/             — BaseTool, tool 装饰器
        output_parsers/    — OutputParser 系列
        retrievers/        — BaseRetriever
        runnables/         — Runnable 接口（LCEL 基础）
        messages/          — HumanMessage, AIMessage, SystemMessage
        prompts/           — ChatPromptTemplate, PromptTemplate
        callbacks/         — CallbackHandler 体系
        documents/         — Document 抽象
    
    langchain/          — 主包（编排逻辑）
      chains/             — LLMChain, SequentialChain, RouterChain
      agents/             — AgentExecutor, create_react_agent
      memory/             — ConversationBufferMemory 等
      output_parsers/     — PydanticOutputParser 等
    
    community/          — 社区集成
    partners/           — 各供应商独立包
      langchain-openai/
      langchain-anthropic/
      langchain-google/
      ...
```

### 3.2 LangChain Expression Language (LCEL)

LCEL 是 LangChain 的声明式组合语法，基于 `Runnable` 接口：

```python
chain = prompt | model | output_parser

# 等价于
chain = prompt.invoke(question) | model.invoke() | output_parser.invoke()
```

核心方法：
- `invoke()` — 单次调用
- `batch()` — 批量调用
- `stream()` — 流式输出
- `astream_events()` — 异步事件流

### 3.3 LangGraph 架构

LangGraph 是独立包，基于 Pregel 模型（Google MapReduce 论文同源）构建有状态图：

```
┌──────────────────────────────────────┐
│            StateGraph                │
│                                      │
│  ┌──────┐   ┌──────┐   ┌──────┐    │
│  │ Node │──>│ Node │──>│ Node │    │
│  │  A   │   │  B   │   │  C   │    │
│  └──────┘   └──┬───┘   └──────┘    │
│                │                     │
│           ┌────┴────┐               │
│           │ Conditional│             │
│           │   Edge    │              │
│           └────┬────┘               │
│          ┌─────┴─────┐              │
│          │           │               │
│     ┌────▼───┐ ┌────▼───┐          │
│     │ Node D │ │ Node E │          │
│     └────┬───┘ └────────┘          │
│          │                          │
│     ┌────▼───┐                     │
│     │ Loop   │ ← 循环边             │
│     │ back   │                     │
│     └────────┘                     │
└──────────────────────────────────────┘
```

核心概念：
- **StateGraph** — 状态图，节点函数接收并返回 State
- **Node** — 节点函数，操作 State
- **Edge** — 普通边（固定转移）和条件边（运行时决定）
- **State** — TypedDict 或 Pydantic Model，自动合并
- **Checkpointer** — 状态持久化（MemorySaver、SqliteSaver、PostgresSaver）
- **Subgraph** — 嵌套图，支持 Multi-Agent

```python
from langgraph.graph import StateGraph, START, END

graph = StateGraph(State)
graph.add_node("researcher", research_node)
graph.add_node("writer", writer_node)
graph.add_conditional_edges("researcher", route, {"writer": "writer", "researcher": "researcher"})
graph.add_edge(START, "researcher")
graph.add_edge("writer", END)

app = graph.compile(checkpointer=memory)
```

### 3.4 Deep Agents（2025 新增）

高层 Agent 封装，内置常见模式：

- **规划能力** — 自动分解复杂任务为子步骤
- **子 Agent** — 动态创建子 Agent 执行子任务
- **文件系统** — 读写文件、管理工作目录
- **工具调用** — 内置常用工具集

## 四、关键特性

### 4.1 700+ 集成

覆盖主流 LLM 供应商、向量数据库、工具、数据加载器：
- LLM：OpenAI、Anthropic、Google、AWS Bedrock、Azure、Mistral、Cohere
- 向量库：Pinecone、Weaviate、Chroma、Qdrant、FAISS、pgvector
- 工具：SerpAPI、Wikipedia、Calculator、Python REPL、SQL Database
- 文档加载：PDF、HTML、Markdown、CSV、Notion、Google Drive

### 4.2 Agent 模式

- **ReAct Agent** — 推理+行动循环
- **OpenAI Tools Agent** — 原生 Function Calling
- **Structured Chat Agent** — 多工具结构化输出
- **Self-Ask Agent** — 自提问搜索
- **LangGraph Agent** — 完全自定义图结构

### 4.3 RAG 管道

```python
# 典型 RAG 链
chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | model
    | StrOutputParser()
)
```

支持高级 RAG 模式：Parent Document Retriever、Multi-Query、Self-Query、Contextual Compression

### 4.4 可观测性（LangSmith）

- Trace 可视化 — 每步输入/输出/Latency/Token
- 评估框架 — 自动化评估 Agent 输出质量
- Prompt 管理 — 版本控制、A/B 测试
- 数据集 — 标注数据集用于评估

## 五、关键设计决策

1. **Runnable 接口统一** — 所有组件实现 `Runnable`，支持 `|` 管道组合，LCEL 是核心抽象而非语法糖
2. **Partner 独立包** — 每个供应商独立 pip 包，避免单一巨大依赖
3. **LangGraph 独立演进** — 图编排是独立包，不与 LangChain 主包耦合
4. **Checkpointer 抽象** — 状态持久化可切换（内存/SQLite/Postgres），支持人机协作
5. **Python + JS 双轨** — 两个团队独立维护，API 设计尽量对齐但不强求一致

## 六、开发命令速查

```bash
# 安装
pip install langchain
pip install langgraph
pip install langchain-openai

# 开发（从源码）
git clone https://github.com/langchain-ai/langchain.git
cd langchain
pip install -e libs/core
pip install -e libs/langchain
pip install -e libs/community

# 测试
make test

# LangGraph
pip install langgraph
pip install langgraph-checkpoint-sqlite
```

## 七、与竞品对比

| 维度 | LangChain | [[llama-index]] | [[crew-ai]] | [[auto-gen]] |
|------|-----------|-----------------|-------------|--------------|
| 定位 | 通用 LLM 框架 | 数据+RAG | 多 Agent 协作 | 多 Agent 对话 |
| 复杂度 | 中-高 | 中 | 低-中 | 中 |
| 灵活性 | 高（LCEL+LangGraph） | 中 | 低（高层抽象） | 中 |
| 生态 | 700+ 集成 | 160+ 数据源 | LangChain 兼容 | 微软生态 |
| 学习曲线 | 陡峭 | 中等 | 平缓 | 中等 |

---

## 相关

- [[llama-index]] — 数据 Agent 和工作流框架（互补关系）
- [[crew-ai]] — 多 Agent 协作框架（LangChain 兼容）
- [[auto-gen]] — 微软 Multi-Agent 框架
- [[dify]] — 可视化 LLMOps 平台（底层可用 LangChain）
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
