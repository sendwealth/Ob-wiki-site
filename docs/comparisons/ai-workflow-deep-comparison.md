---
title: AI Workflow 开源项目深度对比分析
created: 2026-06-03
updated: 2026-06-03
type: comparison
tags: [ai-workflow, llm, agent, mlops, orchestration, comparison, architecture]
sources:
  - https://github.com/langchain-ai/langchain
  - https://github.com/run-llama/llama_index
  - https://github.com/crewAIInc/crewAI
  - https://github.com/microsoft/autogen
  - https://github.com/langgenius/dify
  - https://github.com/FlowiseAI/Flowise
  - https://github.com/langflow-ai/langflow
  - https://github.com/n8n-io/n8n
  - https://github.com/labring/FastGPT
  - https://github.com/apache/airflow
  - https://github.com/PrefectHQ/prefect
  - https://github.com/temporalio/temporal
  - https://github.com/dagster-io/dagster
  - https://github.com/kestra-io/kestra
  - https://github.com/argoproj/argo-workflows
  - https://github.com/kubeflow/kubeflow
  - https://github.com/mlflow/mlflow
  - https://github.com/Netflix/metaflow
  - https://github.com/flyteorg/flyte
  - https://github.com/zenml-io/zenml
confidence: 0.85
---

# AI Workflow 开源项目深度对比分析

> 20 个主流开源项目的架构哲学、设计权衡与选型逻辑——不只是功能清单，而是理解它们为什么这样设计。

---

## 一、分类再审视：四层架构栈

传统分类把项目按"功能"分组（LLM 框架、低代码平台、编排引擎、ML 平台），但这种分类掩盖了一个更本质的差异：**它们在 AI 工作流技术栈中处于不同层级，解决不同抽象层次的问题**。

```
┌─────────────────────────────────────────────────────────────┐
│  Layer 4: 应用层                                             │
│  用户直接交互的产品：[[dify]] [[fast-gpt]] [[n8n]]             │
│  特征：可视化 UI 为主，非技术人员可用                            │
├─────────────────────────────────────────────────────────────┤
│  Layer 3: Agent 框架层                                       │
│  构建 AI Agent 的编程框架：[[langchain]] [[llama-index]]       │
│  [[crew-ai]] [[auto-gen]] [[flowise]] [[langflow]]           │
│  特征：Python/JS API 为主，开发者直接编码                        │
├─────────────────────────────────────────────────────────────┤
│  Layer 2: 编排引擎层                                         │
│  通用任务调度与编排：[[apache-airflow]] [[prefect]] [[dagster]] │
│  [[temporal]] [[kestra]] [[argo-workflows]]                  │
│  特征：不感知 LLM，编排任意计算任务                               │
├─────────────────────────────────────────────────────────────┤
│  Layer 1: 基础设施层                                         │
│  ML 生命周期管理 & K8s 运行时：[[mlflow]] [[kubeflow]]          │
│  [[metaflow]] [[flyte]] [[zenml]]                            │
│  特征：与云/集群深度绑定，关注资源/版本/部署                        │
└─────────────────────────────────────────────────────────────┘
```

关键洞察：**不同层之间是互补关系而非竞争关系**。生产级 AI 系统通常跨层组合——用 Layer 3 的 [[langchain]] 构建 Agent 逻辑，用 Layer 2 的 [[temporal]] 保证可靠执行，用 Layer 1 的 [[mlflow]] 追踪实验。

---

## 二、架构哲学的三个根本分歧

在 20 个项目中，存在三个根本性的设计分歧，这些分歧比功能差异更深刻地决定了项目的适用场景。

### 分歧一：工作流定义方式——声明式 vs 命令式

```
声明式（What）                    命令式（How）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
YAML 描述期望状态                  Python 代码描述执行步骤
解析器推导执行计划                  代码即执行计划
结构运行前确定                     结构运行时确定
Git 友好                          IDE 友好

[[argo-workflows]]               [[langchain]] LangGraph
[[kestra]]                        [[prefect]]
[[apache-airflow]](DAG 部分)      [[crew-ai]]
                                  [[metaflow]]
```

这不是简单的优劣问题：

