---
title: AutoGen
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [multi-agent, workflow, framework, python, microsoft]
sources:
  - https://github.com/microsoft/autogen
confidence: 0.9
---

# AutoGen

> 微软开源的多 Agent 对话工作流框架 — 对话驱动的 Multi-Agent 协作，异步事件驱动架构。

---

## 一、项目定位

AutoGen 由微软研究院开发（Chi Wang 等人），2023 年开源。核心概念是通过多 Agent 对话完成复杂任务。2024 年底 v0.4 版本进行了重大架构重构，升级为异步事件驱动模型。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 35k+ |
| 许可证 | MIT |
| 语言 | Python |
| 创建者 | Chi Wang（微软研究院） |
| 组织 | Microsoft Research |

定位演进：
- **v0.2** — ConversableAgent + GroupChat，对话驱动
- **v0.4** — 架构重构，AgentChat + Core 分层，异步事件驱动
- **当前** — AgentChat（高层）+ Core（底层）+ Extension（扩展）

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│              AgentChat（高层 API）                     │
│   AssistantAgent · UserProxy · GroupChat · Team       │
├─────────────────────────────────────────────────────┤
│              AutoGen Core（底层引擎）                   │
│   Agent Runtime · Message · Event · Topic            │
│   异步事件驱动 · 单 Agent / 分布式                     │
├─────────────────────────────────────────────────────┤
│              Extensions（扩展）                        │
│   Azure · Docker · LangChain · GraphRAG              │
│   Code Execution · MCP · Web Search                  │
└─────────────────────────────────────────────────────┘
```

| 层 | 包 | 说明 |
|---|---|---|
| 高层 API | `autogen-agentchat` | 预构建 Agent 和 Team |
| 核心引擎 | `autogen-core` | Agent Runtime、消息传递 |
| 扩展 | `autogen-ext` | Azure、Docker、LangChain 等 |
| 旧版 | `autogen` (v0.2) | 向后兼容，不推荐新项目使用 |

## 三、核心架构

### 3.1 v0.4 架构重构

v0.4 是一次根本性重构，从同步对话模型升级为异步事件驱动：

```
v0.2 架构（同步对话）:
  ConversableAgent ←→ ConversableAgent
       ↕ GroupChat（中继）

v0.4 架构（异步事件驱动）:
  ┌──────────────────────────────────────┐
  │          Agent Runtime               │
  │                                      │
  │  Topic A ──→ Agent 1 ──→ Topic B    │
  │                │                     │
  │           Topic C ──→ Agent 2        │
  │                          │           │
  │                     Topic D ──→ ...  │
  └──────────────────────────────────────┘
```

### 3.2 目录结构

```
autogen/
  python/
    packages/
      autogen-core/           — 核心引擎
        src/autogen_core/
          base/               — 基础类型
            agent.py            — BaseAgent
            agent_runtime.py    — SingleThreadedAgentRuntime / DistributedAgentRuntime
            message.py          — Message 基类
            topic.py            — Topic（发布/订阅）
          application/         — 应用层
          components/          — 组件
            tool_provider.py    — 工具提供者
            code_executor.py    — 代码执行器
            model_client.py    — LLM 客户端

      autogen-agentchat/       — 高层 API
        src/autogen_agentchat/
          agents/              — 预构建 Agent
            assistant_agent.py   — AssistantAgent
            code_interpreter_agent.py
            user_proxy_agent.py
          teams/               — 团队编排
            group_chat.py        — GroupChat
            round_robin_group_chat.py
            selector_group_chat.py
            swarm.py            — Swarm 模式
          conditions/          — 终止条件
          messages/            — 消息类型
          ui/                  — UI 集成

      autogen-ext/             — 扩展
        src/autogen_ext/
          models/              — LLM 客户端
            openai_model_client.py
            azure_model_client.py
          tools/               — 工具
          code_executors/      — 代码执行
            docker_executor.py
            local_executor.py
```

### 3.3 Core 层核心概念

**Agent Runtime** — Agent 的执行环境：
- `SingleThreadedAgentRuntime` — 单线程，适合本地开发
- `DistributedAgentRuntime` — 分布式，适合生产部署

**Topic（发布/订阅）** — Agent 间通信：
```python
runtime = SingleThreadedAgentRuntime()

@runtime.register_agent(topic="researcher", agent_type=ResearcherAgent)
@runtime.register_agent(topic="writer", agent_type=WriterAgent)

