---
title: "Jina Reader: 极简 URL→LLM 友好输入服务"
created: 2026-07-22
updated: 2026-07-22
type: entity
tags: [web-scraping, llm-ready-data, jina-ai, reader, api, open-source, url-to-markdown]
sources: [https://github.com/jina-ai/reader, https://jina.ai/reader, https://r.jina.ai]
confidence: high
---

> [[web-data-api-comparison|← Web 数据 API 竞品对比]] | [[firecrawl|Firecrawl]] | [[crawl4ai|Crawl4AI]] | [[llm-ready-data|LLM-ready 数据]]

# Jina Reader 深度解析

Jina Reader 是 Jina AI 推出的开源 Web 内容提取服务，核心口号：**“Your LLMs deserve better input.”** 它提供两个极简接口：`https://r.jina.ai/<URL>` 把任意 URL 转成 LLM 友好的 Markdown；`https://s.jina.ai/<query>` 搜索网页并返回结果。截至 2026-07，仓库 [jina-ai/reader](https://github.com/jina-ai/reader) 拥有 12k+ Stars，TypeScript 实现，Apache-2.0 协议。

## 1. 产品定位与核心能力

Jina Reader 不是通用爬虫框架，而是一个**专注、快速、稳定、免费的“网页 → Markdown” 服务**。它牺牲了一部分复杂能力，换取极致的易用性。

| 能力 | 说明 | 接口示例 |
|---|---|---|
| **Read** | URL → Markdown / HTML / Text / Screenshot | `https://r.jina.ai/https://example.com` |
| **Search** | 搜索 → 结果摘要 | `https://s.jina.ai/What+is+AI` |
| **PDF / Office** | 解析 PDF、Word、Excel、PPT | 直接 POST 文件或传 URL |
| **VLM 模式** | 用视觉模型提取页面 | `?format=vlm` |
| **ReaderLM** | 自研小型语言模型做提取 | `?format=readerlm-v2` |
| **Chunking** | 按标题层级切分内容 | `?chunking=h1` |
| **Preset** | reader / index / research / agent / spider | `?preset=research` |
| **Search Grounding** | 返回搜索结果来源 | `https://s.jina.ai/...` |

## 2. 架构设计

### 2.1 代码结构

```
reader/
├── src/
│   ├── api/
│   │   ├── crawler.ts          # 核心抓取逻辑
│   │   ├── searcher.ts         # 搜索逻辑
│   │   └── serp.ts             # SERP 接口
│   ├── dto/
│   │   ├── crawler-options.ts  # 抓取选项枚举
│   │   └── turndown-tweakable-options.ts
│   ├── services/
│   │   ├── puppeteer.ts        # 浏览器渲染
│   │   ├── curl.ts             # curl-impersonate 轻量抓取
│   │   ├── jsdom.ts            # JSDOM 解析
│   │   ├── snapshot-formatter.ts # 输出格式化
│   │   ├── markify.ts          # 自定义 Markdown 转换器
│   │   ├── pdf-extract.ts      # PDF 解析
│   │   ├── binary-extractor.ts # 二进制文件提取
│   │   ├── robots-text.ts      # robots.txt 处理
│   │   ├── proxy-provider/     # 代理集成
│   │   ├── common-llm/         # LLM 封装（GPT/Gemini/ReaderLM 等）
│   │   ├── alt-text.ts         # 图片 alt 生成
│   │   └── canvas.ts           # Canvas 处理
│   ├── stand-alone/
│   │   ├── crawl.ts            # 独立 Crawl 服务入口
│   │   └── search.ts           # 独立 Search 服务入口
│   ├── db/
│   │   ├── bucket-storage.ts   # 可选 S3/MinIO 存储
│   │   └── noop-storage.ts     # 无状态默认
│   ├── lib/
│   │   └── transform-server-event-stream.ts
│   └── 3rd-party/              # 第三方 API 封装
├── package.json
└── docker-compose.yaml
```

### 2.2 服务入口

`CrawlStandAloneServer` 和 `SearchStandAloneServer` 分别启动两个 Koa HTTP/2 服务：

- 使用 `tsyringe` 做依赖注入。
- 基于 Jina AI 自研的 `civkit` 框架构建（RPC、压缩、日志、文件处理等）。
- 支持 HTTP/2 和 HTTP/1 回退。

### 2.3 抓取双引擎

`src/api/crawler.ts` 中 `CrawlerHost` 根据配置选择引擎：

| 引擎 | 用途 | 实现 |
|---|---|---|
| **Browser** | JS 重页面、需要截图 | `PuppeteerControl` |
| **CURL** | 轻量、快速、静态页面 | `CurlControl`（基于 `node-libcurl-impersonate`） |
| **CF Browser Rendering** | Cloudflare 特殊渲染 | `CFBrowserRendering` |
| **AUTO** | 自动选择 | 默认策略 |

`CurlControl` 使用 `curl-impersonate` 模拟 Chrome TLS 指纹，提升绕过简单反爬的能力。

### 2.4 页面快照

`src/services/puppeteer.ts` 中的 `PuppeteerControl`：

- 使用 Puppeteer 控制浏览器。
- 在页面内注入 `@mozilla/readability/Readability.js` 提取正文。
- 返回 `PageSnapshot`：标题、描述、HTML、text、ReadabilityParsed、截图、图片列表、状态码等。
- 支持多种响应时机：`html` / `visible-content` / `mutation-idle` / `resource-idle` / `network-idle`。
- 内置 `minimalStealth.js` 减少 bot 检测。
- 支持 iframe、Shadow DOM 展开。

### 2.5 Markdown 转换

`src/services/markify.ts` 提供 `MarkifyService`：

- 基于自定义规则遍历 DOM，生成 Markdown。
- 支持 CommonMark 元素：heading、paragraph、list、link、image、table、code、quote、math 等。
- 支持 MathML → LaTeX 转换。
- `snapshot-formatter.ts` 最终输出 `FormattedPage`：包含 content、html、text、links、images、metadata、chunks 等。

### 2.6 搜索实现

`src/api/searcher.ts` 中的 `SearcherHost`：

- 使用 Serper 的 Google/Bing 搜索 API。
- 对搜索结果调用 `CrawlerHost` 抓取并格式化。
- 支持 `?q=` 查询参数，以及语言、国家、时间范围等过滤。
- 结果可配置 grounding 和返回格式。

### 2.7 抓取选项（CrawlerOptions）

`src/dto/crawler-options.ts` 定义了丰富的选项：

- **CONTENT_FORMAT**: content / markdown / html / text / pageshot / screenshot / vlm / readerlm-v2 / frontmatter
- **ENGINE_TYPE**: auto / browser / curl / cf-browser-rendering
- **RESPOND_TIMING**: html / visible-content / mutation-idle / resource-idle / media-idle / network-idle
- **CHUNKING_STRATEGY**: h1-h5 / structured
- **IMAGE_RETENTION_MODES**: none / all / alt / all_p / alt_p
- **LINK_RETENTION_MODES**: none / all / text / gpt-oss
- **PRESET_NAMES**: reader / index / research / agent / spider

### 2.8 存储层

- 开源分支默认使用 `noop-storage`（无状态）。
- 可选 `bucket-storage` 接入 S3/MinIO 做缓存。
- 商业版（SaaS）使用 MongoDB Atlas 做持久化，但不在开源分支中。

### 2.9 安全与合规

- `RobotsTxtService` 检查 robots.txt。
- `BlackHoleDetector` 防止黑洞 URL（无限重定向等）。
- 私有 IP 拦截（`privateIpNotAcceptable`）。
- 文件大小限制、超时控制。
- 代理集成：Bright Data、Thordata。

## 3. 关键特性实现

### 3.1 极简 URL 前缀

```
https://r.jina.ai/https://example.com
https://r.jina.ai/http://example.com/path
```

后端识别 URL 模式，提取目标地址，调用抓取流水线，返回 Markdown。

### 3.2 ReaderLM 模型

Jina AI 自研了 ReaderLM（v2 版本），专门把网页 HTML 转成 Markdown：

- 在 `common-llm/reader-lm.ts` 中调用。
- 小模型、低成本、适合高频服务。
- 通过 `?format=readerlm-v2` 启用。

### 3.3 PDF 与 Office 文档

`pdf-extract.ts` 和 `binary-extractor.ts`：

- 支持直接上传 PDF / Word / Excel / PPT 文件。
- 或传 URL 指向文档。
- 提取文本后按 Markdown 格式返回。

### 3.4 Preset 预设

针对不同场景提供预设配置：

| Preset | 特点 |
|---|---|
| **reader** | 默认，保留图片和链接 |
| **index** | 适合构建索引，chunk 更细 |
| **research** | 深度研究，保留更多上下文 |
| **agent** | 适合 Agent 使用，结构化输出 |
| **spider** | 蜘蛛模式，抓取更多链接 |

## 4. 生态与集成

| 类型 | 代表 |
|---|---|
| **使用方式** | URL 前缀、HTTP API、Docker 自部署 |
| **搜索源** | Google、Bing（Serper） |
| **浏览器** | Puppeteer |
| **轻量抓取** | curl-impersonate |
| **Markdown 转换** | 自定义 Markify + Readability |
| **LLM** | ReaderLM、GPT-4、Gemini、OpenRouter 等 |
| **部署** | Docker Compose、Cloud Run |

## 5. 商业模式

- **开源**：Apache-2.0，核心服务代码开放。
- **免费 SaaS**：`r.jina.ai` / `s.jina.ai` 提供稳定公开服务，有 rate limit。
- **商业版**：Jina AI 提供更高并发、企业支持、私有部署。
- **ReaderLM**：自研模型既服务自身，也可能作为独立产品输出。

## 6. 与 Firecrawl / Crawl4AI / ScrapeGraphAI / Browser-Use 的对比

| 维度 | Jina Reader | Firecrawl | Crawl4AI | ScrapeGraphAI | Browser-Use |
|---|---|---|---|---|---|
| **核心定位** | URL→Markdown 服务 | Web 数据 API | Python 爬虫库 | LLM 流水线库 | 浏览器 Agent |
| **易用性** | ⭐⭐⭐ 极简 | 低 | 中 | 中 | 中 |
| **功能丰富度** | 中 | 高 | 高 | 高 | 中（偏交互） |
| **浏览器交互** | ❌ | ✅ | ⚠️ | ⚠️ | ✅ |
| **结构化提取** | 基础 | 强 | 强 | 强 | 弱 |
| **搜索** | ✅ | ✅ | ✅ | ✅ | ❌ |
| **自部署** | ✅ Docker | ✅ docker-compose | ✅ Docker | ✅ pip install | ✅ Docker |
| **License** | Apache-2.0 | AGPL-3.0 | Apache-2.0 | MIT | Apache-2.0 |
| **开源代码量** | 中 | 大 | 中 | 中 | 大 |

## 7. 学习启示

| 维度 | 可借鉴点 |
|---|---|
| **极简接口** | 用 URL 前缀降低使用门槛，让非开发者也能用 |
| **双引擎选择** | 浏览器 + curl-impersonate 自动切换，平衡速度和成功率 |
| **Readability 提取** | 用成熟库提取正文，避免重复造轮子 |
| **Preset 配置** | 针对不同场景预设参数，减少用户选择 |
| **自研小模型** | ReaderLM 是差异化武器，降低服务成本 |
| **无状态开源** | 剥离 MongoDB 商业层，开源分支可一键跑 |
| **免费即营销** | 稳定免费服务是最好的获客和生态扩散手段 |

## 相关页面
- [[firecrawl]] — Firecrawl 深度解析
- [[crawl4ai]] — Crawl4AI 深度解析
- [[scrapegraph]] — ScrapeGraphAI 深度解析
- [[browser-use]] — Browser-Use 深度解析
- [[web-data-api-comparison]] — Web 数据 API 竞品对比
- [[llm-ready-data]] — LLM-ready 数据概念
- [[ai-agent-ecosystem]] — AI Agent 生态概览