| 维度 | 声明式 | 命令式 |
|------|--------|--------|
| 可审查性 | 高（YAML/JSON 可视化审查） | 低（需读代码逻辑） |
| 动态性 | 低（结构运行前固定） | 高（循环/条件运行时决定） |
| 版本控制 | 天然友好（文本 diff） | 友好（代码 diff） |
| AI Agent 适配 | 差（Agent 行为不可预测） | 好（Agent 自主决定下一步） |
| 学习曲线 | 中等（需学 DSL） | 低（就是写代码） |

**结论**：构建 AI Agent 工作流，命令式几乎是必选项——Agent 的核心特征就是运行时自主决策，这天然与声明式冲突。[[argo-workflows]] 和 [[kestra]] 适合确定性 Pipeline，不适合自主 Agent。

### 分歧二：抽象层次——高层封装 vs 低级控制

```
高层封装（Convention over Configuration）     低级控制（Power user first）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
5 行代码跑起 Agent                          手动定义每个节点和边
约定大于配置                                 显式声明一切
灵活度低，上手快                              灵活度高，上手慢
容易碰天花板                                 天花板极高

[[crew-ai]]                                 [[langchain]] LangGraph
[[dify]](可视化模式)                          [[auto-gen]] Core
[[fast-gpt]]                                 [[temporal]]
                                            [[argo-workflows]]
```

[[crew-ai]] 是高层封装的典型：定义 Agent 的角色/目标/背景故事，Crew 自动编排。代价是当你的 Agent 协作模式不在预设模板内时，需要绕路。

[[langchain]] LangGraph 是低级控制的典型：手动定义每个节点函数、每条边（含条件边），状态图完全由你控制。代价是 100 行代码才能搭起一个 Multi-Agent 系统。

**选型原则**：原型阶段用高层封装快速验证，生产阶段用低级控制精确调优。两者不矛盾——[[crew-ai]] 和 [[langchain]] 本身就兼容，可以在 Crew 内部调用 LangChain 工具。

### 分歧三：执行保证——尽力而为 vs 持久化保证

```
尽力而为（Best-effort）               持久化保证（Durable）
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
进程崩溃 = 状态丢失                     进程崩溃 = 自动恢复
重试是附加功能                           重试是架构基础
适合秒级/分钟级任务                      适合分钟级/天级/月级任务

[[langchain]]                          [[temporal]]
[[crew-ai]]                            [[argo-workflows]](K8s 重启)
[[prefect]](默认)                      [[prefect]](with TaskRunner)
[[dify]]                               [[dagster]](with daemon)
```

这是最容易被忽视但影响最深的分歧。

[[temporal]] 的持久化保证来自事件溯源（Event Sourcing）——每个 Workflow 的每个动作都记录为不可变事件，崩溃后通过重放事件历史恢复状态。这意味着一个跑了一周的 AI Agent 任务，服务器重启后能从断点继续，不丢进度。

[[langchain]] LangGraph 的 Checkpointer 也提供状态持久化（MemorySaver / SqliteSaver / PostgresSaver），但这是附加层，不是架构基础。如果 Checkpointer 写入失败，状态可能丢失。

**选型原则**：如果工作流涉及金钱/合规/长时间计算（模型训练、数据标注、合规审核），持久化保证是硬需求，[[temporal]] 或 [[argo-workflows]] 是正确选择。如果是快速 Agent 循环（Chat、RAG 问答），尽力而为足够。

---

## 三、六大核心维度横向对比

### 3.1 Multi-Agent 编排模式

20 个项目中，只有 6 个原生支持 Multi-Agent，但它们的编排哲学截然不同：

| 项目 | 编排模型 | Agent 间通信 | 动态性 | 适用规模 |
|------|----------|-------------|--------|---------|
| [[langchain]] LangGraph | 状态图（Pregel） | 共享 State | 高 | 中-大 |
| [[auto-gen]] | Topic 发布/订阅 | 异步事件 | 最高 | 大（分布式） |
| [[crew-ai]] | 顺序/层级 | 任务链 | 低 | 小-中 |
| [[dify]] | 可视化 DAG | 节点输出传递 | 中 | 小-中 |
| [[n8n]] | 节点连线 | 节点输出传递 | 中 | 小-中 |
| [[temporal]] | 信号/查询 | 异步消息 | 高 | 大 |

三种编排哲学：

