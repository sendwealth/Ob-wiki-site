---
title: MLflow
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [ml, mlops, tracking, registry, python, databricks]
sources:
  - https://github.com/mlflow/mlflow
confidence: 0.9
---

# MLflow

> ML 生命周期管理平台 — 实验追踪、模型注册、AI Gateway、LLM 评估，行业标准级 MLOps 工具。

---

## 一、项目定位

MLflow 由 Databricks 主导开发，是 Linux Foundation 项目。定位为 AI 工程平台，覆盖 Agent、LLM 和传统 ML 模型的完整生命周期管理。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 18k+ |
| 许可证 | Apache 2.0 |
| 语言 | Python |
| 主导 | Databricks |
| 组织 | Linux Foundation |
| 官网 | https://mlflow.org |

定位演进：
- **初始** — Tracking（实验追踪）+ Models（模型打包）+ Registry（模型注册）
- **2024** — 新增 AI Gateway（LLM 统一网关）和 Evaluate（LLM 评估）
- **当前** — "The Open Source AI Engineering Platform for Agents, LLMs & Models"

四大支柱：
1. **Tracing** — LLM/Agent 调用追踪
2. **Evaluation** — LLM 输出评估
3. **Tracking** — 实验参数/指标/Artifact 追踪
4. **Model Registry** — 模型版本管理

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│              MLflow UI                                │
│   Experiments · Runs · Models · Prompts · Traces      │
├─────────────────────────────────────────────────────┤
│              MLflow Core                             │
│   Tracking · Models · Registry · Projects             │
│   Evaluate · AI Gateway · Prompt Engineering          │
├─────────────────────────────────────────────────────┤
│              存储层                                   │
│   File Store · SQL Store · S3/GCS/Azure               │
├─────────────────────────────────────────────────────┤
│              部署层                                   │
│   Built-in Server · SageMaker · Azure ML · K8s         │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| UI | React + Flask | 管理界面 |
| Tracking Server | Flask | REST API |
| 存储 | File/SQL/S3 | Artifact + Metadata |
| 部署 | 多种 | 模型部署到各平台 |
| 语言 | Python + R + Java | 多语言客户端 |

## 三、核心架构

### 3.1 目录结构

```
mlflow/
  mlflow/
    tracking/              — 实验追踪
      _tracking_service/     — Tracking Service
      context/               — 运行上下文
      _fluent/               — Fluent API
    store/                 — 存储抽象
      artifact/              — Artifact Store
        s3/ gcs/ azure/ hdfs/ local/
      model_registry/        — Model Registry Store
    models/                — 模型管理
      evaluation/            — 评估
    utils/                 — 工具
    server/                — 服务器
    deploy/                — 部署
    genai/                 — GenAI/LLM 支持
      evaluators/            — LLM 评估器
    tracing/               — Tracing（2024 新增）
    prompt/                — Prompt 工程
```

### 3.2 Tracking（实验追踪）

```python
import mlflow

mlflow.set_experiment("my-experiment")

with mlflow.start_run():
    # 记录参数
    mlflow.log_param("learning_rate", 0.01)
    mlflow.log_param("epochs", 100)
    
    # 训练模型
    model = train_model()
    
    # 记录指标
    mlflow.log_metric("accuracy", 0.95)
    mlflow.log_metric("f1_score", 0.93)
    
    # 记录模型
    mlflow.sklearn.log_model(model, "model")
    
    # 记录 Artifact
    mlflow.log_artifact("confusion_matrix.png")
```

### 3.3 Model Registry（模型注册）

```python
# 注册模型
mlflow.register_model(
    "runs:/<run-id>/model",
    "my-registered-model"
)

# 模型版本管理
client = mlflow.tracking.MlflowClient()
client.transition_model_version_stage(
    name="my-registered-model",
    version=1,
    stage="Production"
)

# 加载生产模型
model = mlflow.pyfunc.load_model("models:/my-registered-model/Production")
```

模型阶段：None → Staging → Production → Archived

### 3.4 Models（模型打包）

MLmodel 格式统一打包：
```yaml
artifact_path: model
flavors:
  python_function:
    env: conda.yaml
    loader_module: mlflow.sklearn
    model_path: model.pkl
    python_version: 3.11
  sklearn:
    pickled_model: model.pkl
    sklearn_version: 1.3.0
model_uuid: abc-123
run_id: xyz-456
utc_time_created: '2024-01-01 00:00:00'
```

支持的 Flavor：sklearn、pytorch、tensorflow、xgboost、lightgbm、huggingface、onnx 等

