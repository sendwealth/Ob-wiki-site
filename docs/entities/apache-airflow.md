---
title: Apache Airflow
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [workflow, orchestration, dag, python, apache, scheduling]
sources:
  - https://github.com/apache/airflow
confidence: 0.9
---

# Apache Airflow

> 最成熟的工作流调度平台 — 2014 年创建，DAG 工作流调度的事实标准，1000+ Provider Package。

---

## 一、项目定位

Apache Airflow 由 Airbnb 的 Maxime Beauchemin 于 2014 年创建，2016 年进入 Apache 孵化器，2019 年成为顶级项目。是工作流调度领域的事实标准。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 37k+ |
| 许可证 | Apache 2.0 |
| 语言 | Python |
| 创建者 | Maxime Beauchemin（Airbnb） |
| 组织 | Apache Software Foundation |

核心定位：
- **DAG 即代码** — Python 定义工作流，版本可控
- **调度优先** — 强大的 Cron + 传感器调度
- **1000+ Provider** — 覆盖几乎所有数据源和服务
- **批处理和 ETL** — 不适合高度动态工作流

局限：
- DAG 必须在运行前定义（非动态）
- 对 AI Agent 这种高度动态工作流不够灵活
- 更适合批处理和 ETL 类型 AI Pipeline

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                  Web UI（Flask + React）               │
│   DAG 视图 · Gantt · Graph · Task Log · Variable      │
├─────────────────────────────────────────────────────┤
│                  调度器（Scheduler）                    │
│   DagProcessor · SchedulerJob · Executor              │
├─────────────────────────────────────────────────────┤
│                  执行器（Executor）                     │
│   Sequential · Local · Celery · Kubernetes · Dask     │
├─────────────────────────────────────────────────────┤
│                  元数据（Metadata DB）                  │
│   SQLite / PostgreSQL / MySQL                         │
│   DAG · TaskInstance · XCom · Variable · Connection   │
├─────────────────────────────────────────────────────┤
│                  Provider（1000+）                     │
│   AWS · GCP · Azure · Databricks · Slack · ...        │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| Web UI | Flask + FAB + React | 管理界面 |
| 调度器 | Python 多进程 | 触发和调度 |
| 执行器 | 多种 Executor | 任务执行 |
| 元数据库 | PostgreSQL（推荐）/ MySQL / SQLite | 状态存储 |
| 队列 | Redis / RabbitMQ（Celery Executor） | 任务分发 |
| Provider | 1000+ pip 包 | 第三方集成 |

## 三、核心架构

### 3.1 目录结构

```
airflow/
  src/airflow/
    api/                   — REST API
    cli/                   — CLI 命令
    configuration/         — 配置
    connections/           — 连接管理
    dag_processing/        — DAG 解析
    executors/             — 执行器
      base_executor.py       — BaseExecutor
      local_executor.py      — LocalExecutor
      celery_executor.py     — CeleryExecutor
      kubernetes_executor.py — KubernetesExecutor
    jobs/                  — 后台任务
      scheduler_job.py       — SchedulerJob
      triggerer_job.py       — TriggererJob
    models/                — 数据模型
      dag.py
      taskinstance.py
      xcom.py
      variable.py
      connection.py
    schedulers/            — 调度逻辑
    serialization/         — 序列化
    settings/              — 设置
    task/                  — Task 框架
      task_runner/           — TaskRunner
    triggers/              — 异步触发器
    utils/                 — 工具
    www/                   — Web UI
```

### 3.2 核心概念

**DAG（有向无环图）**：
```python
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime

with DAG(
    'my_dag',
    start_date=datetime(2024, 1, 1),
    schedule='@daily',
    catchup=False,
) as dag:
    
    task1 = PythonOperator(
        task_id='extract',
        python_callable=extract_data,
    )
    
    task2 = PythonOperator(
        task_id='transform',
        python_callable=transform_data,
    )
    
    task3 = PythonOperator(
        task_id='load',
        python_callable=load_data,
    )
    
    task1 >> task2 >> task3
```

**Operator** — 任务类型：
| 类别 | Operator |
|------|----------|
| 动作 | PythonOperator、BashOperator |
| 传输 | S3ToRedshiftOperator、GCSToBigQueryOperator |
| 传感器 | S3KeySensor、DateTimeSensor |
| AI/ML | SageMakerEndpointOperator、VertexAIOperator |

**XCom** — Task 间数据传递：
- 小数据（< 48KB）存数据库
- 大数据应通过外部存储（S3、GCS）

**TaskFlow API**（v2.0+）：
```python
from airflow.decorators import dag, task

@dag(schedule='@daily', start_date=datetime(2024, 1, 1))
def my_dag():
    
    @task
    def extract():
        return {"data": [1, 2, 3]}
    
    @task
    def transform(data):
        return [x * 2 for x in data["data"]]
    
    @task
    def load(data):
        print(data)
    
    data = extract()
    transformed = transform(data)
    load(transformed)

my_dag()
```

### 3.3 执行器架构