**1. 共享状态模型**（[[langchain]] LangGraph）
```
所有节点读写同一个 State 字典
State = TypedDict 或 Pydantic Model
节点函数：State → State（纯变换）
```
优点：简单直观，调试方便。缺点：State 膨胀风险，并发写入需合并策略。

**2. 消息传递模型**（[[auto-gen]]、[[temporal]]）
```
Agent 间通过 Topic/Signal 异步通信
每个 Agent 有独立状态
解耦彻底，天然支持分布式
```
优点：松耦合，可独立部署。缺点：调试链路长，消息丢失需处理。

**3. 流水线模型**（[[crew-ai]]、[[dify]]）
```
Agent A 完成任务 → 传递给 Agent B → 传递给 Agent C
顺序或层级（Manager 分配）
```
优点：简单易懂。缺点：灵活度低，难以表达复杂交互。

### 3.2 RAG 能力深度

| 项目 | RAG 深度 | 数据源 | 检索策略 | 分片策略 | 重排序 |
|------|---------|--------|---------|---------|--------|
| [[llama-index]] | 最深 | 160+ 连接器 | 5+ 高级模式 | 多种 | 支持 |
| [[dify]] | 深 | 内置 10+ | 混合检索 | 自动/自定义 | 支持 |
| [[fast-gpt]] | 深 | 内置 10+ | 向量/混合 | 自动 | 有限 |
| [[langchain]] | 中 | 700+ 集成 | 基础+高级 | 多种 | 支持 |
| [[n8n]] | 浅 | 节点组装 | 需自建 | 需自建 | 需自建 |
| 其他 | 无/极浅 | — | — | — | — |

[[llama-index]] 在 RAG 深度上无可匹敌——5 种高级检索模式（Sentence Window、Auto-Merging、Recursive、Multi-Document Agent、Self-RAG），这不是锦上添花，而是生产级 RAG 系统必需的。基础向量检索在真实场景中召回率通常不足 60%，高级模式才能拉到 85%+。

[[dify]] 和 [[fast-gpt]] 的 RAG 是开箱即用的——上传文档、选择分片策略、一键部署问答机器人。牺牲了深度换取易用性。

### 3.3 可观测性

| 项目 | Trace | 评估 | Dashboard | 告警 | 商业化 |
|------|-------|------|-----------|------|--------|
| [[langchain]] LangSmith | 最强 | 强 | 强 | 支持 | SaaS |
| [[mlflow]] | 强 | 强（LLM 评估） | 强 | 支持 | 开源 |
| [[prefect]] | 强 | — | 内置 | 强 | SaaS |
| [[dagster]] | 中 | — | 强（Dagit） | 中 | SaaS |
| [[temporal]] | 强 | — | 内置 | 支持 | SaaS |
| [[dify]] | 中 | — | 内置 | 有限 | SaaS+开源 |
| [[crew-ai]] | 弱 | — | 弱 | — | SaaS |
| [[apache-airflow]] | 中 | — | 内置 | 强 | 开源 |

可观测性是生产级系统的命脉。[[langchain]] 的 LangSmith 之所以重要，不只是因为 Trace 可视化，更因为它的评估框架——能自动化评估 Agent 输出质量，这是从"能用"到"可靠"的关键一步。

[[mlflow]] 的 Tracing（2024 新增）正在追赶 LangSmith，优势是开源且与实验追踪统一。劣势是 Agent 追踪的深度不如 LangSmith。

### 3.4 部署复杂度

```
简单 ←——————————————————————————————→ 复杂

[[flowise]]  pip install → npx start     [[kubeflow]]     K8s 集群 + Helm + 多组件
[[fast-gpt]] docker-compose up           [[argo-workflows]] K8s + CRD + S3
[[n8n]]      docker run → 访问 5678       [[flyte]]         K8s + Helm + Go 服务
[[dify]]     docker-compose up           [[temporal]]       K8s/Helm + Cassandra/PG
[[mlflow]]   pip install → mlflow ui     [[dagster]]        daemon + PostgreSQL
```

部署复杂度直接关联运维成本。一个 3 人团队用 [[kubeflow]] 需要 1 个人全职维护基础设施；同样的团队用 [[dify]] 只需要 0.2 个人力。

**但要注意**：部署复杂度和能力天花板正相关。[[flowise]] 部署最简单，但碰到的天花板也最低——没有多租户、没有水平扩展、没有企业级安全。

### 3.5 数据传递模型

