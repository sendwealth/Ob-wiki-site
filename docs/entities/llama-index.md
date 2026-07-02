---
title: LlamaIndex
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [llm, rag, workflow, data, python, framework]
sources:
  - https://github.com/run-llama/llama_index
confidence: 0.9
---

# LlamaIndex

> LLM 与数据的桥梁 — 数据 Agent 和工作流框架，从 RAG 框架升级为完整 AI Workflow 平台。

---

## 一、项目定位

LlamaIndex 由 Jerry Liu 于 2022 年 11 月创建（原名 GPT Index），核心定位是 LLM 与外部数据的桥梁。2024 年推出 Workflow 引擎，从单纯 RAG 框架升级为完整 AI Workflow 平台。

定位演进：
- **v0.x (GPT Index)** — 索引结构连接 LLM 与数据
- **v0.8+ (LlamaIndex)** — RAG Pipeline + 数据连接器
- **v0.10+** — 引入 Workflow 引擎，Agent 优先
- **v0.11+** — Workflow DAG 模式，完整工作流平台

| 指标 | 数据 |
|------|------|
| GitHub Stars | 36k+ |
| 许可证 | MIT |
| 语言 | Python + TypeScript |
| 创建者 | Jerry Liu |
| 公司 | LlamaIndex, Inc. |

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                  应用层                               │
│   Chat Engine · Query Engine · Agent · Workflow      │
├─────────────────────────────────────────────────────┤
│               Workflow 引擎                           │
│   Step-based · DAG-based · 事件驱动 · 条件分支        │
├─────────────────────────────────────────────────────┤
│              LlamaIndex Core                         │
│   Index · Retriever · Synthesizer · Router           │
│   Prompt · Output Parser · Callbacks                 │
├─────────────────────────────────────────────────────┤
│              数据层                                   │
│   160+ Data Connectors · Node · Document             │
│   Embeddings · Vector Stores · Knowledge Graph       │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 核心框架 | `llama-index-core` | 基础抽象，零重依赖 |
| 集成包 | `llama-index-llms-openai` 等 | 各供应商独立包 |
| 数据连接器 | `llama-hub` → 内置 | 160+ 数据源连接器 |
| Workflow | `llama-index-core/workflow` | Step + DAG 工作流引擎 |
| TS 版本 | `llama-index-ts` | TypeScript 实现 |

## 三、核心架构

### 3.1 数据抽象

```
llama-index-core/
  schema/
    document.py       — Document（文本 + 元数据）
    node.py           — Node（文档分片，最小检索单元）
  indices/
    vector_store_index.py   — 向量索引
    tree_index.py           — 树索引（自底向上摘要）
    keyword_index.py        — 关键词索引
    knowledge_graph_index.py — 知识图谱索引
    property_graph_index.py  — 属性图索引
  retrievers/
    base.py           — BaseRetriever
    vector_index_retriever.py
    auto_merging_retriever.py
    recursive_retriever.py
  query/
    engine/           — QueryEngine（查询引擎）
    pipeline/         — QueryPipeline（查询管道）
  synthesize/
    response_synthesizer.py — 响应合成
  chat_engine/
    simple.py         — SimpleChatEngine
    condense.py       — CondensePlusContextChatEngine
    agent.py          — AgentChatEngine
```

### 3.2 数据连接器（160+）

覆盖主流数据源：

| 类别 | 连接器 |
|------|--------|
| 文件 | PDF、DOCX、PPTX、XLSX、CSV、Markdown、HTML |
| Web | Web Page、Sitemap、ReadTheDocs、Notion |
| 数据库 | SQL、MongoDB、ChromaDB、Pinecone |
| API | Google Drive、Slack、GitHub、Jira |
| 云存储 | S3、GCS、Azure Blob、Dropbox |

### 3.3 索引策略

```
┌─────────────────────────────────────────────┐
│              Index 类型                       │
├──────────────┬──────────────────────────────┤
│ Vector Store │ Embedding → 向量相似度检索     │
│              │ 适合：语义搜索                 │
├──────────────┼──────────────────────────────┤
│ Summary      │ LLM 摘要 → 全文摘要检索        │
│              │ 适合：文档级检索               │
├──────────────┼──────────────────────────────┤
│ Tree         │ 自底向上递归摘要树             │
│              │ 适合：从叶到根遍历             │
├──────────────┼──────────────────────────────┤
│ Keyword      │ 关键词倒排索引                 │
│              │ 适合：精确匹配                 │
├──────────────┼──────────────────────────────┤
│ Knowledge    │ LLM 提取三元组 → 知识图谱      │
│ Graph        │ 适合：实体关系推理             │
├──────────────┼──────────────────────────────┤
│ Property     │ 属性图（节点+边+属性）          │
│ Graph        │ 适合：结构化知识               │
└──────────────┴──────────────────────────────┘
```

