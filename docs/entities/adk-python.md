---
title: Google ADK (Agent Development Kit) Python
created: 2026-05-14
updated: 2026-06-28
type: entity
tags: [agent-framework, google, python, multi-agent, a2a]
---

# Google ADK (Agent Development Kit) Python

> Google 官方开源 Agent 框架，code-first 方式构建多 Agent 系统。PyPI 包名 `google-adk`，Apache 2.0 许可。
> Source: https://github.com/google/adk-python

## 一、项目定位

| 维度 | 内容 |
|------|------|
| 维护者 | Google LLC |
| 语言 | Python 3.10+ |
| 构建 | flit |
| 核心依赖 | pydantic v2, google-genai, click, fastapi, uvicorn |
| 许可 | Apache 2.0 |
| 版本 | v1.33.0+ (2026-05) |

ADK 的核心理念：**用 Python 代码定义 Agent，而非 YAML/JSON 配置**。Agent 即 Python 对象，工具即函数，流程即编排。

## 二、架构总览

```
google.adk
├── agents/          # Agent 定义层
│   ├── BaseAgent    # 所有 Agent 的基类（Pydantic BaseModel）
│   ├── LlmAgent     # LLM 驱动的 Agent（核心）
│   ├── LoopAgent    # 循环编排
│   ├── ParallelAgent    # 并行编排
│   └── SequentialAgent # 顺序编排
├── models/          # LLM 接入层
│   ├── Gemini / Google LLM   # Google 原生（默认 gemini-2.5-flash）
│   ├── Anthropic LLM         # Claude 系列
│   ├── LiteLLM               # 100+ 模型统一接口
│   ├── Gemma LLM             # 本地 Gemma 模型
│   └── Apigee LLM            # 企业 API 网关
├── tools/           # 工具层（50+ 内置工具）
├── flows/           # 执行流（LLM 交互循环）
├── sessions/        # 会话持久化
├── memory/          # 长期记忆
├── artifacts/       # 文件/二进制存储
├── a2a/             # Agent-to-Agent 协议
├── cli/             # 命令行工具（adk 命令）
├── auth/            # 认证服务
├── telemetry/       # 可观测性（OpenTelemetry）
├── evaluation/      # Agent 评估框架
├── optimization/    # Prompt 优化（GEPA）
├── skills/          # 技能注册表
└── code_executors/  # 代码执行沙箱
```

## 三、Agent 体系

### 3.1 类层次

```
BaseAgent (Pydantic BaseModel)
├── LlmAgent (= Agent 快捷别名)
│   └── 内部使用 Flow 驱动 LLM 交互循环
├── LoopAgent        # 循环执行子 Agent
├── ParallelAgent    # 并行执行子 Agent
└── SequentialAgent  # 顺序执行子 Agent
```

### 3.2 LlmAgent 核心属性

```python
Agent(
    name="my_agent",
    model="gemini-2.5-flash",      # 模型选择
    instruction="系统提示词",        # 可为函数（动态生成）
    description="Agent 描述",       # 供其他 Agent 路由决策
    tools=[...],                    # 工具列表
    sub_agents=[...],               # 子 Agent（多 Agent 编排）
    output_schema=MySchema,         # 结构化输出
    planner=BasePlanner,            # 规划器
    flow=AutoFlow | SingleFlow,    # 执行流
    before_agent_callback=...,      # 前置回调
    after_agent_callback=...,       # 后置回调
)
```

### 3.3 多 Agent 编排

- **树形结构**：`sub_agents` 定义父子关系
- **Agent 转移**：运行时通过 `agent_transfer` 工具动态切换
- **编排模式**：Sequential / Parallel / Loop 三种内置编排器
- **模型驱动路由**：LLM 根据 `description` 自动选择转移目标

## 四、工具系统

### 4.1 工具类型

| 类型 | 说明 |
|------|------|
| `FunctionTool` | 普通 Python 函数自动包装 |
| `AgentTool` | 将另一个 Agent 作为工具调用 |
| `BaseToolset` | 工具集（按需加载、条件启用） |
| MCP Toolset | Model Context Protocol 工具 |
| Google Search | 内置搜索 |
| BigQuery Toolset | 数据库查询 |
| OpenAPI Toolset | REST API 自动封装 |
| API Hub Toolset | Google API Hub 集成 |
| Application Integration | Google Application Integration |
| Retrieval | RAG 检索（Vertex AI RAG / LlamaIndex） |
| Bash Tool | Shell 命令执行 |
| Skill Toolset | 技能注册表工具 |
| Agent Simulator | Agent 模拟器（测试用） |