工作流节点间如何传递数据，深刻影响系统设计：

| 模型 | 代表项目 | 机制 | 大数据支持 | 延迟 |
|------|---------|------|-----------|------|
| 内存传递 | [[langchain]]、[[crew-ai]] | Python 对象引用 | 差（受内存限制） | 最低 |
| 数据库传递 | [[apache-airflow]] XCom | 元数据库 | 差（<48KB 限制） | 中 |
| 文件传递 | [[argo-workflows]] | S3/GCS Artifact | 好 | 中 |
| IO Manager | [[dagster]] | 可插拔存储抽象 | 好 | 中 |
| 事件溯源 | [[temporal]] | 不可变事件日志 | 中 | 中 |
| 对象存储 | [[flyte]] | S3/GCS 原始数据 | 最好 | 中 |

AI 工作流的数据传递特殊性在于：**LLM 的输入/输出主要是文本（KB 级），但训练/推理 Pipeline 的中间数据可能是模型权重（GB 级）**。

- LLM Agent 工作流（[[langchain]]、[[crew-ai]]）：内存传递足够，因为数据量小
- ML 训练 Pipeline（[[argo-workflows]]、[[flyte]]）：必须用文件/对象存储，因为模型权重可能数 GB
- 混合场景（[[dagster]]）：IO Manager 抽象可以根据 Asset 大小自动选择存储策略

### 3.6 学习曲线 vs 天花板

```
天花板
  ↑
  │                          ╭─── [[langchain]] LangGraph
  │                     ╭───│──── [[auto-gen]] Core
  │                ╭───│────│──── [[temporal]]
  │           ╭───│────│────│──── [[argo-workflows]]
  │      ╭───│────│────│────│──── [[dagster]]
  │ ╭───│────│────│────│────│──── [[prefect]]
  ││────│────│────│────│────│──── [[mlflow]]（追踪维度）
  │┤────│────│────│────│────│──── [[kubeflow]]
  ││    │    │    │    │    │
  │[[dify]]                    │
  │[[fast-gpt]]                │
  │[[n8n]]                     │
  │[[flowise]]                 │
  │[[crew-ai]]                 │
  │[[kestra]]                  │
  └──────────────────────────────→ 学习曲线
  平缓                           陡峭
```

关键规律：**学习曲线和天花板正相关，但不是线性关系**。

[[crew-ai]] 的学习曲线极平缓（5 行代码），但天花板也低（非标准协作模式需要绕路）。[[temporal]] 学习曲线陡峭（事件溯源 + 确定性约束），但天花板极高（百万级并发 Workflow、跨月持久执行）。

[[langchain]] 处于有趣的中间位置：基础用法（Chain + Agent）学习曲线平缓，但 LangGraph 的图编排拉高了曲线，同时也显著提高了天花板。这种分层设计是优秀的架构选择。

---

## 四、五组典型竞品深度对比

### 4.1 LangChain vs LlamaIndex — 互补而非替代

这是被最多人误解的一组对比。两者不是竞品，而是互补：

| 维度 | [[langchain]] | [[llama-index]] |
|------|-------------|----------------|
| 核心抽象 | Chain → Agent → Graph | Document → Index → Retriever |
| 数据层 | 700+ 集成（广） | 160+ 数据连接器（深） |
| RAG 深度 | 中等（需手拼高级模式） | 最深（5+ 高级模式开箱即用） |
| Agent 灵活度 | 高（LangGraph 图编排） | 中（Workflow 引擎） |
| 典型用途 | 构建 Agent 逻辑 | 构建数据管线 + RAG |

最佳实践：**用 LlamaIndex 构建 RAG 管线（数据摄取→索引→检索），用 LangChain/LangGraph 编排 Agent 逻辑（规划→工具调用→决策循环）**。两者共享底层 LLM 接口，天然可组合。

```
用户查询
    ↓
┌─────────────────────────────────┐
│ LangGraph Agent（决策循环）       │
│   ┌─── 规划 ───┐               │
│   │  需要检索？  │──是──→ LlamaIndex RAG
│   └─── ↓否 ───┘               │
│   直接调用 LLM                   │
└─────────────────────────────────┘
```

### 4.2 CrewAI vs AutoGen — 高层 vs 底层 Multi-Agent