### 3.5 Evaluate（LLM 评估，2024 新增）

```python
import mlflow

# 评估 LLM 输出
results = mlflow.evaluate(
    data=eval_data,
    targets="ground_truth",
    predictions="predictions",
    model_type="question-answering",
    evaluators="default",
)

# 自定义评估器
from mlflow.metrics import make_metric

def custom_metric(predictions, targets):
    return sum(1 for p, t in zip(predictions, targets) if p in t) / len(targets)

mlflow.evaluate(
    ...,
    extra_metrics=[make_metric(custom_metric, "custom_accuracy")],
)
```

### 3.6 Tracing（LLM/Agent 追踪，2024 新增）

```python
import mlflow

@mlflow.trace
def my_agent(query):
    # 自动追踪 Agent 调用链
    docs = retriever(query)
    answer = llm(query, docs)
    return answer
```

追踪特性：
- 自动记录 LLM 调用
- Token 用量统计
- Latency 分析
- 嵌套调用链可视化

### 3.7 AI Gateway（LLM 统一网关）

```yaml
# gateway_config.yaml
routes:
  - name: completions
    route_type: llm/v1/completions
    model:
      provider: openai
      name: gpt-4o
      config:
        openai_api_key: $OPENAI_API_KEY
  
  - name: embeddings
    route_type: llm/v1/embeddings
    model:
      provider: openai
      name: text-embedding-3-small
```

```bash
mlflow gateway start --config-path gateway_config.yaml
```

统一 API 端点，可切换供应商无需改代码。

## 四、关键特性

### 4.1 多语言支持

- Python（主要）
- R
- Java
- REST API（任何语言）

### 4.2 部署到多种平台

```python
# 本地部署
mlflow models serve -m "models:/my-model/Production" -p 5000

# Docker
mlflow models build-docker -m "models:/my-model/Production"
docker run -p 5000:5000 my-model-image

# SageMaker
mlflow sagemaker build-and-push-container
mlflow sagemaker deploy -m "models:/my-model/Production"

# Azure ML
mlflow azureml deploy ...
```

### 4.3 Prompt 工程

```python
import mlflow

# 注册 Prompt
mlflow.register_prompt(
    name="summarize",
    template="Summarize the following text: {text}",
    commit_message="Initial version",
)

# 加载 Prompt
prompt = mlflow.load_prompt("summarize")
result = llm(prompt.format(text="..."))
```

### 4.4 Projects（可复现运行）

```yaml
# MLproject
name: my-project
conda_env: conda.yaml
entry_points:
  main:
    parameters:
      alpha: {type: float, default: 0.5}
    command: "python train.py --alpha {alpha}"
```

```bash
mlflow run . -P alpha=0.1
```

## 五、关键设计决策

1. **框架无关** — 不绑定任何 ML 框架，通过 Flavor 抽象支持所有主流框架
2. **存储可插拔** — File Store / SQL Store / S3 / GCS / Azure 灵活选择
3. **Databricks 主导** — 社区驱动但 Databricks 引领方向
4. **LLM 扩展** — 2024 年大幅增加 GenAI 支持（Tracing、Evaluate、AI Gateway）
5. **通常与编排器搭配** — 不自研 Pipeline，与 [[apache-airflow]] / [[prefect]] 搭配

## 六、开发命令速查

```bash
# 安装
pip install mlflow
pip install mlflow[extras]  # 全功能

# 启动 UI
mlflow ui --port 5000

# 启动 Tracking Server
mlflow server --backend-store-uri postgresql://... --default-artifact-root s3://...

# 模型服务
mlflow models serve -m "models:/my-model/Production"
mlflow models build-docker -m "models:/my-model/Production"

# AI Gateway
mlflow gateway start --config-path gateway.yaml
```

## 七、与竞品对比

| 维度 | MLflow | [[kubeflow]] | [[zenml]] | [[metaflow]] |
|------|--------|-------------|----------|-------------|
| 实验追踪 | 最强 | 基础 | 支持 | 支持 |
| 模型注册 | 最强 | 基础 | 支持 | 有限 |
| Pipeline | 无自研 | Argo Workflows | 多编排器 | 自研 |
| LLM 支持 | 强（Tracing+Evaluate+Gateway） | 无 | 新增 | 新增 |
| 学习曲线 | 平缓 | 陡峭 | 平缓 | 平缓 |

---

## 相关

- [[kubeflow]] — K8s 原生 ML 平台
- [[zenml]] — 可扩展 MLOps 框架
- [[metaflow]] — Netflix ML 工作流框架
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
