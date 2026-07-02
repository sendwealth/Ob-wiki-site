---
title: Argo Workflows
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [workflow, kubernetes, containers, cncf, argo]
sources:
  - https://github.com/argoproj/argo-workflows
confidence: 0.9
---

# Argo Workflows

> Kubernetes 原生工作流引擎 — CNCF 毕业项目，每个步骤是独立 Pod，Kubeflow Pipelines 底层引擎。

---

## 一、项目定位

Argo Workflows 是 CNCF 毕业项目，Kubernetes 原生的工作流引擎。每个工作流步骤是独立的 K8s Pod，天然隔离。是 Kubeflow Pipelines 的底层引擎。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 15k+ |
| 许可证 | Apache 2.0 |
| 语言 | Go |
| 组织 | CNCF（Argo 项目） |
| 官网 | https://argoproj.github.io/argo-workflows/ |

核心定位：
- **K8s 原生** — CRD 定义工作流，Controller 调度
- **容器隔离** — 每个步骤是独立 Pod
- **DAG + Steps** — 两种编排模式
- **Artifact 传递** — S3/GCS/Azure Blob 等

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                  Argo UI                             │
│   Workflow List · Graph View · Logs · Artifacts       │
├─────────────────────────────────────────────────────┤
│                  Argo Workflow Controller             │
│   Workflow Reconciler · Pod Manager · Artifact Mgr    │
├─────────────────────────────────────────────────────┤
│                  Kubernetes                          │
│   Workflow CRD · Pod · ConfigMap · Secret             │
├─────────────────────────────────────────────────────┤
│                  Artifact Storage                     │
│   S3 · GCS · Azure Blob · MinIO · Git · HTTP          │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 控制器 | Go + Controller Runtime | K8s Operator |
| UI | React | 管理界面 |
| CLI | argo | 命令行工具 |
| 存储 | S3/GCS/Azure/MinIO | Artifact 存储 |
| 执行 | K8s Pod | 每个任务一个 Pod |

## 三、核心架构

### 3.1 Workflow CRD

```yaml
apiVersion: argoproj.io/v1alpha1
kind: Workflow
metadata:
  generateName: my-workflow-
spec:
  entrypoint: main
  
  templates:
  - name: main
    dag:
      tasks:
      - name: extract
        template: python-task
        arguments:
          parameters:
          - name: script
            value: |
              import json
              data = fetch_data()
              print(json.dumps(data))
      
      - name: transform
        template: python-task
        dependencies: [extract]
        arguments:
          parameters:
          - name: script
            value: |
              data = {{tasks.extract.outputs.result}}
              transformed = process(data)
              print(transformed)
      
      - name: load
        template: python-task
        dependencies: [transform]
        arguments:
          parameters:
          - name: script
            value: |
              data = {{tasks.transform.outputs.result}}
              save_to_db(data)
  
  - name: python-task
    inputs:
      parameters:
      - name: script
    container:
      image: python:3.11
      command: [python, -c]
      args: ["{{inputs.parameters.script}}"]
```

### 3.2 DAG vs Steps

**DAG 模式**（有向无环图）：
```yaml
templates:
- name: dag-workflow
  dag:
    tasks:
    - name: A
      template: task-template
    - name: B
      dependencies: [A]
      template: task-template
    - name: C
      dependencies: [A]
      template: task-template
    - name: D
      dependencies: [B, C]
      template: task-template
```

**Steps 模式**（顺序/并行）：
```yaml
templates:
- name: steps-workflow
  steps:
  - - name: step1
      template: task-template
  - - name: step2a
      template: task-template
    - name: step2b        # 并行
      template: task-template
  - - name: step3
      template: task-template
```

### 3.3 Artifact 传递

```yaml
templates:
- name: producer
  container:
    image: python:3.11
    command: [python, -c]
    args: ["print('hello') > /tmp/output.txt"]
  outputs:
    artifacts:
    - name: output
      path: /tmp/output.txt

- name: consumer
  inputs:
    artifacts:
    - name: input
      path: /tmp/input.txt
  container:
    image: python:3.11
    command: [cat, /tmp/input.txt]
```

Artifact 存储配置：
```yaml
artifactRepository:
  s3:
    bucket: my-bucket
    endpoint: s3.amazonaws.com
    accessKeySecret:
      name: aws-credentials
      key: accessKey
    secretKeySecret:
      name: aws-credentials
      key: secretKey
```

