---
title: CrewAI
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [multi-agent, workflow, framework, python]
sources:
  - https://github.com/crewAIInc/crewAI
confidence: 0.9
---

# CrewAI

> 多 Agent 协作工作流框架 — 模拟人类团队协作，角色化 Agent 定义，简洁 API 换取高易用性。

---

## 一、项目定位

CrewAI 由 João Moura 于 2023 年创建，核心理念是模拟人类团队协作方式构建 AI Agent 系统。通过定义 Agent（角色）、Task（任务）、Crew（团队）和 Process（流程），快速搭建多 Agent 协作工作流。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 20k+ |
| 许可证 | MIT |
| 语言 | Python |
| 创建者 | João Moura |
| 公司 | CrewAI Inc. |

定位：
- **高层抽象** — 不暴露图/节点/边等底层概念
- **角色驱动** — Agent = 角色 + 目标 + 背景故事
- **团队协作** — Crew 组织多个 Agent 完成复杂任务
- **LangChain 兼容** — 可复用 LangChain 的 LLM 和工具

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                 应用层                                │
│   Crew · Flow · Pipeline                             │
├─────────────────────────────────────────────────────┤
│              CrewAI Core                             │
│   Agent · Task · Process · Tool · Memory             │
│   LLM · Planner · Reasoning                         │
├─────────────────────────────────────────────────────┤
│              集成层                                   │
│   LangChain Tools · 任何 Python 函数 · MCP           │
│   50+ 内置工具 · 自定义工具                           │
├─────────────────────────────────────────────────────┤
│              LLM 层                                  │
│   OpenAI · Anthropic · Google · Ollama · AWS · ...   │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 核心框架 | `crewai` | Agent/Task/Crew/Process/Tool |
| 企业版 | `crewai-enterprise` | 托管平台（商业） |
| 工具集 | `crewai-tools` | 50+ 内置工具 |
| LLM | LiteLLM | 统一 LLM 接口，支持所有主流供应商 |
| 流程引擎 | Sequential / Hierarchical | 任务执行模式 |

## 三、核心架构

### 3.1 四大核心概念

```
┌──────────────────────────────────────┐
│                Crew                   │
│  （团队：组织 Agent + Task）           │
│                                      │
│  ┌─────────┐  ┌─────────┐           │
│  │ Agent A │  │ Agent B │           │
│  │ 角色:研究员│  │ 角色:写手 │           │
│  └────┬────┘  └────┬────┘           │
│       │            │                  │
│  ┌────▼────┐  ┌────▼────┐           │
│  │ Task 1  │──│ Task 2  │           │
│  │ 调研任务 │  │ 写作任务 │           │
│  └─────────┘  └─────────┘           │
│                                      │
│  Process: sequential / hierarchical  │
└──────────────────────────────────────┘
```

### 3.2 目录结构

```
crewai/
  src/crewai/
    agent.py              — Agent 定义
    task.py               — Task 定义
    crew.py               — Crew 定义（编排器）
    process/              — 执行流程
      process.py            — Process 基类
      sequential.py         — 顺序执行
      hierarchical.py       — 层级执行（Manager Agent）
    tools/                — 工具系统
      base_tool.py          — BaseTool
      tool_usage.py         — 工具调用解析
    llm.py                — LLM 抽象（基于 LiteLLM）
    memory/               — 记忆系统
      short_term_memory.py  — 短期记忆
      long_term_memory.py   — 长期记忆
      entity_memory.py      — 实体记忆
    knowledge/            — 知识管理
    planning/             — 任务规划
    reasoning/            — 推理引擎
    utilities/            — 工具函数
```

### 3.3 Agent 定义

```python
from crewai import Agent

researcher = Agent(
    role="高级研究员",
    goal="发现关于 {topic} 的突破性技术",
    backstory="你是一位在 AI 领域有 20 年经验的研究员...",
    tools=[search_tool, scrape_tool],
    llm="gpt-4o",
    memory=True,
    verbose=True,
    allow_delegation=False,
    max_iter=25,
)
```

Agent 配置项：
- `role` / `goal` / `backstory` — 角色定义三要素
- `tools` — 可用工具列表
- `llm` — 使用的 LLM
- `memory` — 是否启用记忆
- `allow_delegation` — 是否可委派任务给其他 Agent
- `max_iter` — 最大推理迭代次数
- `verbose` — 详细输出
- `reasoning` — 推理模式（2025 新增）

### 3.4 Task 定义

```python
from crewai import Task

research_task = Task(
    description="研究 {topic} 的最新进展",
    expected_output="一份包含 10 个要点的研究报告",
    agent=researcher,
    output_file="report.md",
    callback=callback_func,
)
```

