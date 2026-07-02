---
title: AI Workflow 开源项目全景调研
created: 2026-06-02
updated: 2026-06-02
type: comparison
tags: [ai-workflow, llm, agent, mlops, orchestration, landscape]
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
confidence: 0.9
---

# 🔍 AI Workflow 开源项目全景调研报告

> 以下报告将 20 个主流开源项目按 **四大类别** 组织，覆盖 LLM 应用层、通用编排层、ML 平台层、可视化低代码层。

---

## 一、🤖 LLM 原生 Agent & 工作流框架

这类项目直接面向 LLM/AI Agent 工作流，是当前最热门的方向。

| 项目 | Stars | 语言 | 关键词 |
|------|-------|------|--------|
| [[langchain]] | 90k+ | Python + JS | LangGraph, Multi-Agent, 有状态工作流, 条件分支, 循环 |
| [[llama-index]] | 36k+ | Python | RAG, Workflow引擎, 数据连接器, 160+数据源 |
| [[crew-ai]] | 20k+ | Python | Multi-Agent, 角色化, 团队协作, 顺序/层级流程 |
| [[auto-gen]] | 35k+ | Python | Multi-Agent, 对话驱动, 异步事件驱动, 微软研究院 |

---

## 二、🎨 可视化 / 低代码 AI Workflow 平台

这类项目提供拖拽式界面，降低 AI 工作流构建门槛。

| 项目 | Stars | 语言 | 关键词 |
|------|-------|------|--------|
| [[dify]] | 50k+ | Python + TS | 可视化工作流编排, RAG Pipeline, 私有化部署, 100+模型 |
| [[flowise]] | 30k+ | Node.js | LangChain.js, 拖拽节点, iframe嵌入, 快速原型 |
| [[langflow]] | 30k+ | Python | React Flow, 导出Python代码, DataStax收购 |
| [[n8n]] | 50k+ | TypeScript | 400+集成, AI Agent节点, Fair-code, 业务自动化 |
| [[fast-gpt]] | 18k+ | TypeScript | 国产, 知识库问答, 可视化工作流, Docker一键部署 |

---

## 三、⚙️ 通用工作流编排引擎（广泛用于 AI/ML Pipeline）

这类项目是成熟的工作流编排平台，在 AI/ML 场景中被广泛采用。

| 项目 | Stars | 语言 | 关键词 |
|------|-------|------|--------|
| [[apache-airflow]] | 37k+ | Python | DAG, 1000+ Provider, 批处理, 调度 |
| [[prefect]] | 17k+ | Python | 原生Python, 动态工作流, 事件驱动, Airflow替代 |
| [[temporal]] | 12k+ | Go/Java/Python/TS | 分布式, 长时运行, 故障恢复, Workflow as Code |
| [[dagster]] | 11k+ | Python | Software-Defined Assets, 资产思维, 数据血缘 |
| [[kestra]] | 8k+ | Java | YAML声明式, 600+插件, 任务重放 |
| [[argo-workflows]] | 15k+ | Kubernetes | CNCF毕业, 容器原生, Kubeflow底层, GPU调度 |

---

## 四、🔬 ML 平台 & MLOps 专用工作流

这类项目专注于 ML 开发生命周期的完整管理。

| 项目 | Stars | 语言 | 关键词 |
|------|-------|------|--------|
| [[kubeflow]] | 14k+ | Kubernetes | CNCF, Pipelines, KServe, Katib |
| [[mlflow]] | 18k+ | Python | 实验追踪, 模型注册, AI Gateway, Databricks |
| [[metaflow]] | 8k+ | Python | 数据科学家友好, AWS深度集成, 内置版本控制 |
| [[flyte]] | 5k+ | Kubernetes | 强类型, Spotify, LF AI基金会 |
| [[zenml]] | 4k+ | Python | MLOps连接器, 多编排器, LLMOps |

---

## 📊 选型建议

| 场景 | 推荐项目 |
|---|---|
| 🧠 **构建 AI Agent / LLM 应用** | [[langchain]] + LangGraph、[[llama-index]] |
| 🤝 **Multi-Agent 协作** | [[crew-ai]]（易用）、[[auto-gen]]（微软生态） |
| 🎨 **可视化低代码 AI 工作流** | [[dify]]（全栈）、[[fast-gpt]]（国产/知识库）、[[flowise]]（轻量原型） |
| 🔗 **AI + 业务系统集成自动化** | [[n8n]]（400+连接器） |
| ⚙️ **传统 ML Pipeline 编排** | [[apache-airflow]]（最成熟）、[[prefect]]（现代替代）、[[dagster]]（资产思维） |
| 🔒 **长时运行 / 高可靠 AI 工作流** | [[temporal]]（最强容错） |
| ☸️ **Kubernetes 原生 AI Pipeline** | [[kubeflow]]、[[argo-workflows]]、[[flyte]] |
| 📈 **ML 实验追踪 & 模型管理** | [[mlflow]]（行业标准） |
| 🏗️ **数据科学家友好型** | [[metaflow]]（Netflix 出品） |

### 🏆 综合热度 TOP 5（按 GitHub Stars）

| 排名 | 项目 | Stars | 定位 |
|------|------|-------|------|
| 1 | [[langchain]] | 90k+ | LLM 框架之王 |
| 2 | [[dify]] / [[n8n]] | 50k+ | 可视化 AI 平台双雄 |
| 3 | [[apache-airflow]] | 37k+ | 调度领域常青树 |
| 4 | [[llama-index]] | 36k+ | 数据+RAG 首选 |
| 5 | [[auto-gen]] | 35k+ | 微软 Multi-Agent 旗舰 |

---

## 相关

- [[kubernetes-agent-platforms]] — K8s 原生 AI Agent 管理平台竞品
- [[agentic-rag]] — Agentic RAG 概念与框架
- [[agent-world]] — Agent World 智能体世界设计