| 维度 | [[crew-ai]] | [[auto-gen]] |
|------|-----------|-------------|
| 抽象层次 | 高（角色+团队+流程） | 低（Agent+Topic+Event） |
| 5 行代码能做什么 | 跑起一个 3 Agent 团队 | 几乎什么都没做 |
| 50 行代码能做什么 | 已碰到天花板 | 刚热身完毕 |
| 分布式 | 不支持 | 原生支持 |
| 灵活度 | 低（3 种预设流程） | 高（自由拓扑） |

**场景选择**：
- "3 个 Agent 协作写一份报告" → [[crew-ai]]，10 分钟搞定
- "10 个 Agent 分布式协作，需要消息广播、故障恢复、人工介入" → [[auto-gen]]，1 周搭建

### 4.3 Dify vs FastGPT — 国内双雄

| 维度 | [[dify]] | [[fast-gpt]] |
|------|---------|-------------|
| 核心定位 | AI 全栈开发平台 | 知识库问答平台 |
| 工作流复杂度 | 高（12+ 节点类型） | 中（基础节点） |
| 模型兼容 | 100+（国际+国产） | 10+（重点国产） |
| 多租户 | 原生 | 原生 |
| 数据库 | PostgreSQL | MongoDB |
| 商业化 | 国际化 | 国内为主 |
| 开源社区 | 活跃（国际化） | 活跃（国内） |

**关键差异**：[[dify]] 的核心是工作流引擎——它想成为 AI 时代的"低代码应用平台"。[[fast-gpt]] 的核心是知识库——它想成为"最好的 AI 知识库问答产品"。

选 [[dify]] 如果你需要：复杂工作流、多应用管理、团队协作、国际化部署。
选 [[fast-gpt]] 如果你需要：快速搭建知识库问答、国产模型适配、MongoDB 技术栈。

### 4.4 Airflow vs Prefect vs Dagster — 编排三杰

这是最经典的编排器对比，三者代表了三种哲学：

| 维度 | [[apache-airflow]] | [[prefect]] | [[dagster]] |
|------|-------------------|-------------|-------------|
| 中心概念 | DAG + Operator | Flow + Task | Asset + Job |
| 核心哲学 | 任务为中心 | 代码为中心 | 数据为中心 |
| 动态性 | 静态（解析时确定） | 动态（运行时） | 动态（运行时） |
| 数据传递 | XCom（<48KB） | Python 返回值 | IO Manager |
| 血缘追踪 | 无原生支持 | 有限 | 原生最强 |
| ML 友好度 | 中（需适配） | 良好 | 最好（资产=模型） |

**选择逻辑**：

```
你的数据团队主要做什么？
    │
    ├── ETL / 批处理 → Airflow（最成熟，1000+ Provider）
    │
    ├── Python 原生工作流 → Prefect（最简单，增量采纳）
    │
    └── ML Pipeline / 数据产品 → Dagster（资产思维，血缘追踪）
```

一个常被忽略的细节：[[dagster]] 的 Asset 抽象天然映射 ML Pipeline——"数据集→特征→模型→评估→部署"每个环节都是一个 Asset，Dagit UI 自动绘制血缘图。Airflow 和 Prefect 要实现同等效果需要大量手动配置。

### 4.5 Argo Workflows vs Temporal — K8s 原生 vs 语言原生

| 维度 | [[argo-workflows]] | [[temporal]] |
|------|-------------------|-------------|
| 执行模型 | K8s Pod | 用户进程（Worker） |
| 定义方式 | YAML CRD | 代码（Go/Java/Python/TS） |
| 持久化 | K8s etcd + S3 | Cassandra/PostgreSQL + 事件溯源 |
| 故障恢复 | Pod 重启 + 重试 | 事件重放（确定性恢复） |
| 适用语言 | 容器内任意语言 | SDK 支持的语言 |
| 冷启动 | 中（Pod 调度 ~秒级） | 低（Worker 常驻） |
| GPU | 原生（K8s Device Plugin） | 需自定义 |

这是两种完全不同的执行哲学：

**Argo 的哲学**：每个任务是一个容器。容器是隔离单元、调度单元、计费单元。K8s 管一切。

**Temporal 的哲学**：每个任务是一段代码。代码是逻辑单元、状态单元、演进单元。平台管可靠性。