### 4.2 工具定义方式

```python
# 方式 1：自动包装函数
def get_weather(city: str) -> dict:
    """获取天气信息"""  # docstring 自动成为工具描述
    return {"temp": 25, "city": city}

# 方式 2：直接在 Agent 声明
Agent(tools=[get_weather, google_search])
```

### 4.3 认证工具

- `AuthenticatedFunctionTool` — OAuth2 / API Key 自动注入
- `BaseAuthenticatedTool` — 认证工具基类
- 支持 OAuth2 Client Credentials、Google Cloud Auth 等

## 五、执行流 (Flows)

Flows 是 LLM 交互的编排引擎，控制 Agent 如何与 LLM 通信。

| Flow | 说明 |
|------|------|
| `AutoFlow` | 默认流，自动处理工具调用循环 |
| `SingleFlow` | 单轮交互，无自动工具调用 |
| `BaseLlmFlow` | 基类，可自定义 |

### Flow 内部处理器 (Processors)

```
BaseLlmFlow
├── instructions.py        # 指令注入
├── contents.py            # 上下文内容管理
├── functions.py           # 工具调用处理
├── compaction.py          # 上下文压缩
├── identity.py            # 身份信息
├── agent_transfer.py      # Agent 转移
├── context_cache_processor.py  # 上下文缓存
├── _code_execution.py     # 代码执行
├── _nl_planning.py        # 自然语言规划
├── _output_schema_processor.py # 输出 Schema 处理
├── request_confirmation.py # 人工确认
├── interactions_processor.py   # 交互处理
└── audio_*.py             # 音频处理
```

## 六、会话与状态

### 6.1 Session Service

| 实现 | 说明 |
|------|------|
| `InMemorySessionService` | 内存存储（开发/测试） |
| `SQLiteSessionService` | SQLite 持久化 |
| `DatabaseSessionService` | 通用数据库（SQLAlchemy） |
| `VertexAISessionService` | Google Vertex AI 托管存储 |

### 6.2 状态管理

- 会话状态 (`State`) 通过 `session.state` 访问
- 支持前缀约定：`temp:` 临时、`app:` 应用级、`user:` 用户级
- 提供 Schema 版本迁移 (v0 → v1)

## 七、记忆与存储

### 7.1 Memory Service

| 实现 | 说明 |
|------|------|
| `InMemoryMemoryService` | 内存向量检索 |
| `VertexAiRagMemoryService` | Vertex AI RAG 服务 |

### 7.2 Artifact Service

| 实现 | 说明 |
|------|------|
| `InMemoryArtifactService` | 内存存储 |
| `GcsArtifactService` | Google Cloud Storage |
| `FileArtifactService` | 本地文件系统 |

## 八、A2A 协议集成

ADK 内置 Agent-to-Agent (A2A) 协议支持，实现跨框架 Agent 互操作。

```
a2a/
├── agent/              # A2A 服务端
│   ├── config.py       # 服务配置
│   └── interceptors/   # 请求拦截器
├── converters/         # ADK ↔ A2A 消息转换
│   ├── from_adk_event.py   # ADK Event → A2A Event
│   ├── to_adk_event.py     # A2A Event → ADK Event
│   ├── part_converter.py   # Part 级转换
│   └── request_converter.py # 请求转换
├── executor/           # A2A 执行器
│   ├── a2a_agent_executor.py    # 执行器接口
│   └── a2a_agent_executor_impl.py # 实现
├── utils/
│   ├── agent_card_builder.py    # Agent Card 构建
│   └── agent_to_a2a.py          # ADK Agent 暴露为 A2A 服务
└── experimental.py     # 实验性功能
```

关键能力：
- **暴露 ADK Agent 为 A2A 服务**：自动生成 Agent Card
- **消费远程 A2A Agent**：`RemoteA2aAgent` 类
- **消息格式转换**：ADK Event ↔ A2A Task/Artifact
- **长运行任务**：支持长时间运行的 Agent 任务
- **Human-in-the-Loop**：A2A 协议中的人工确认

## 九、CLI 工具

```bash
# 开发服务器（热重载）
adk web <agent_dir>

# 运行 Agent
adk run <agent_dir>

# 部署到 Google Cloud
adk deploy <agent_dir>

# 评估 Agent
adk eval <agent_dir> <eval_set.json>

# API 服务器模式
adk api_server <agent_dir>
```

## 十、评估与优化

### 10.1 评估框架

