---
title: Kubeflow
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [ml, platform, kubernetes, cncf, pipeline]
sources:
  - https://github.com/kubeflow/kubeflow
confidence: 0.9
---

# Kubeflow

> K8s 原生 ML 工作流平台 — CNCF 孵化项目，Pipelines + Katib + KServe，完整的 ML 开发生命周期管理。

---

## 一、项目定位

Kubeflow 由 Google 发起，是 CNCF 孵化项目，定位为 Kubernetes 上的 ML 平台。核心组件：Pipelines（基于 [[argo-workflows]]）、Katib（超参数调优）、KServe（模型推理）、Notebooks。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 14k+ |
| 许可证 | Apache 2.0 |
| 语言 | Python + Go + YAML |
| 发起者 | Google |
| 组织 | CNCF |
| 官网 | https://kubeflow.org |

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│              Kubeflow Dashboard                       │
│   Notebooks · Pipelines · Experiments · Models        │
├─────────────────────────────────────────────────────┤
│              核心组件                                 │
│   Pipelines · Katib · KServe · Training Operator      │
├─────────────────────────────────────────────────────┤
│              基础设施                                 │
│   Argo Workflows · Istio · Knative · Cert-Manager     │
├─────────────────────────────────────────────────────┤
│              Kubernetes                              │
│   Pod · Service · Ingress · GPU · PV/PVC             │
└─────────────────────────────────────────────────────┘
```

| 组件 | 功能 | 底层 |
|------|------|------|
| Pipelines | ML Pipeline 编排 | [[argo-workflows]] |
| Katib | 超参数调优 | K8s Job |
| KServe | 模型推理 | Knative + Istio |
| Training Operator | 分布式训练 | K8s Job |
| Notebooks | Jupyter 开发环境 | K8s Pod |
| Central Dashboard | 统一管理界面 | React |
| Profiles | 多租户命名空间 | K8s RBAC |

## 三、核心架构

### 3.1 Kubeflow Pipelines

基于 Argo Workflows 的 ML Pipeline 编排：

```python
from kfp import dsl
from kfp.dsl import component

@component(base_image="python:3.11")
def extract_data(output_path: str):
    import pandas as pd
    data = pd.read_csv("https://example.com/data.csv")
    data.to_csv(output_path)

@component(base_image="python:3.11")
def train_model(data_path: str, model_path: str):
    import pickle
    from sklearn.ensemble import RandomForestClassifier
    import pandas as pd
    data = pd.read_csv(data_path)
    model = RandomForestClassifier().fit(data.drop("label", axis=1), data["label"])
    pickle.dump(model, open(model_path, "wb"))

@dsl.pipeline(name="my-ml-pipeline")
def my_pipeline():
    extract = extract_data(output_path="/tmp/data.csv")
    train = train_model(data_path=extract.outputs["output_path"], model_path="/tmp/model.pkl")
    
from kfp.compiler import Compiler
Compiler().compile(my_pipeline, "pipeline.yaml")
```

### 3.2 Katib（超参数调优）

```yaml
apiVersion: kubeflow.org/v1beta1
kind: Experiment
metadata:
  name: pytorch-experiment
spec:
  objective:
    type: maximize
    goal: 0.99
    objectiveMetricName: accuracy
  algorithm:
    algorithmName: bayesianoptimization
  parameters:
    - name: lr
      parameterType: double
      feasibleSpace:
        min: "0.001"
        max: "0.1"
    - name: epochs
      parameterType: int
      feasibleSpace:
        min: "10"
        max: "100"
  trialTemplate:
    spec:
      template:
        spec:
          containers:
          - name: training
            image: my-training-image
            command: ["python", "train.py", "--lr=${trialParameters.lr}", "--epochs=${trialParameters.epochs}"]
```

### 3.3 KServe（模型推理）

```yaml
apiVersion: serving.kserve.io/v1beta1
kind: InferenceService
metadata:
  name: sklearn-model
spec:
  predictor:
    model:
      modelFormat:
        name: sklearn
      storageUri: "gs://my-bucket/models/sklearn"
      resources:
        requests:
          cpu: "1"
          memory: "2Gi"
```

### 3.4 Training Operator（分布式训练）

支持框架：PyTorch、TensorFlow、MXNet、XGBoost

```yaml
apiVersion: kubeflow.org/v1
kind: PyTorchJob
metadata:
  name: pytorch-training
spec:
  pytorchReplicaSpecs:
    Master:
      replicas: 1
      template:
        spec:
          containers:
          - name: pytorch
            image: my-training-image
            resources:
              limits:
                nvidia.com/gpu: 4
    Worker:
      replicas: 4
      template:
        spec:
          containers:
          - name: pytorch
            image: my-training-image
            resources:
              limits:
                nvidia.com/gpu: 4
```

## 四、关键特性

### 4.1 Notebooks

Web 端 Jupyter Notebook，连接 K8s 集群资源：
- 自定义镜像
- GPU 分配
- PVC 持久存储
- 多用户隔离

### 4.2 Profiles（多租户）

```yaml
apiVersion: kubeflow.org/v1
kind: Profile
metadata:
  name: team-a
spec:
  owner:
    kind: User
    name: user@example.com
  resourceQuotaSpec:
    hard:
      cpu: "100"
      memory: 200Gi
      nvidia.com/gpu: "8"
```

### 4.3 Metadata 和实验追踪

- Experiment 跟踪训练实验
- Run 记录 Pipeline 执行
- Artifact 存储模型和数据

## 五、关键设计决策

1. **K8s 原生** — 所有组件部署在 K8s，利用 K8s 资源管理
2. **Argo Workflows 底层** — Pipeline 引擎不自研，复用 Argo
3. **组件独立** — 各组件可独立安装使用
4. **GPU 原生** — K8s Device Plugin 直接支持 GPU
5. **多租户** — Profile + RBAC 隔离

## 六、开发命令速查

```bash
# 安装（需要 K8s 集群）
kustomize build example | kubectl apply -f -

# 或使用 kfctl
kfctl apply -V -f kfctl_config.yaml

# Pipeline 编译
dsl-compile --py pipeline.py --output pipeline.yaml

# kfp CLI
kfp endpoint=<kfp-url>
kfp pipeline upload pipeline.yaml
kfp run submit -e experiment -p pipeline
```

## 七、与竞品对比

| 维度 | Kubeflow | [[mlflow]] | [[flyte]] | [[zenml]] |
|------|----------|-----------|----------|----------|
| 定位 | K8s ML 全栈 | ML 生命周期 | K8s 工作流 | MLOps 连接器 |
| Pipeline | Argo Workflows | 无自研 | 自研 | 多编排器 |
| 调优 | Katib（原生） | 无 | 无 | 无 |
| 推理 | KServe | MLflow Serving | 无 | 无 |
| 训练 | Training Operator | 无 | 支持 | 支持 |
| 学习曲线 | 陡峭 | 平缓 | 中等 | 平缓 |

---

## 相关

- [[argo-workflows]] — Pipeline 底层引擎
- [[mlflow]] — ML 生命周期管理
- [[flyte]] — 云原生 ML 工作流
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
