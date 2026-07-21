---
title: "Browser-Use: AI 浏览器自动化 Agent"
created: 2026-07-22
updated: 2026-07-22
type: entity
tags: [ai-agent, browser-automation, web-interaction, playwright, cdp, python, open-source]
sources: [https://github.com/browser-use/browser-use, https://docs.browser-use.com, https://browser-use.com]
confidence: high
---

> [[web-data-api-comparison|← Web 数据 API 竞品对比]] | [[browser-use-architecture|Browser-Use 技术架构]] | [[ai-agent-ecosystem|AI Agent 生态]]

# Browser-Use 深度解析

Browser-Use 是一个开源的 AI 浏览器自动化框架，让大语言模型像人类一样操作网页：打开页面、点击按钮、填写表单、滚动、截图、提取信息。仓库 [browser-use/browser-use](https://github.com/browser-use/browser-use) 截至 2026-07 拥有 106k+ Stars、11.6k+ Forks，是 AI Agent 浏览器自动化赛道最火的项目之一。

## 1. 产品定位与核心能力

Browser-Use 的核心理念：**“让网站对 AI Agent 可访问”**。它把浏览器操作封装成 LLM 可理解的结构化接口，让 Agent 通过自然语言任务完成复杂的网页交互。

| 能力 | 说明 | 典型场景 |
|---|---|---|
| **自然语言任务** | 描述目标，Agent 自动规划执行 | “帮我在亚马逊上搜机械键盘并比较价格” |
| **浏览器操作** | 点击、输入、滚动、选择下拉框、上传文件 | 表单填写、后台操作 |
| **多标签管理** | 自动创建、切换、关闭标签页 | 跨页面流程 |
| **截图与视觉** | 可选使用截图辅助 LLM 决策 | 视觉敏感任务 |
| **文件系统** | Agent 可读写本地文件 | 保存中间结果 |
| **结构化输出** | 返回 Pydantic 模型 | 与后端系统对接 |
| **评价/裁判** | 自动判断任务是否完成 | 无需人工验证 |
| **消息压缩** | 历史消息摘要，避免上下文爆炸 | 长时任务 |
| **Skill 市场** | 从 Browser-Use Cloud 加载复用技能 | 降低重复开发 |
| **MCP 支持** | 提供 MCP Server | 接入 Claude/Cursor 等客户端 |

## 2. 架构设计

### 2.1 代码结构

```
browser_use/
├── agent/                    # Agent 核心
│   ├── service.py            # Agent 主循环
│   ├── views.py              # 状态/动作/输出模型
│   ├── prompts.py            # Prompt 生成
│   ├── system_prompts/       # 系统提示模板
│   ├── message_manager/      # 消息历史管理
│   ├── judge.py              # 裁判/评价系统
│   ├── variable_detector.py  # 变量复用检测
│   └── gif.py                # 执行过程 GIF 生成
├── browser/                  # 浏览器层
│   ├── session.py            # BrowserSession（事件驱动）
│   ├── chrome.py             # Chrome 可执行文件探测
│   ├── profile.py            # 浏览器配置/代理
│   ├── cloud/                # Cloud Browser 支持
│   ├── watchdogs/            # 浏览器看门狗
│   ├── events.py             # 事件总线定义
│   └── views.py              # 状态视图
├── dom/                      # DOM 处理
│   ├── service.py            # DomService（AX tree + DOM 快照）
│   ├── serializer/           # DOM 序列化
│   ├── enhanced_snapshot.py  # 增强快照
│   └── views.py              # DOM 视图模型
├── tools/                    # 工具/动作注册
│   ├── service.py            # Controller/Tools
│   └── registry/             # 动作注册表
├── llm/                      # 多模型封装
│   ├── base.py               # 统一 ChatModel 接口
│   ├── openai/chat.py        # OpenAI
│   ├── anthropic/chat.py     # Anthropic
│   ├── google/chat.py        # Google
│   ├── litellm/chat.py        # LiteLLM 代理
│   └── ...                   # 其他 provider
├── actor/                    # 高级 actor 操作（page/element/mouse）
├── filesystem/               # 本地文件系统操作
├── telemetry/                # 匿名遥测
├── observability/            # 可观测性
└── skills/                   # Browser-Use Cloud Skills
```

### 2.2 Agent 主循环

`agent/service.py` 中的 `Agent` 类是核心。每轮循环：

1. 获取当前浏览器状态（URL、标签、可交互元素、截图）。
2. 把状态 + 历史 + 任务拼成 prompt。
3. 调用 LLM 生成下一步动作（`AgentOutput`）。
4. 执行动作（通过 `Tools`）。
5. 记录结果到历史。
6. 重复直到任务完成或达到最大步数。

关键模型 `AgentOutput`（`agent/views.py`）：

- `current_state`：包含当前状态、思考、下一步目标、是否完成。
- `action`：一个或多个动作（Pydantic 模型列表）。
- `memory` / `thought`：可选记忆和推理。

### 2.3 浏览器层：事件驱动架构

`browser/session.py` 中 `BrowserSession` 基于 **事件总线（EventBus）** 设计：

- 事件类型：`BrowserStartEvent` / `NavigateToUrlEvent` / `NavigationCompleteEvent` / `ClickElementEvent` / `ScrollEvent` / `TabCreatedEvent` / `FileDownloadedEvent` 等。
- CDP 集成：通过 `cdp_use` 库与 Chrome DevTools Protocol 通信。
- 多 Target 支持：页面、iframe、popup 都是 Target，可独立处理。
- Cloud Browser：支持 `CloudBrowserClient` 连接远程浏览器实例。

`BrowserStateSummary` 是发给 LLM 的浏览器状态摘要：

- 当前 URL、标题、标签页列表。
- 可交互元素树（XML 格式，带索引）。
- 可选截图（base64）。
- 页面滚动/尺寸信息。

### 2.4 DOM 服务：可交互元素快照

`dom/service.py` 中的 `DomService`：

- 使用 CDP 的 `Accessibility.getFullAXTree` 获取可访问性树。
- 结合 DOM 序列化，生成 LLM 可读的元素索引列表。
- 支持跨域 iframe、paint order 过滤、视口阈值。
- 输出 `SerializedDOMState`，每个元素有唯一索引，LLM 通过 `@e1` 引用。

### 2.5 工具系统（Tools/Controller）

`tools/service.py` 是工具总线：

- 动作模型：`ClickElementAction` / `InputTextAction` / `NavigateAction` / `ScrollAction` / `ScreenshotAction` / `ExtractAction` / `DoneAction` / `SearchAction` / `UploadFileAction` 等。
- 每个动作映射到对应浏览器事件。
- 支持自定义动作注册。
- 与 `agent/views.py` 中的 `ActionModel` 联动，LLM 输出结构化动作。

### 2.6 消息管理（Message Manager）

`agent/message_manager/service.py`：

- 维护 Agent 与 LLM 的对话历史。
- 敏感信息脱敏（`redact_sensitive_string`）。
- 消息压缩（`MessageCompactionSettings`）：当上下文超过阈值，自动摘要历史。

### 2.7 系统提示词

`agent/system_prompts/system_prompt.md` 定义 Agent 行为：

- 输入包括 user_request、agent_history、agent_state、browser_state、browser_vision、read_state。
- 输出格式为 XML，包含思考、记忆、下一步目标、动作。
- 支持多语言（默认英文，跟随用户请求）。
- 针对 Anthropic / Browser-Use 自研模型有不同模板变体。

### 2.8 Watchdog 系统

`browser/watchdogs/` 是一组浏览器守护程序：

- `CaptchaWatchdog`：监听验证码解决事件，阻塞 Agent 直到完成。
- `CrashWatchdog`：检测浏览器崩溃并恢复。
- `AboutBlankWatchdog`：处理空白页导航。

### 2.9 裁判/评价系统

`agent/judge.py`：

- 任务完成后，使用 LLM 评估执行轨迹是否真正达成目标。
- 输入：任务、最终结果、步骤列表、截图。
- 输出：成功/失败判断 + 理由。
- 可配合 `ground_truth` 做客观验证。

### 2.10 变量检测与复用

`agent/variable_detector.py`：

- 在历史动作中检测可复用变量（email、phone、date 等）。
- 基于元素属性和值模式匹配。
- 帮助 Agent 在后续步骤中自动填充已输入过的信息。

### 2.11 多模型支持

`llm/` 目录封装了 10+ 模型 provider：OpenAI、Anthropic、Google、Azure、Groq、Mistral、Ollama、LiteLLM、Vercel、OCI 等。统一通过 `BaseChatModel` 接口接入 Agent。

### 2.12 遥测与可观测性

`telemetry/service.py`：

- 使用 PostHog 收集匿名遥测数据。
- 可通过 `ANONYMIZED_TELEMETRY=False` 关闭。
- 生成设备 ID 用于去重统计。

## 3. 关键特性实现

### 3.1 视觉模式

`AgentSettings.use_vision`：

- `True`：将截图加入 LLM 输入，用于视觉理解。
- `'auto'`：由系统判断何时使用截图。
- `False`：纯文本模式（基于 DOM 描述）。

### 3.2 Flash 模式

`flash_mode=True`：

- 禁用“评估上一步”和“下一步目标”字段，减少 token。
- 适合简单、高吞吐任务。

### 3.3 Skills 模块

`browser_use/skills/`：

- 从 Browser-Use Cloud 拉取技能。
- 技能是可复用的浏览器任务单元。
- 通过 API key 执行。

### 3.4 MCP 支持

Browser-Use 提供 MCP Server，让 Claude Desktop、Cursor、Windsurf 等客户端直接调用浏览器能力。这是其生态扩展的重要一环。

## 4. 生态与集成

| 类型 | 代表 |
|---|---|
| **模型** | OpenAI、Anthropic、Google、Azure、Groq、Ollama 等 |
| **浏览器** | 本地 Chrome/Chromium、远程 CDP、Cloud Browser |
| **客户端** | Claude Desktop、Cursor、Windsurf、Goose、Grok、Junie（MCP） |
| **云** | cloud.browser-use.com |
| **CLI** | 与 Playwright CLI + Skills 区分（官方推荐 CLI+Skills 给 coding agent） |

## 5. 商业模式

- **开源**：Apache-2.0，完全免费。
- **Cloud**：cloud.browser-use.com 提供托管浏览器、代理、技能市场、企业支持。
- **MCP/Skills**：通过生态扩展形成付费转化。

## 6. 与 Firecrawl / Crawl4AI 的对比

| 维度 | Firecrawl | Crawl4AI | Browser-Use |
|---|---|---|---|
| **核心目标** | 数据提取 API | 可编程爬虫库 | 浏览器自动化 Agent |
| **交互能力** | ✅ Interact（有限） | ⚠️ 需自行实现 | ✅ 核心能力 |
| **数据输出** | Markdown/JSON/截图 | Markdown/JSON | 结构化输出/文件 |
| **自主性** | 中（Agent endpoint） | 低 | 高 |
| **视觉理解** | 截图 | 截图 | 截图 + DOM 双树 |
| **使用场景** | RAG 数据管道 | 数据工程师 | 自动化操作任务 |
| **LLM 依赖** | 抽取/Agent 用 LLM | 抽取用 LLM | 核心循环强依赖 LLM |
| **MCP** | ✅ | ❌ | ✅ |

## 7. 学习启示

| 维度 | 可借鉴点 |
|---|---|
| **事件驱动浏览器** | 用 EventBus + CDP 事件把浏览器状态解耦，比直接操作 page 更灵活 |
| **AX + DOM 双树** | 可访问性树提供 LLM 友好的元素索引，DOM 提供视觉/结构信息 |
| **结构化动作输出** | 每个动作都是 Pydantic 模型，LLM 输出可直接执行 |
| **消息压缩** | 长时任务必须做历史摘要，否则上下文爆炸 |
| **裁判系统** | 自动评估任务完成度，降低人工验证成本 |
| **变量复用** | 检测历史输入中的变量，减少重复输入和错误 |
| **分层模板** | 针对不同模型（Anthropic / 自研模型）使用不同系统提示模板 |
| **遥测默认开启+可关闭** | 收集数据同时尊重隐私选择 |

## 相关页面
- [[browser-use-architecture]] — Browser-Use 技术架构（更详细的分层分析）
- [[browser-use-highlights]] — Browser-Use 十大技术亮点
- [[firecrawl]] — Firecrawl 深度解析
- [[crawl4ai]] — Crawl4AI 深度解析
- [[web-data-api-comparison]] — Web 数据 API 竞品对比
- [[ai-agent-ecosystem]] — AI Agent 生态概览