### 3.4 目录结构

```
argo-workflows/
  cmd/
    workflow-controller/   — Controller 入口
    argo/                  — CLI 入口
    server/                — API Server
  pkg/
    apis/                  — CRD 定义
    workflow/              — 工作流核心逻辑
      controller/           — Controller
      validate/             — 校验
      util/                 — 工具
    executor/              — Pod 执行器
    artifacts/             — Artifact 管理
    plugins/               — 插件系统
  ui/                     — React 前端
```

### 3.5 工作流执行流程

```
1. 用户提交 Workflow CRD
2. Controller 监听并创建 Workflow
3. Controller 解析 DAG/Steps，创建 Pod
4. Pod 执行任务，写入 Artifact
5. Controller 监控 Pod 状态
6. Pod 完成后，Controller 创建下一个 Pod
7. 所有 Pod 完成，Workflow 标记为 Succeeded
```

## 四、关键特性

### 4.1 资源管理

```yaml
templates:
- name: resource-intensive
  container:
    image: python:3.11
    resources:
      requests:
        memory: "4Gi"
        cpu: "2"
        nvidia.com/gpu: "1"  # GPU
      limits:
        memory: "8Gi"
        cpu: "4"
```

### 4.2 重试和超时

```yaml
templates:
- name: retry-task
  retryStrategy:
    limit: "3"
    backoff:
      duration: "10s"
      factor: "2"
  container:
    image: python:3.11
    command: [python, -c]
    args: ["import random; exit(random.randint(0,1))"]
  activeDeadlineSeconds: 300  # 超时
```

### 4.3 参数化

```yaml
spec:
  arguments:
    parameters:
    - name: date
      value: "2024-01-01"

templates:
- name: param-task
  inputs:
    parameters:
    - name: date
  container:
    image: python:3.11
    command: [echo]
    args: ["{{inputs.parameters.date}}"]
```

### 4.4 循环

```yaml
templates:
- name: loop-task
  withParam: "{{workflow.parameters.items}}"  # ["a", "b", "c"]
  container:
    image: python:3.11
    command: [echo]
    args: ["{{item}}"]
```

### 4.5 条件执行

```yaml
templates:
- name: conditional
  dag:
    tasks:
    - name: check
      template: check-template
    - name: run-if-true
      template: task-template
      dependencies: [check]
      when: "{{tasks.check.outputs.result}} == true"
```

### 4.6 工作流模板

```yaml
apiVersion: argoproj.io/v1alpha1
kind: WorkflowTemplate
metadata:
  name: my-template
spec:
  templates:
  - name: main
    ...

# 使用
apiVersion: argoproj.io/v1alpha1
kind: Workflow
spec:
  entrypoint: main
  templateRef:
    name: my-template
    template: main
```

## 五、关键设计决策

1. **K8s 原生** — CRD + Controller 模式，与 K8s 深度集成
2. **Pod 隔离** — 每个任务独立 Pod，资源隔离、故障隔离
3. **Artifact 传递** — 任务间通过对象存储传递数据，而非内存
4. **声明式 YAML** — 工作流用 YAML 定义，Git 友好
5. **DAG + Steps 双模式** — 灵活编排

## 六、开发命令速查

```bash
# 安装
kubectl create namespace argo
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.5.0/install.yaml

# CLI
argo submit my-workflow.yaml
argo list
argo logs my-workflow
argo get my-workflow
argo delete my-workflow

# UI
kubectl -n argo port-forward deployment/argo-server 2746:2746
# https://localhost:2746
```

## 七、与竞品对比

| 维度 | Argo Workflows | [[kubeflow]] Pipelines | [[apache-airflow]] |
|------|----------------|----------------------|-------------------|
| 执行环境 | K8s Pod | K8s Pod（底层是 Argo） | 多种 Executor |
| 定义方式 | YAML | Python SDK | Python DAG |
| 隔离性 | 最强（Pod 级） | 最强 | 依赖 Executor |
| GPU 支持 | 原生 | 原生 | 需配置 |
| 学习曲线 | 中等 | 陡峭 | 陡峭 |
| 生态 | K8s 生态 | ML 生态 | 数据生态 |

---

## 相关

- [[kubeflow]] — K8s 原生 ML 平台（底层用 Argo）
- [[apache-airflow]] — 传统工作流调度
- [[prefect]] — 现代 Python 工作流编排
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
