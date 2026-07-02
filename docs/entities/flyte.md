---
title: Flyte
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [ml, workflow, kubernetes, python, type-safe]
sources:
  - https://github.com/flyteorg/flyte
confidence: 0.9
---

# Flyte

> 云原生 ML/数据工作流平台 — 强类型工作流、K8s 原生、可复用组件，LF AI 基金会项目。

---

## 一、项目定位

Flyte 由 Lyft 开发，是 LF AI & Data 基金会项目。核心特点：强类型工作流（编译时类型检查）、K8s 原生、可复用 Task 和 Workflow。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 5k+ |
| 许可证 | Apache 2.0 |
| 语言 | Python + Go |
| 创建者 | Lyft |
| 组织 | LF AI & Data Foundation |
| 官网 | https://flyte.org |

Flyte 2（2025）：全新的 Python SDK（`flyte-sdk`），更轻量级，但底层后端不变。

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│              Flyte Console                            │
│   Workflows · Tasks · Executions · Launch Plans       │
├─────────────────────────────────────────────────────┤
│              Flyte Admin + Control Plane              │
│   Scheduler · Propeller · Data Catalog · Admin        │
├─────────────────────────────────────────────────────┤
│              Flytekit（Python SDK）                    │
│   Task · Workflow · Launch Plan · Type System          │
├─────────────────────────────────────────────────────┤
│              Kubernetes                               │
│   Pod · Workflow · Spark · Dask · Ray                 │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 控制平面 | Go（FlyteAdmin/Propeller） | 调度和编排 |
| SDK | Python（flytekit） | 工作流定义 |
| UI | React | 管理界面 |
| 执行 | K8s Pod | 任务执行 |
| 存储 | S3/GCS/Azure | 原始数据存储 |
| 数据库 | PostgreSQL | 元数据 |

## 三、核心架构

### 3.1 Task 和 Workflow

```python
from flytekit import task, workflow

@task
def extract(data_path: str) -> list:
    return load_data(data_path)

@task
def transform(data: list) -> list:
    return [x * 2 for x in data]

@task
def load(data: list) -> str:
    return save_data(data)

@workflow
def my_pipeline(data_path: str = "s3://bucket/data/") -> str:
    data = extract(data_path=data_path)
    transformed = transform(data=data)
    result = load(data=transformed)
    return result
```

### 3.2 类型系统（核心差异化）

Flyte 的类型系统在编译时检查，不是运行时：

```python
from flytekit.types.file import FlyteFile
from flytekit.types.directory import FlyteDirectory
from typing import List, Dict, Tuple

@task
def typed_task(
    data: FlyteFile[csv],         # 类型化文件
    config: Dict[str, int],       # 字典类型
    items: List[float],           # 列表类型
    pair: Tuple[str, int],        # 元组类型
) -> FlyteFile[parquet]:          # 返回类型化文件
    ...
```

支持的类型：
- 基础：int, float, str, bool
- 集合：List, Dict, Tuple, Set
- 文件：FlyteFile, FlyteDirectory
- 自定义：TypeTransformer 注册自定义类型
- Pandas：DataFrame（自动序列化/反序列化）

### 3.3 动态工作流

```python
from flytekit import dynamic

@dynamic
def dynamic_pipeline(n: int) -> list:
    results = []
    for i in range(n):
        result = process(data=i)
        results.append(result)
    return results
```

### 3.4 Map Task（批量并行）

```python
from flytekit import map_task

@task
def process_single(item: int) -> int:
    return item * 2

@workflow
def batch_pipeline(items: list[int]) -> list[int]:
    return map_task(process_single)(item=items)
```

### 3.5 执行插件

| 插件 | 用途 |
|------|------|
| Container | 默认，K8s Pod |
| Spark | Apache Spark 任务 |
| Dask | Dask 分布式计算 |
| Ray | Ray 分布式计算 |
| Athena | AWS Athena 查询 |
| Snowflake | Snowflake 查询 |
| Hive | Hive 查询 |
| dbt | dbt 数据转换 |

## 四、关键特性

### 4.1 数据目录

自动追踪所有数据血缘：
- 输入/输出类型
- 数据大小
- 数据哈希
- 可查询

### 4.2 缓存

```python
@task(cache=True, cache_version="1.0")
def expensive_task(data: str) -> str:
    ...
```

相同输入 + 相同版本 = 缓存命中

### 4.3 重试

```python
@task(retries=3, interruptible=True)
def flaky_task():
    ...
```

### 4.4 资源请求

```python
from flytekit import Resources

@task(requests=Resources(cpu="4", mem="16Gi", gpu="1"))
def gpu_task():
    ...
```

### 4.5 Launch Plan

参数化的工作流入口：
```python
from flytekit import LaunchPlan

my_plan = LaunchPlan.create(
    "daily-plan",
    my_pipeline,
    default_inputs={"data_path": "s3://bucket/daily/"},
    schedule=CronSchedule(cron_expression="0 8 * * *"),
)
```

## 五、关键设计决策

1. **强类型** — 编译时类型检查，减少运行时错误
2. **Go 控制平面** — 高性能调度和编排
3. **可复用组件** — Task 和 Workflow 可独立注册和复用
4. **K8s 原生** — 利用 K8s 资源管理和调度
5. **数据目录** — 自动追踪数据血缘

## 六、开发命令速查

```bash
# 安装
pip install flytekit

# 本地运行
pyflyte run my_workflow.py my_pipeline

# 注册到 Flyte 集群
flytectl register files my_workflow.py

# CLI
flytectl get workflows
flytectl get tasks
flytectl launch -p my-project -d development --workflow my_pipeline

# Flyte 集群部署（Helm）
helm install flyte flyteorg/flyte
```

## 七、与竞品对比

| 维度 | Flyte | [[kubeflow]] | [[argo-workflows]] | [[prefect]] |
|------|-------|-------------|-------------------|-------------|
| 类型安全 | 最强 | 无 | 无 | Python 类型 |
| 执行环境 | K8s Pod | K8s Pod | K8s Pod | 多种 |
| 语言 | Python SDK + Go 后端 | Python + YAML | YAML | Python |
| 动态工作流 | 支持 | 有限 | 支持 | 支持 |
| 数据血缘 | 内置 | 基础 | 无 | 无 |
| 学习曲线 | 中等 | 陡峭 | 中等 | 平缓 |

---

## 相关

- [[kubeflow]] — K8s 原生 ML 平台
- [[argo-workflows]] — K8s 原生工作流引擎
- [[mlflow]] — ML 生命周期管理
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
