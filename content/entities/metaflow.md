---
title: Metaflow
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [ml, workflow, python, netflix, data-science]
sources:
  - https://github.com/Netflix/metaflow
confidence: 0.9
---

# Metaflow

> Netflix 人性化 ML 工作流框架 — 数据科学家友好，纯 Python API，内置版本控制，一键部署到 AWS。

---

## 一、项目定位

Metaflow 由 Netflix 开发，核心理念是让数据科学家开发体验与生产部署无缝衔接。纯 Python API、内置数据版本控制、一键部署到 AWS/K8s。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 8k+ |
| 许可证 | Apache 2.0 |
| 语言 | Python |
| 创建者 | Netflix |
| 官网 | https://metaflow.org |

核心定位：
- **人性化** — 数据科学家无需 DevOps 知识即可构建生产级工作流
- **纯 Python** — 无 DSL，无 YAML，纯 Python 类定义工作流
- **内置版本控制** — 每次运行自动版本化数据和代码
- **AWS 深度集成** — 一键部署到 AWS Batch/SageMaker

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│              Metaflow 客户端                          │
│   Flow · Step · Include · Parameter · Resources       │
├─────────────────────────────────────────────────────┤
│              Metaflow 服务层                          │
│   Metadata Service · Artifact Store · Timeline        │
├─────────────────────────────────────────────────────┤
│              执行层                                   │
│   Local · AWS Batch · Kubernetes · Condor             │
├─────────────────────────────────────────────────────┤
│              AWS 服务                                 │
│   S3 · Batch · Step Functions · SageMaker             │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 核心框架 | `metaflow` | Flow/Step/Parameter |
| 元数据服务 | GraphQL + RDS | 运行追踪 |
| Artifact 存储 | S3 | 数据版本化 |
| 执行 | AWS Batch / K8s / 本地 | 多种执行环境 |
| UI | Metaflow UI（开源） | 可视化 |

## 三、核心架构

### 3.1 Flow 定义

```python
from metaflow import FlowSpec, step, Parameter, resources

class MyMLPipeline(FlowSpec):
    alpha = Parameter("alpha", default=0.5, type=float)
    data_path = Parameter("data_path", default="s3://my-bucket/data/")
    
    @step
    def start(self):
        self.data = load_data(self.data_path)
        self.next(self.train)
    
    @step
    def train(self):
        self.model = train_model(self.data, alpha=self.alpha)
        self.next(self.evaluate)
    
    @step
    def evaluate(self):
        self.score = evaluate_model(self.model, self.data)
        print(f"Score: {self.score}")
        self.next(self.end)
    
    @step
    def end(self):
        print("Pipeline complete!")

if __name__ == "__main__":
    MyMLPipeline()
```

### 3.2 核心概念

| 概念 | 说明 |
|------|------|
| Flow | 工作流定义（类） |
| Step | 工作流步骤（方法） |
| Parameter | 参数定义 |
| Include | 文件依赖 |
| Resources | 资源请求（CPU/GPU/内存） |
| foreach | 并行分支 |
| branch/join | 条件分支 |

### 3.3 分支和并行

**条件分支**：
```python
@step
def start(self):
    self.next(self.train_a, self.train_b)

@step
def train_a(self):
    self.model_a = train_variant_a()
    self.next(self.join)

@step
def train_b(self):
    self.model_b = train_variant_b()
    self.next(self.join)

@step
def join(self, inputs):
    self.best = max(inputs, key=lambda x: x.score)
    self.next(self.end)
```

**Foreach 并行**：
```python
@step
def start(self):
    self.params = [0.1, 0.5, 1.0]
    self.next(self.train, foreach="params")

@step
def train(self):
    self.model = train(alpha=self.input)
    self.next(self.join)

@step
def join(self, inputs):
    self.results = [inp.model for inp in inputs]
    self.next(self.end)
```

### 3.4 资源请求

```python
from metaflow import resources, conda

@resources(gpu=2, memory=16000, cpu=4)
@conda(libraries={"pytorch": "2.0"})
@step
def train(self):
    model = train_with_gpu()
    self.next(self.evaluate)
```

### 3.5 版本控制

每次运行自动版本化：
- **代码快照** — Git SHA + 代码快照
- **数据版本** — S3 Artifact 自动版本化
- **参数版本** — 所有 Parameter 记录
- **环境版本** — Conda 依赖快照

```python
from metaflow import Flow

# 查看历史运行
runs = Flow("MyMLPipeline").runs()
for run in runs:
    print(f"Run {run.id}: score={run.data.score}")
```

## 四、关键特性

### 4.1 AWS 集成

- **AWS Batch** — 一键部署到 Batch 执行
- **Step Functions** — 编排为 AWS Step Functions
- **SageMaker** — 部署模型到 SageMaker
- **S3** — Artifact 存储

```bash
# 部署到 AWS Batch
python my_flow.py --with batch
```

### 4.2 Metaflow UI

开源可视化界面：
- 流程图
- 运行历史
- Timeline
- 参数对比

### 4.3 LLMOps 支持（2024 新增）

```python
from metaflow import FlowSpec, step

class LLMPipeline(FlowSpec):
    @step
    def start(self):
        self.prompts = load_prompts()
        self.next(self.generate, foreach="prompts")
    
    @step
    def generate(self):
        self.output = call_llm(self.input)
        self.next(self.join)
    
    @step
    def join(self, inputs):
        self.results = [inp.output for inp in inputs]
        self.next(self.end)
    
    @step
    def end(self):
        save_results(self.results)
```

### 4.4 Card（可视化报告）

```python
from metaflow import card, Card

@card(type="html")
@step
def evaluate(self):
    self.report = generate_html_report()
```

### 4.5 命名空间和标签

```python
from metaflow import namespace, tag

namespace("project:my-project")
tag("experiment:v2")
```

## 五、关键设计决策

1. **纯 Python** — 无 DSL，Flow 就是 Python 类，Step 就是方法
2. **数据科学家优先** — Jupyter 友好，本地开发体验流畅
3. **内置版本控制** — 无需 DVC/Git LFS，自动版本化
4. **AWS 优先** — Netflix 是 AWS 客户，深度集成 AWS 服务
5. **装饰器扩展** — `@resources`、`@conda`、`@card`、`@batch` 等

## 六、开发命令速查

```bash
# 安装
pip install metaflow

# 本地运行
python my_flow.py run

# AWS Batch 运行
python my_flow.py --with batch run

# Step Functions 部署
python my_flow.py step-functions create

# Notebook 集成
from metaflow import Flow
runs = Flow("MyFlow").runs()

# UI
pip install metaflow-ui
metaflow ui
```

## 七、与竞品对比

| 维度 | Metaflow | [[mlflow]] | [[kubeflow]] | [[prefect]] |
|------|----------|-----------|-------------|-------------|
| 核心定位 | 数据科学家友好 | 实验追踪+模型管理 | K8s ML 全栈 | 通用编排 |
| 代码风格 | Python 类 | Python API | Python+YAML | Python 函数 |
| 版本控制 | 内置 | 实验追踪 | 基础 | 无 |
| GPU 支持 | AWS Batch | 无原生 | K8s 原生 | 需配置 |
| 云集成 | AWS | 多云 | K8s | 多云 |
| 学习曲线 | 平缓 | 平缓 | 陡峭 | 平缓 |

---

## 相关

- [[mlflow]] — ML 生命周期管理
- [[kubeflow]] — K8s 原生 ML 平台
- [[prefect]] — 现代 Python 工作流编排
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
