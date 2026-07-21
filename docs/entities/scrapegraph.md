---
title: "ScrapeGraphAI: 基于 LangChain 的 LLM 驱动爬虫流水线"
created: 2026-07-22
updated: 2026-07-22
type: entity
tags: [web-scraping, ai-agent, llm, langchain, scrapegraph, python, open-source]
sources: [https://github.com/ScrapeGraphAI/Scrapegraph-ai, https://scrapegraphai.com]
confidence: high
---

> [[web-data-api-comparison|← Web 数据 API 竞品对比]] | [[firecrawl|Firecrawl]] | [[crawl4ai|Crawl4AI]] | [[llm-ready-data|LLM-ready 数据]]

# ScrapeGraphAI 深度解析

ScrapeGraphAI 是一个基于 Python 和 LangChain 的 LLM 驱动爬虫库，核心理念是 **“You Only Scrape Once”**：用户用自然语言描述想提取的信息，库自动构建并执行爬虫流水线。仓库 [ScrapeGraphAI/Scrapegraph-ai](https://github.com/ScrapeGraphAI/Scrapegraph-ai) 截至 2026-07 拥有 29k+ Stars，主要语言 Python，MIT 协议。

## 1. 产品定位与核心能力

ScrapeGraphAI 把“爬虫任务”建模为**节点图（Graph of Nodes）**，每个节点负责一个步骤（抓取、解析、搜索、生成答案等），最终由 LLM 完成信息提取。

| 能力 | 说明 | 典型场景 |
|---|---|---|
| **SmartScraper** | 单 URL + prompt → 结构化答案 | 产品信息、价格、新闻提取 |
| **SearchGraph** | 搜索 + 多结果聚合回答 | 开放性问题调研 |
| **SpeechGraph** | 网页内容 → 语音 | 语音摘要 |
| **OmniScraper** | 多模态（图像 + 文本） | 视觉信息理解 |
| **CSV / JSON / XML Scraper** | 结构化文件处理 | 本地文档解析 |
| **ScriptCreator** | 生成可复用的 Python 脚本 | 自动化流水线 |
| **MultiGraph** | 批量 URL / 多图处理 | 大规模提取 |
| **Code Generator** | 根据 prompt 生成代码 | 编程辅助 |
| **Markdownify** | 网页 → Markdown | 文档化 |
| **Screenshot** | 网页截图 | 可视化验证 |

## 2. 架构设计

### 2.1 代码结构

```
scrapegraphai/
├── graphs/                 # 预定义图流水线
│   ├── abstract_graph.py   # 抽象图基类
│   ├── base_graph.py       # 图执行引擎
│   ├── smart_scraper_graph.py
│   ├── search_graph.py
│   ├── omni_scraper_graph.py
│   ├── speech_graph.py
│   ├── csv_scraper_graph.py
│   ├── json_scraper_graph.py
│   ├── xml_scraper_graph.py
│   ├── script_creator_graph.py
│   ├── markdownify_graph.py
│   └── screenshot_scraper_graph.py
├── nodes/                  # 图节点实现
│   ├── fetch_node.py       # 获取内容
│   ├── parse_node.py       # 解析 HTML
│   ├── generate_answer_node.py
│   ├── search_internet_node.py
│   ├── rag_node.py
│   ├── reasoning_node.py
│   ├── conditional_node.py
│   ├── description_node.py
│   ├── get_probable_tags_node.py
│   └── ...
├── docloaders/             # 文档加载器
│   ├── chromium.py         # Chromium/Playwright
│   ├── browser_base.py
│   ├── plasmate.py
│   └── scrape_do.py
├── helpers/                # 辅助工具
│   ├── nodes_metadata.py   # 节点元数据
│   ├── default_filters.py
│   ├── models_tokens.py
│   ├── robots.py
│   └── schemas.py
├── models/                 # 模型封装
│   ├── xai.py
│   ├── deepseek.py
│   ├── nvidia.py
│   ├── clod.py
│   ├── minimax.py
│   └── oneapi.py
├── integrations/           # 第三方集成
│   ├── burr_bridge.py
│   ├── indexify_node.py
│   └── scrapegraph_py_compat.py
├── prompts/                # 提示词模板
├── utils/                  # 工具函数
└── telemetry/              # 遥测
```

### 2.2 图执行模型

`AbstractGraph` 是基类：

- 接收 `prompt`、可选 `source`（URL/文件路径）、`config`（含 LLM 配置）、`schema`（Pydantic 输出模型）。
- 负责创建 LLM 模型实例（`init_chat_model`）。
- 子类通过 `_create_graph()` 构建节点和边。

`BaseGraph` 是执行引擎：

- 维护 `nodes` 列表和 `edges` 有向边。
- 从 `entry_point` 开始执行。
- 按拓扑顺序调用每个节点的 `execute(state)`，更新全局状态。
- 支持 Burr 工作流引擎集成（`use_burr`）。
- 自动处理日志和遥测（`log_graph_execution`）。

### 2.3 节点类型

`nodes/` 目录是核心。每个节点继承 `BaseNode`，实现 `execute(state)`：

| 节点 | 作用 |
|---|---|
| **FetchNode** | 通过 ChromiumLoader 或 HTTP 抓取 HTML |
| **ParseNode** | 用 `Html2TextTransformer` 解析 HTML 并分块 |
| **GenerateAnswerNode** | 用 LLM 根据 prompt 和文档生成答案 |
| **SearchInternetNode** | 把 prompt 改写为搜索查询，调用 DuckDuckGo/Serper |
| **RAGNode** | 向量检索，支持 Qdrant，降低长文档 token |
| **ReasoningNode** | 根据 schema 和上下文精炼 prompt |
| **ConditionalNode** | 条件分支 |
| **GetProbableTagsNode** | 识别可能包含答案的 HTML 标签 |
| **RobotsNode** | 检查 robots.txt |
| **DescriptionNode** | 生成页面描述 |
| **ImageToTextNode** | 图像 OCR |
| **MarkdownifyNode** | 生成 Markdown |
| **TextToSpeechNode** | 文本转语音 |

### 2.4 SmartScraperGraph 流水线

`smart_scraper_graph.py` 是最典型的图：

```
FetchNode → ParseNode → GenerateAnswerNode
```

- 如果启用搜索，会加入 `SearchInternetNode`。
- 如果启用 RAG，会加入 `RAGNode`。
- 支持 schema 约束输出。

`GenerateAnswerNode` 会根据文档长度选择模板：

- 短文档：`TEMPLATE_NO_CHUNKS`
- 长文档：`TEMPLATE_CHUNKS` + `TEMPLATE_MERGE`
- Markdown 模式：`TEMPLATE_*_MD`

### 2.5 文档加载器

`docloaders/chromium.py` 的 `ChromiumLoader`：

- 默认使用 Playwright 作为后端。
- 支持代理、headless 模式、存储状态、加载状态（`domcontentloaded` / `networkidle`）。
- 可回退到 `requests`（`use_soup=True`）。
- 输出 LangChain `Document` 对象。

### 2.6 LLM 集成

`abstract_graph.py` 中通过 `init_chat_model` 统一初始化各种 LangChain 兼容模型：

- OpenAI / Azure OpenAI
- Anthropic / Claude
- Google / Gemini
- Mistral / Groq / Ollama / DeepSeek / xAI / Nvidia / OneApi / CLoD / MiniMax
- 支持 rate limiter（`InMemoryRateLimiter`）

### 2.7 RAG 节点

`rag_node.py` 使用 Qdrant 作为向量库：

- 将文档分块后 embedding。
- 支持内存、本地 db、远程三种 client_type。
- 通过向量检索压缩输入 token。

### 2.8 提示词工程

`prompts/` 目录包含大量模板：

- `TEMPLATE_CHUNKS`、`TEMPLATE_NO_CHUNKS`：按是否分块生成答案。
- `TEMPLATE_MERGE`：合并多个 chunk 的答案。
- `TEMPLATE_SEARCH_INTERNET`：搜索查询改写。
- `TEMPLATE_REASONING`：基于 schema 推理。
- 使用 `JsonOutputParser` 或 Pydantic 输出解析器确保结构化输出。

### 2.9 遥测与日志

- `telemetry/` 收集匿名执行数据。
- `utils/logging.py` 提供统一日志。
-  verbose 模式控制是否打印执行过程。

## 3. 关键特性实现

### 3.1 自然语言 → 结构化数据

用户示例：

```python
from scrapegraphai.graphs import SmartScraperGraph

graph = SmartScraperGraph(
    prompt="List me all the attractions in Chioggia.",
    source="https://en.wikipedia.org/wiki/Chioggia",
    config={"llm": {"model": "openai/gpt-3.5-turbo"}}
)
result = graph.run()
```

底层：Fetch → Parse → GenerateAnswer，LLM 根据 prompt 和页面内容生成答案。

### 3.2 Schema 约束输出

```python
from pydantic import BaseModel

class Attraction(BaseModel):
    name: str
    description: str

graph = SmartScraperGraph(..., schema=Attraction)
```

`GenerateAnswerNode` 使用 `get_pydantic_output_parser` 强制 LLM 输出符合 schema。

### 3.3 搜索增强

`SearchGraph` 在 `SmartScraperGraph` 基础上加入 `SearchInternetNode`：

1. 用 LLM 把 prompt 改写为搜索查询。
2. 调用 DuckDuckGo 或 Serper。
3. 对多个结果分别抓取、解析、生成答案。
4. 合并为最终答案。

### 3.4 多模态

`OmniScraperGraph` 结合图像和文本：

- 使用 `FetchScreenNode` 获取页面截图。
- `ImageToTextNode` / `GenerateAnswerFromImageNode` 对图像做 OCR/理解。
- 最终结合文本答案生成结构化输出。

## 4. 生态与集成

| 类型 | 代表 |
|---|---|
| **LLM 框架** | LangChain、LlamaIndex、CrewAI、Agno、CamelAI |
| **搜索** | DuckDuckGo、Serper |
| **向量库** | Qdrant |
| **文档加载器** | Playwright / Chromium |
| **工作流** | Burr |
| **平台** | ScrapeGraphAI Cloud（scrapegraphai.com） |
| **SDK** | Python、Node.js（官方） |

## 5. 商业模式

- **开源**：MIT 协议。
- **Cloud**：scrapegraphai.com 提供托管增强版。
- **SDK**：Python 为主，Node.js 为辅。

## 6. 与 Firecrawl / Crawl4AI / Browser-Use 的对比

| 维度 | Firecrawl | Crawl4AI | ScrapeGraphAI | Browser-Use |
|---|---|---|---|---|
| **核心抽象** | 多引擎 API | 策略模式 | LangChain Graph 节点 | 浏览器 Agent |
| **上手难度** | 低 | 中 | 中 | 中 |
| **灵活性** | 中 | 高 | 中（受 LangChain 约束） | 高 |
| **LangChain 依赖** | 无 | 无 | 强 | 无 |
| **自然语言提取** | ✅ | ✅ | ✅（主打） | ⚠️ 需结合 LLM |
| **浏览器交互** | 有限 | 有限 | 有限 | 强 |
| **搜索** | ✅ | ✅ | ✅ | ❌ |
| **结构化输出** | ✅ schema | ✅ schema | ✅ schema（强） | ✅ Pydantic |
| **社区热度** | 154k | 74k | 29k | 106k |
| **License** | AGPL-3.0 | Apache-2.0 | MIT | Apache-2.0 |

## 7. 学习启示

| 维度 | 可借鉴点 |
|---|---|
| **Graph 节点模型** | 把爬虫任务拆成可组合节点，对复杂多步骤任务表达清晰 |
| **自然语言即接口** | 用 prompt 替代 XPath/CSS，降低非开发者使用门槛 |
| **Schema 约束** | Pydantic 输出确保下游可直接消费 |
| **LangChain 生态** | 复用 LangChain 模型、文档、加载器、解析器，减少自研成本 |
| **模板化生成** | 针对短/长文档、是否 Markdown 使用不同模板，提升输出质量 |
| **多模态扩展** | 图像 + 文本结合的 OmniScraper 是差异化方向 |

## 相关页面
- [[firecrawl]] — Firecrawl 深度解析
- [[crawl4ai]] — Crawl4AI 深度解析
- [[browser-use]] — Browser-Use 深度解析
- [[web-data-api-comparison]] — Web 数据 API 竞品对比
- [[llm-ready-data]] — LLM-ready 数据概念
- [[ai-agent-ecosystem]] — AI Agent 生态概览