**选 Argo 如果**：你已经在 K8s 生态中、需要 GPU 调度、任务间隔离要求高（训练任务）。
**选 Temporal 如果**：你需要微秒级任务调度、长时运行的 Agent 编排、跨服务的工作流协调。

---

## 五、组合架构：生产级 AI 系统怎么搭

单一项目几乎无法覆盖生产级 AI 系统的全部需求。以下是三种验证过的组合架构：

### 架构 A：AI Agent SaaS（中小团队）

```
┌─────────────────────────────────────────────┐
│              [[dify]]（前端 + 编排）            │
│   可视化构建 → 发布为 API/嵌入                   │
├─────────────────────────────────────────────┤
│   [[langchain]]（Agent 逻辑）                  │
│   [[llama-index]]（RAG 管线）                  │
├─────────────────────────────────────────────┤
│   PostgreSQL + Redis + Milvus/PGVector       │
└─────────────────────────────────────────────┘
```

特点：Docker Compose 一键部署，3 人团队可维护，适合内部工具和 SaaS 产品。

### 架构 B：企业级 AI 平台（大团队）

```
┌─────────────────────────────────────────────┐
│   [[apache-airflow]] 或 [[prefect]]（调度）     │
├─────────────────────────────────────────────┤
│   [[langchain]]（Agent 逻辑）                  │
│   [[mlflow]]（实验追踪 + 模型注册）              │
├─────────────────────────────────────────────┤
│   K8s + Helm + S3 + PostgreSQL               │
└─────────────────────────────────────────────┘
```

特点：编排器统一调度 AI 和非 AI 任务，MLflow 追踪所有实验，适合已有 Airflow 基础设施的数据团队。

### 架构 C：K8s 原生 ML 平台（基础设施团队）

```
┌─────────────────────────────────────────────┐
│   [[kubeflow]] Pipelines（ML Pipeline）        │
│   [[argo-workflows]]（底层编排）                │
├─────────────────────────────────────────────┤
│   [[mlflow]]（实验追踪）                        │
│   KServe（模型推理）                            │
│   Katib（超参数调优）                           │
├─────────────────────────────────────────────┤
│   K8s + GPU + S3 + Istio                     │
└─────────────────────────────────────────────┘
```

特点：GPU 原生、分布式训练、模型推理一体化，适合有 K8s 运维能力的基础设施团队。

---

## 六、2025-2026 趋势判断

### 趋势一：Agent 原生工作流正在吞噬传统编排

2024 年之前，AI 工作流 = 传统编排器 + LLM 调用步骤。2025 年之后，Agent 原生工作流（[[langchain]] LangGraph、[[auto-gen]]、[[crew-ai]]）正在重新定义编排——Agent 自主决策下一步，而非由 DAG 预定义。

这并不意味着传统编排器会消亡——批处理、ETL、定时调度仍有需求。但 **新增的 AI 工作流需求，首选 Agent 原生框架**。

### 趋势二：RAG 从功能变为基础设施

早期 RAG 是框架的一个功能（LangChain 的 Retriever、LlamaIndex 的 Index）。现在 RAG 正在变为独立基础设施层——[[dify]] 和 [[fast-gpt]] 的知识库管理本质上就是 RAG 基础设施化。

[[llama-index]] 的 Workflow 引擎是这个趋势的早期信号——RAG 不再是"检索-生成"两步，而是多步迭代、自我评估、动态路由的复杂管线。

### 趋势三：可观测性从附加功能变为核心卖点

LangSmith 的成功证明：AI 工作流的瓶颈不是"能不能跑起来"，而是"跑起来之后怎么保证质量"。

[[mlflow]] 在 2024 年新增 Tracing 和 LLM Evaluate，[[prefect]] 的内置 Dashboard，[[dagster]] 的 Dagit 血缘图——都在向同一个方向演进：**AI 工程的可观测性正在成为平台级能力**。

### 趋势四：低代码平台的边界在收窄

[[flowise]] 和 [[langflow]] 面临一个根本困境：低代码用户想要的是"不需要写代码"，但 LLM 应用的复杂度（Prompt 工程、评估、调试）天然需要代码级控制。

[[dify]] 的策略更聪明——提供可视化编排作为入口，但保留代码级扩展（HTTP 节点、代码节点、API 调用）。这使得它既能服务非技术人员，又不让开发者碰到天花板。

---

## 七、选型决策树