# Agent 自动订阅 Topic，收到消息后处理
```

**Message** — 类型化消息：
```python
from autogen_core import Message

class ResearchRequest(Message):
    topic: str
    depth: int
```

### 3.4 AgentChat 层

**AssistantAgent** — 最常用的 Agent：
```python
from autogen_agentchat.agents import AssistantAgent

agent = AssistantAgent(
    name="researcher",
    model_client=openai_client,
    tools=[search_tool, web_scraper],
    system_message="你是一个研究助手...",
)
```

**Team 编排模式**：

1. **RoundRobinGroupChat** — 轮流发言
2. **SelectorGroupChat** — 选择器决定下一个发言者
3. **Swarm** — Agent 自主决定是否移交控制权
4. **GroupChat** — 经典群聊模式

```python
from autogen_agentchat.teams import RoundRobinGroupChat, SelectorGroupChat

# 轮流模式
team = RoundRobinGroupChat(
    participants=[agent1, agent2, agent3],
    termination_condition=MaxMessageTermination(10),
)

# 选择器模式
team = SelectorGroupChat(
    participants=[researcher, coder, reviewer],
    selector_model_client=openai_client,
    termination_condition=TextMentionTermination("TERMINATE"),
)
```

### 3.5 终止条件

```python
from autogen_agentchat.conditions import (
    MaxMessageTermination,      # 最大消息数
    TextMentionTermination,     # 文本触发
    TokenUsageTermination,      # Token 用量
    TimeoutTermination,         # 超时
    HandoffTermination,         # Agent 移交
    SourceMatchTermination,     # 来源匹配
    ExternalTermination,        # 外部信号
)
# 可组合：condition1 | condition2（OR）, condition1 & condition2（AND）
```

## 四、关键特性

### 4.1 代码执行

- **Docker 隔离** — 在容器中安全执行代码
- **本地执行** — 开发环境直接执行
- **Jupyter 内核** — 支持 IPython 内核执行

### 4.2 工具系统

```python
from autogen_core import FunctionTool

def search_web(query: str, max_results: int = 5) -> str:
    """搜索网页"""
    ...

search_tool = FunctionTool(search_web, description="搜索网页")
```

### 4.3 MCP 支持

v0.4 支持 Model Context Protocol：
```python
from autogen_ext.tools.mcp import McpWorkbench

workbench = McpWorkbench(config)
tools = await workbench.list_tools()
```

### 4.4 可观测性

- OpenTelemetry 集成
- 内置 Trace 和 Logging
- Agent 交互可视化

## 五、关键设计决策

1. **异步事件驱动** — v0.4 根本性重构为异步模型，支持分布式部署
2. **分层设计** — Core（底层引擎）+ AgentChat（高层 API），各层独立演进
3. **Topic 发布/订阅** — Agent 间通过 Topic 解耦，天然支持一对多通信
4. **Swarm 模式** — Agent 自主移交控制权，无需中央调度器
5. **微软生态深度集成** — Azure OpenAI、Semantic Kernel、GraphRAG

## 六、开发命令速查

```bash
# 安装 v0.4
pip install autogen-agentchat autogen-ext
pip install autogen-ext[openai]

# 安装旧版 v0.2（不推荐）
pip install autogen

# 开发（从源码）
git clone https://github.com/microsoft/autogen.git
cd autogen/python
pip install -e packages/autogen-core
pip install -e packages/autogen-agentchat
pip install -e packages/autogen-ext

# 测试
pytest packages/autogen-core/tests
pytest packages/autogen-agentchat/tests
```

## 七、与竞品对比

| 维度 | AutoGen | [[langchain]] LangGraph | [[crew-ai]] |
|------|---------|------------------------|-------------|
| 核心概念 | 对话+Topic | StateGraph | Agent+Task+Crew |
| 架构 | 异步事件驱动 | Pregel 图模型 | 同步顺序/层级 |
| 分布式 | 原生支持 | 需 LangGraph Cloud | 不支持 |
| 学习曲线 | 中等 | 陡峭 | 平缓 |
| 生态 | 微软生态 | 700+ 集成 | LangChain 兼容 |
| 代码执行 | Docker 原生 | 需外部工具 | 内置 |

---

## 相关

- [[langchain]] — LLM 应用框架
- [[crew-ai]] — 多 Agent 协作框架
- [[dify]] — 可视化 LLMOps 平台
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