```
┌───────────────────────────────────────────────────────────┐
│                     Airflow 架构                            │
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐ │
│  │  Web UI  │  │Scheduler │  │ Triggerer│  │  CLI     │  │
│  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘ │
│       │              │              │              │        │
│  ┌────▼──────────────▼──────────────▼──────────────▼─────┐│
│  │              元数据库 (PostgreSQL)                       ││
│  └───────────────────────────────────────────────────────┘│
│                                                           │
│  ┌───────────────────────────────────────────────────────┐│
│  │              Executor（执行器）                         ││
│  │  ┌──────┐  ┌──────┐  ┌──────┐  ┌──────────────────┐ ││
│  │  │Local │  │Celery│  │ K8s  │  │  ...             │ ││
│  │  │      │  │      │  │      │  │                  │ ││
│  │  └──────┘  └──────┘  └──────┘  └──────────────────┘ ││
│  └───────────────────────────────────────────────────────┘│
└───────────────────────────────────────────────────────────┘
```

Executor 类型：
- **SequentialExecutor** — 单线程串行（开发用）
- **LocalExecutor** — 多进程并行
- **CeleryExecutor** — 分布式（Redis/RabbitMQ + Worker）
- **KubernetesExecutor** — 每个 Task 一个 K8s Pod
- **DaskExecutor** — Dask 分布式

### 3.4 调度模型

- **Schedule Interval** — Cron 表达式或预设（@daily, @hourly）
- **Timetable**（v2.2+）— 自定义调度逻辑
- **Catchup** — 是否补跑历史
- **Backfill** — 手动补跑指定时间段
- **Dataset**（v2.4+）— 数据驱动调度

## 四、关键特性

### 4.1 1000+ Provider Package

| 类别 | Provider |
|------|----------|
| 云 | amazon、google、azure、alibaba |
| 数据库 | postgres、mysql、sqlite、mssql、oracle |
| 大数据 | hdfs、hive、spark、databricks、trino |
| AI/ML | amazon.aws (SageMaker)、google.cloud (Vertex AI) |
| 消息 | slack、discord、email |
| 监控 | datadog、pagerduty、opsgenie |

### 4.2 动态任务映射（v2.3+）

```python
@task
def get_files():
    return ["file1.csv", "file2.csv", "file3.csv"]

@task
def process_file(filename):
    return process(filename)

files = get_files()
process_file.expand(filename=files)
```

### 4.3 异步触发器（v2.2+）

Deferrable Operator 不占用 Worker 槽位：
```python
from airflow.providers.amazon.aws.sensors.s3 import S3KeySensor

wait_for_file = S3KeySensor(
    task_id='wait_for_file',
    bucket_key='data/*.csv',
    deferrable=True,  # 异步等待
)
```

### 4.4 数据集调度（v2.4+）

数据驱动调度，DAG A 产出数据集后自动触发 DAG B：
```python
from airflow.datasets import Dataset

my_dataset = Dataset("s3://bucket/data/")

@task(outlets=[my_dataset])
def produce_data():
    ...

@dag(schedule=[my_dataset])
def consume_dag():
    ...
```

### 4.5 可观测性

- Web UI 实时查看 DAG 状态
- Gantt 图分析任务耗时
- Graph 视图查看依赖关系
- Task Log 查看日志
- Alert 通知（Slack/Email/PagerDuty）

## 五、关键设计决策

1. **DAG 即代码** — Python 文件定义工作流，版本可控，IDE 友好
2. **静态 DAG** — DAG 结构在解析时确定，运行时不能动态改变（与 [[prefect]] 的关键区别）
3. **Scheduler 单点** — 调度器是单点，需要 HA 方案（Standby Scheduler）
4. **XCom 限制** — 小数据传递模型，大数据必须走外部存储
5. **Operator 生态** — 1000+ Provider 由社区维护，质量参差

## 六、开发命令速查

```bash
# 安装
pip install apache-airflow
# 或带 Provider
pip install "apache-airflow[amazon,google,postgres]"

# 初始化
airflow db init
airflow users create --username admin --role Admin --email admin@example.com

# 启动
airflow webserver --port 8080
airflow scheduler

# CLI
airflow dags list
airflow dags trigger my_dag
airflow tasks test my_dag task1 2024-01-01
airflow dags backfill my_dag --start-date 2024-01-01 --end-date 2024-01-31

# Docker
docker compose up -d
```

## 七、与竞品对比

| 维度 | Airflow | [[prefect]] | [[dagster]] | [[temporal]] |
|------|---------|-------------|-------------|--------------|
| 核心概念 | DAG + Operator | Task + Flow | Asset + Job | Workflow + Activity |
| 动态性 | 静态（解析时确定） | 动态（运行时） | 动态 | 动态 |
| 调度 | 强大 | 内置 | 内置 | 事件驱动 |
| 数据传递 | XCom（小数据） | 原生 Python | IO Manager | 原生序列化 |
| 容错 | 重试 | 重试 | 重试 | 最强（状态持久化） |
| 学习曲线 | 陡峭 | 平缓 | 中等 | 中等 |
| 社区 | 最大 | 增长快 | 增长快 | 成熟 |

---

## 相关

- [[prefect]] — 现代 Python 工作流编排（Airflow 替代）
- [[dagster]] — 现代数据编排器（资产思维）
- [[temporal]] — 分布式工作流引擎（最强容错）
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