```
你的核心需求是什么？
│
├── 构建 AI Agent / LLM 应用
│   ├── 需要可视化？ → [[dify]]
│   ├── 需要最灵活的 Agent 编排？ → [[langchain]] + LangGraph
│   ├── 需要快速原型？ → [[crew-ai]]
│   ├── 需要分布式 Agent？ → [[auto-gen]]
│   └── 需要 RAG？ → + [[llama-index]]
│
├── AI + 业务系统自动化
│   ├── 400+ 第三方集成？ → [[n8n]]
│   └── 只需基础集成？ → [[dify]]
│
├── ML Pipeline 编排
│   ├── 已有 K8s 集群？
│   │   ├── 需要完整 ML 平台？ → [[kubeflow]]
│   │   ├── 只需工作流引擎？ → [[argo-workflows]]
│   │   └── 需要强类型？ → [[flyte]]
│   ├── 需要资产血缘追踪？ → [[dagster]]
│   ├── 需要最简单的 Python 编排？ → [[prefect]]
│   └── 需要数据科学家友好？ → [[metaflow]]
│
├── ML 实验追踪 & 模型管理
│   ├── 行业标准？ → [[mlflow]]
│   └── 多编排器切换？ → [[zenml]]
│
└── 长时运行 / 高可靠工作流
    └── [[temporal]]
```

---

## 八、综合评分矩阵

按 5 个维度对 20 个项目评分（1-5 分）：

| 项目 | Agent 适配 | RAG 深度 | 可靠性 | 易用性 | 生态 | 总分 |
|------|-----------|---------|--------|--------|------|------|
| [[langchain]] | 5 | 3 | 2 | 2 | 5 | 17 |
| [[llama-index]] | 3 | 5 | 2 | 3 | 4 | 17 |
| [[auto-gen]] | 5 | 1 | 3 | 2 | 3 | 14 |
| [[crew-ai]] | 4 | 1 | 2 | 5 | 3 | 15 |
| [[dify]] | 3 | 4 | 3 | 5 | 4 | 19 |
| [[flowise]] | 2 | 1 | 1 | 5 | 3 | 12 |
| [[langflow]] | 2 | 1 | 1 | 4 | 3 | 11 |
| [[n8n]] | 2 | 1 | 3 | 4 | 5 | 15 |
| [[fast-gpt]] | 2 | 4 | 3 | 5 | 2 | 16 |
| [[apache-airflow]] | 1 | 0 | 4 | 1 | 5 | 11 |
| [[prefect]] | 2 | 0 | 3 | 4 | 3 | 12 |
| [[temporal]] | 3 | 0 | 5 | 2 | 3 | 13 |
| [[dagster]] | 2 | 0 | 3 | 3 | 3 | 11 |
| [[kestra]] | 1 | 0 | 3 | 3 | 4 | 11 |
| [[argo-workflows]] | 1 | 0 | 4 | 2 | 3 | 10 |
| [[kubeflow]] | 1 | 0 | 4 | 1 | 3 | 9 |
| [[mlflow]] | 1 | 0 | 3 | 4 | 4 | 12 |
| [[metaflow]] | 2 | 0 | 2 | 5 | 2 | 11 |
| [[flyte]] | 2 | 0 | 4 | 2 | 2 | 10 |
| [[zenml]] | 2 | 0 | 2 | 4 | 3 | 11 |

说明：
- Agent 适配：构建 AI Agent 工作流的能力
- RAG 深度：知识库/RAG 功能的深度
- 可靠性：持久化保证、容错、故障恢复
- 易用性：学习曲线、部署复杂度、文档质量
- 生态：集成数量、社区活跃度、商业支持

没有"最好"的项目，只有"最适合"的组合。[[dify]] 总分最高因为它在 AI 应用层做到了最好的平衡，但如果你要构建复杂 Agent 逻辑，[[langchain]] LangGraph 的 Agent 适配分无可替代。

---

## 相关

- [[ai-workflow-landscape]] — 全景调研（分类速查版）
- [[langchain]] — LLM 应用框架
- [[llama-index]] — 数据 Agent 和工作流框架
- [[temporal]] — 分布式工作流引擎
- [[dify]] — 开源 LLMOps 平台
- [[apache-airflow]] — 工作流调度平台
- [[mlflow]] — ML 生命周期管理平台