- 内置 `adk eval` 命令
- `.evalset.json` 格式定义测试集
- 支持自动评估和人工评估
- 与 Google Cloud AI Platform 集成

### 10.2 Prompt 优化

- `GEPA` 根 Agent Prompt 优化器
- `SimplePromptOptimizer` 简单优化器
- `AgentOptimizer` Agent 级优化

## 十一、可观测性

- OpenTelemetry 集成
- SQLite Span Exporter（本地开发）
- Google Cloud 遥测
- 指标收集 (`_metrics.py`)

## 十二、设计特色

### 12.1 Pydantic 全量使用

所有核心类（Agent, Tool, Flow, Session 等）均为 Pydantic BaseModel，天然获得：
- 类型验证
- 序列化/反序列化
- Schema 自动生成
- IDE 补全支持

### 12.2 异步优先

- 所有 Agent 执行、LLM 调用均为 `async`
- `AsyncGenerator` 流式输出
- `Aclosing` 上下文管理确保资源释放

### 12.3 回调机制

```python
# Agent 级回调
before_agent_callback / after_agent_callback
# Tool 级回调
before_tool_callback / after_tool_callback
# LLM 级回调
before_model_callback / after_model_callback
```

### 12.4 实验性功能标记

通过 `@experimental(FeatureName.XXX)` 装饰器标记实验性 API，如 `BaseAgentState`（Agent 状态管理）。

## 十三、与其他框架对比

| 特性 | ADK | LangChain | CrewAI | AutoGen |
|------|-----|-----------|--------|---------|
| 维护者 | Google | 社区 | CrewAI | Microsoft |
| Agent 定义 | Python 类 | Chain/Runnable | Python 类 | Python 类 |
| 多模型 | Gemini+Anthropic+LiteLLM | 全模型 | 全模型 | 全模型 |
| A2A 协议 | 原生支持 | 无 | 无 | 无 |
| 内置工具 | 50+ | 200+ | 少 | 少 |
| 评估框架 | 内置 | LangSmith | 无 | 无 |
| 部署 | 内置 CLI | 无 | 无 | 无 |

## 最新动态：ADK 2.0 GA（截至 2026-06-28）

> [!warning] 重大破坏性变更 — 2.0.0 GA（2026-05-19 发布）
> 从 1.x 升级到 2.0 需要迁移。这是 ADK 从"预览"到"生产级"的分水岭。

### 关键变化

| 维度 | 1.x | 2.0 GA |
|------|-----|--------|
| 状态 | Preview | **General Availability（生产级）** |
| 默认模型 | `gemini-2.5-flash` | **`gemini-3-flash-preview`**（破坏性）|
| Agent API | 旧版 | 重构（agent API、event model、session schema 全变）|
| Session 兼容 | — | 2.0 生成的 session 与 1.x **不兼容** |
| 工作流 | 线性为主 | **新增 graph-based workflows**（图式工作流）|
| 多 Agent | 基础 | **新增 collaborative agents**（协作式多 agent）|

### 核心新特性

1. **Graph-based Workflows** — 从线性 pipeline 升级为有向图编排，支持复杂分支/合并/循环
2. **Collaborative Agents** — 多 agent 协作模式原生支持，不再需要手动编排
3. **Agent Modes** — 引入 agent 运行模式概念
4. **生产级基础** — session 持久化、评估、部署 CLI 打磨成熟

### 升级影响

- **向后兼容设计**：官方声明 2.0 设计为"与 1.x agent 兼容"，但 session schema 变了，旧 session 需迁移
- **默认模型切 preview**：这是个争议点——`gemini-3-flash-preview` 是预览模型，生产环境需手动指定 stable 模型
- **文档站迁移**：官方文档从 `google.github.io/adk-docs/` 迁移到 [adk.dev/2.0](https://adk.dev/2.0/)
- **跨语言扩展**：同期 ADK for Java 1.0.0 发布，Kotlin & Android 支持跟进，Google 把 ADK 做成跨语言生态

### 生态信号

- 2026 年社区评测普遍将 ADK 列为"Google 对 LangChain/CrewAI 的官方回应"
- 与 [[a2a-protocol]]、[[multica]] 的集成成为 ADK 2.0 的差异化卖点（原生 A2A + 多 agent 协作）

## 相关链接

- GitHub: https://github.com/google/adk-python
- 文档: https://google.github.io/adk-docs/
- PyPI: https://pypi.org/project/google-adk/
- 关联 [[agentic-rag]]、[[multica]]、[[heuristic-learning]]
