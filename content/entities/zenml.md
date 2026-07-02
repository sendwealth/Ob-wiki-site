---
title: ZenML
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [ml, mlops, pipeline, python, framework]
sources:
  - https://github.com/zenml-io/zenml
confidence: 0.9
---

# ZenML

> 可扩展 MLOps 框架 — "MLOps 连接器"，统一 Pipeline 抽象连接各种 ML 基础设施，多编排器支持。

---

## 一、项目定位

ZenML 定位为 "MLOps 连接器"——提供统一 Pipeline 抽象连接各种 ML 基础设施。支持 Kubeflow、Airflow、Vertex AI 等多种编排器，2024 年增加 LLMOps 支持。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 4k+ |
| 许可证 | Apache 2.0 |
| 语言 | Python |
| 公司 | ZenML GmbH |
| 官网 | https://zenml.io |

核心定位：
- **Pipeline 抽象** — 统一 API 适配不同后端
- **Stack 抽象** — 将基础设施抽象为可切换的 Stack
- **多编排器** — Local / Airflow / Kubeflow / Vertex AI / Step Functions
- **LLMOps** — LLM 评估、Prompt 版本管理

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│              ZenML Dashboard                         │
│   Pipelines · Runs · Stacks · Models · Artifacts     │
├─────────────────────────────────────────────────────┤
│              ZenML Core                              │
│   Pipeline · Step · Stack · Model · Artifact          │
│   Flavor · Plugin · Secret                           │
├─────────────────────────────────────────────────────┤
│              Stack Components                        │
│   Orchestrator · Artifact Store · Step Operator       │
│   Container Registry · Secret Store · Model Deployer │
├─────────────────────────────────────────────────────┤
│              后端                                    │
│   Local · AWS · GCP · Azure · K8s                     │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 核心框架 | `zenml` | Pipeline/Step/Stack |
| Dashboard | React + FastAPI | 管理界面 |
| 数据库 | SQLite / MySQL / PostgreSQL | 元数据 |
| Artifact Store | Local / S3 / GCS / Azure | 数据存储 |
| 编排器 | 多种 | 可插拔 |

## 三、核心架构

### 3.1 Pipeline 定义

```python
from zenml import pipeline, step

@step
def extract() -> dict:
    return load_data()

@step
def train(data: dict) -> dict:
    return train_model(data)

@step
def evaluate(model: dict) -> float:
    return evaluate_model(model)

@pipeline
def my_pipeline():
    data = extract()
    model = train(data)
    score = evaluate(model)
```

### 3.2 Stack 抽象（核心创新）

Stack = 一组基础设施组件的集合：

```
┌─────────────────────────────────────────────┐
│                 Stack                        │
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │ Orchestrator  │  │Artifact Store│        │
│  │ (Kubeflow)   │  │   (S3)       │        │
│  └──────────────┘  └──────────────┘        │
│  ┌──────────────┐  ┌──────────────┐        │
│  │ Step Operator │  │Container Reg │        │
│  │ (Vertex AI)  │  │  (ECR)       │        │
│  └──────────────┘  └──────────────┘        │
│  ┌──────────────┐  ┌──────────────┐        │
│  │ Secret Store │  │Model Deployer│        │
│  │ (AWS SM)     │  │  (SageMaker) │        │
│  └──────────────┘  └──────────────┘        │
└─────────────────────────────────────────────┘
```

切换 Stack 即切换整个基础设施：
```bash
zenml stack set local-stack     # 本地开发
zenml stack set aws-stack       # AWS 生产
zenml stack set gcp-stack       # GCP 生产
```

### 3.3 Stack Components

| 组件 | 说明 | Flavor 示例 |
|------|------|-------------|
| Orchestrator | 任务执行 | local, kubeflow, airflow, vertex, step_functions |
| Artifact Store | 数据存储 | local, s3, gcs, azure |
| Container Registry | 容器镜像 | local, ecr, gcr |
| Step Operator | 远程执行 | vertex, sagemaker, spark |
| Secret Store | 密钥管理 | local, aws, gcp, azure |
| Model Deployer | 模型部署 | sagemaker, mlflow, bento |
| Experiment Tracker | 实验追踪 | mlflow, wandb, neptune |
| Alerter | 告警通知 | slack, discord, email |

### 3.4 Model 管理

```python
from zenml import Model

model = Model(
    name="my-model",
    version="1.0.0",
)

@pipeline(model=model)
def my_pipeline():
    ...
```

### 3.5 LLMOps 支持（2024 新增）

```python
from zenml import step

@step
def generate_llm_response(prompt: str) -> str:
    # LLM 调用
    response = call_llm(prompt)
    return response

@step
def evaluate_llm(response: str, ground_truth: str) -> float:
    # LLM 评估
    score = evaluate(response, ground_truth)
    return score
```

## 四、关键特性

### 4.1 本地到生产

```bash
# 本地开发
zenml init
python my_pipeline.py

# 注册生产 Stack
zenml stack register aws-stack \
    -o kubeflow \
    -a s3 \
    -c ecr

# 切换并运行
zenml stack set aws-stack
python my_pipeline.py
```

### 4.2 集成

| 集成 | 功能 |
|------|------|
| MLflow | 实验追踪、模型注册 |
| Wandb | 实验追踪 |
| Neptune | 实验追踪 |
| Evidently | 数据漂移检测 |
| Whylogs | 数据分析 |
| HuggingFace | 模型集成 |
| Label Studio | 数据标注 |

### 4.3 CLI 丰富

```bash
zenml pipeline list
zenml pipeline runs list
zenml stack list
zenml model list
zenml artifact list
```

## 五、关键设计决策

1. **Stack 抽象** — 基础设施即配置，切换零代码改动
2. **Pipeline 即代码** — Python 定义，版本可控
3. **多编排器** — 不绑定任何编排器，可切换
4. **Flavor 系统** — 组件实现以 Flavor 形式注册，可扩展
5. **本地优先** — 本地开发体验流畅，逐步上云

## 六、开发命令速查

```bash
# 安装
pip install zenml

# 初始化
zenml init

# 运行
python my_pipeline.py

# 集成
zenml integration install mlflow
zenml integration install kubeflow

# Dashboard
zenml up

# Stack 管理
zenml stack register my-stack -o local -a local
zenml stack set my-stack
```

## 七、与竞品对比

| 维度 | ZenML | [[mlflow]] | [[kubeflow]] | [[metaflow]] |
|------|-------|-----------|-------------|-------------|
| 定位 | MLOps 连接器 | 实验追踪+模型 | K8s ML 全栈 | 数据科学友好 |
| Pipeline | 统一抽象 | 无 | Argo | 自研 |
| 编排器 | 多种 | 无 | Argo | AWS Batch |
| 基础设施切换 | Stack（零代码） | N/A | K8s 配置 | AWS 绑定 |
| 学习曲线 | 平缓 | 平缓 | 陡峭 | 平缓 |
| 灵活性 | 最高 | 中 | 低 | 中 |

---

## 相关

- [[mlflow]] — ML 生命周期管理（常搭配使用）
- [[kubeflow]] — K8s 原生 ML 平台
- [[metaflow]] — Netflix ML 工作流框架
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