### 3.4 Workflow 引擎（v0.10+）

2024 年推出的核心新特性，支持两种模式：

**Step-based 模式**（线性流程）：
```python
from llama_index.core.workflow import Workflow, StartEvent, StopEvent, step

class MyWorkflow(Workflow):
    @step
    async def step1(self, ev: StartEvent) -> Step2Event:
        # 处理
        return Step2Event(data=result)

    @step
    async def step2(self, ev: Step2Event) -> StopEvent:
        # 处理
        return StopEvent(result=final)
```

**DAG 模式**（有向无环图）：
```python
from llama_index.core.workflow import Workflow, Context

workflow = Workflow()
workflow.add_step("retrieve", retrieve_step)
workflow.add_step("synthesize", synthesize_step)
workflow.add_step("validate", validate_step)
# 定义边
workflow.add_edge("retrieve", "synthesize")
workflow.add_edge("synthesize", "validate")
```

核心特性：
- 事件驱动 — 步骤间通过自定义 Event 传递数据
- 条件分支 — 根据事件类型路由到不同步骤
- 并行执行 — 多步骤可并行运行
- 流式输出 — 支持中间结果流式返回
- 绘图 — 自动生成工作流 Mermaid 图

### 3.5 Agent 模式

```python
from llama_index.core.agent import ReActAgent

agent = ReActAgent.from_tools(
    tool_list,
    llm=llm,
    verbose=True
)
response = agent.chat("分析这份报告")
```

支持模式：
- **ReAct Agent** — 推理+行动循环
- **Function Calling Agent** — 原生工具调用
- **Workflow Agent** — 基于 Workflow 引擎的自定义 Agent

## 四、关键特性

### 4.1 高级 RAG 模式

- **Sentence Window Retrieval** — 检索匹配句 + 前后窗口
- **Auto-Merging Retrieval** — 小块匹配，自动合并为大块
- **Recursive Retrieval** — 多级索引递归检索
- **Multi-Document Agent** — 每个文档一个 Agent，路由选择
- **Self-RAG** — 自我评估检索质量

### 4.2 查询管道（QueryPipeline）

声明式 DAG 查询管道：
```python
from llama_index.core.query_pipeline import QueryPipeline

p = QueryPipeline()
p.add_modules({"retriever": retriever, "synthesizer": synthesizer})
p.add_link("retriever", "synthesizer", dest_key="nodes")
```

### 4.3 可观测性

内置集成：
- LangSmith — Trace 可视化
- Arize Phoenix — 开源 LLM 可观测
- OpenTelemetry — 标准化追踪
- Honeycomb — 生产监控

## 五、关键设计决策

1. **数据优先** — 核心抽象围绕 Document/Node/Index，而非 Chain/Agent
2. **零重依赖核心** — `llama-index-core` 不依赖任何 LLM 供应商
3. **独立集成包** — 每个供应商独立 pip 包，按需安装
4. **Workflow 事件驱动** — 步骤间通过 Event 解耦，天然支持条件分支
5. **与 LangChain 互补** — 不竞争，专注数据层，可组合使用

## 六、开发命令速查

```bash
# 安装
pip install llama-index
pip install llama-index-llms-openai
pip install llama-index-vector-stores-chroma

# 开发（从源码）
git clone https://github.com/run-llama/llama_index.git
cd llama_index
pip install -e llama-index-core
pip install -e llama-index-integrations/llms/llama-index-llms-openai

# 测试
pytest tests/
```

## 七、与竞品对比

| 维度 | LlamaIndex | [[langchain]] | [[dify]] |
|------|-----------|---------------|----------|
| 核心定位 | 数据+RAG | 通用 LLM 框架 | 可视化 LLMOps |
| 数据连接 | 160+ 连接器 | 700+ 集成 | 内置 RAG Pipeline |
| RAG 深度 | 最深（5+ 高级模式） | 中等 | 内置基础 RAG |
| 工作流 | Workflow 引擎 | LangGraph | 可视化拖拽 |
| 代码量 | 中 | 大 | 大 |
| 学习曲线 | 中等 | 陡峭 | 平缓 |

---

## 相关

- [[langchain]] — LLM 应用框架（互补关系）
- [[dify]] — 可视化 LLMOps 平台
- [[fast-gpt]] — 国产知识库问答平台
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