Task 特性：
- 可指定 Agent 或由 Crew Manager 分配
- 支持异步执行
- 支持输出到文件
- 支持 callback 回调
- 支持上下文依赖（`context=[task1, task2]`）

### 3.5 Crew 定义

```python
from crewai import Crew, Process

crew = Crew(
    agents=[researcher, writer],
    tasks=[research_task, write_task],
    process=Process.sequential,  # 或 Process.hierarchical
    memory=True,
    verbose=True,
    planning=True,  # 启用任务规划
)

result = crew.kickoff(inputs={"topic": "AI Agents"})
```

### 3.6 Process 模式

**Sequential（顺序）**：
```
Agent A → Task 1 → Agent B → Task 2 → Agent C → Task 3
```

**Hierarchical（层级）**：
```
          Manager Agent
         /     |      \
    Agent A  Agent B  Agent C
        │       │       │
    Task 1   Task 2   Task 3
```

Manager Agent 自动创建，负责：
- 任务分解和分配
- 验证输出质量
- 请求重做
- 最终汇总

### 3.7 Flow（v0.80+ 新增）

2025 年推出 Flow 概念，支持更灵活的工作流编排：

```python
from crewai import Flow, start, listen, router

class ResearchFlow(Flow):
    @start()
    def init(self):
        return "begin"

    @listen("init")
    def research(self, state):
        return research_crew.kickoff()

    @router("research")
    def route(self, result):
        if result.quality > 0.8:
            return "approve"
        return "revise"

    @listen("approve")
    def finalize(self, result):
        return final_report
```

Flow 特性：
- `@start()` — 入口方法
- `@listen()` — 监听事件
- `@router()` — 条件路由
- 支持并行分支
- 支持循环
- 状态持久化

## 四、关键特性

### 4.1 50+ 内置工具

| 类别 | 工具 |
|------|------|
| 搜索 | SerperDev、Serper、Tavily |
| 浏览器 | ScrapeWebsite、Selenium |
| 文件 | FileReader、CSVSearch、JSONSearch |
| 数据库 | SQLDatabase、MySQL、PostgreSQL |
| 代码 | CodeInterpreter、Docker |
| AI | DALL-E、StableDiffusion |
| 通信 | Slack、Email |

### 4.2 记忆系统

- **Short Term Memory** — 当前会话上下文
- **Long Term Memory** — 跨会话持久化（RAG 检索）
- **Entity Memory** — 实体知识提取和存储
- **Contextual Memory** — 任务间上下文传递

### 4.3 知识管理

```python
from crewai.knowledge.source.string_knowledge_source import StringKnowledgeSource

content = "公司成立于2020年，主要产品是..."
knowledge = StringKnowledgeSource(content=content)

crew = Crew(
    agents=[agent],
    tasks=[task],
    knowledge_sources=[knowledge],
)
```

### 4.4 企业版特性

- CrewAI Enterprise 托管平台
- 云端部署和运行
- API 管理和监控
- 团队协作

## 五、关键设计决策

1. **角色化而非图结构** — Agent 通过角色/目标/背景故事定义，而非节点/边，降低学习门槛
2. **简洁 API 优先** — 5 行代码可以跑起来一个 Multi-Agent 系统
3. **LiteLLM 统一接口** — 不绑定任何 LLM 供应商
4. **Flow 弥补灵活性** — v0.80 引入 Flow 概念，在简洁和灵活间取平衡
5. **LangChain 工具复用** — 不重复造工具轮子，直接复用 LangChain 生态

## 六、开发命令速查

```bash
# 安装
pip install crewai crewai-tools

# 或使用 UV（推荐）
uv add crewai crewai-tools

# 创建项目
crewai create crew my-crew
cd my-crew
crewai run

# 开发（从源码）
git clone https://github.com/crewAIInc/crewAI.git
cd crewAI
pip install -e .
pip install -e ./crewai-tools

# 测试
pytest tests/
```

## 七、与竞品对比

| 维度 | CrewAI | [[langchain]] LangGraph | [[auto-gen]] | [[dify]] |
|------|--------|------------------------|--------------|----------|
| 核心概念 | Agent+Task+Crew | StateGraph+Node+Edge | ConversableAgent | 可视化拖拽 |
| 学习曲线 | 平缓 | 陡峭 | 中等 | 平缓 |
| 灵活性 | 低-中 | 高 | 中 | 中 |
| 代码量 | 少 | 多 | 中 | 无代码 |
| Multi-Agent | 原生支持 | 原生支持 | 原生支持 | 原生支持 |
| 目标用户 | 快速原型/中小项目 | 复杂生产级 | 企业/微软生态 | 非技术人员 |

---

## 相关

- [[langchain]] — LLM 应用框架（工具复用生态）
- [[auto-gen]] — 微软 Multi-Agent 框架
- [[dify]] — 可视化 LLMOps 平台
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
