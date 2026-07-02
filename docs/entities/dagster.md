---
title: Dagster
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [workflow, orchestration, data, python, assets, lineage]
sources:
  - https://github.com/dagster-io/dagster
confidence: 0.9
---

# Dagster

> 现代数据编排器 — Software-Defined Assets 资产思维，数据血缘追踪，一流开发体验。

---

## 一、项目定位

Dagster 由 GraphQL 联合创建者 Nick Schrock 创立，核心创新是 Software-Defined Assets——以数据资产为中心定义工作流，而非以任务为中心。"资产思维"非常适合 ML Pipeline（数据集→特征→模型→评估→部署），天然支持数据血缘追踪。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 11k+ |
| 许可证 | Apache 2.0 |
| 语言 | Python |
| 创建者 | Nick Schrock |
| 公司 | Dagster Labs |
| 官网 | https://dagster.io |

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│              Dagster Web UI (Dagit)                   │
│   Asset Catalog · Lineage Graph · Run History         │
│   Schedule · Sensor · Backfill                        │
├─────────────────────────────────────────────────────┤
│              Dagster Core                             │
│   Asset · Job · Op · Graph · Schedule · Sensor        │
│   IO Manager · Resource · Config · Logger             │
├─────────────────────────────────────────────────────┤
│              执行层                                   │
│   Multiprocess · Celery · K8s · Docker                │
├─────────────────────────────────────────────────────┤
│              存储层                                   │
│   SQLite（本地） · PostgreSQL（生产）                   │
│   IO Manager → S3 / GCS / 本地文件系统                 │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 核心框架 | `dagster` | Asset/Op/Job/Graph |
| Web UI | `dagster-webserver` | Dagit 管理界面 |
| 云服务 | Dagster Cloud | 托管服务（商业） |
| 执行器 | 多种 | Multiprocess/Celery/K8s |
| 数据库 | SQLite / PostgreSQL | 运行元数据 |
| IO Manager | 可插拔 | 数据读写抽象 |

## 三、核心架构

### 3.1 核心概念对比

```
传统编排器（Airflow/Prefect）:
  Task → Task → Task
  （以任务为中心）

Dagster:
  Asset → Asset → Asset
  （以数据资产为中心）
  
  数据集 → 特征 → 模型 → 评估 → 部署
  （天然 ML Pipeline 映射）
```

### 3.2 Software-Defined Assets

```python
from dagster import asset, AssetKey

@asset
def raw_data():
    """原始数据集"""
    return fetch_data()

@asset
def cleaned_data(raw_data):
    """清洗后数据"""
    return clean(raw_data)

@asset
def feature_store(cleaned_data):
    """特征存储"""
    return engineer_features(cleaned_data)

@asset
def trained_model(feature_store):
    """训练好的模型"""
    return train(feature_store)

@asset
def model_evaluation(trained_model, feature_store):
    """模型评估"""
    return evaluate(trained_model, feature_store)
```

资产图自动推导：
```
raw_data → cleaned_data → feature_store → trained_model → model_evaluation
                                         ↗               ↑
                              feature_store ──────────────┘
```

### 3.3 目录结构

```
dagster/
  python_modules/
    dagster/               — 核心框架
      dagster/
        core/
          definitions/       — 定义系统
          execution/         — 执行引擎
          storage/           — 存储
          scheduler/         — 调度
          sensor/            — 传感器
          assets/            — 资产系统
        _core/
          executable_definition.py
        utils/
    dagster-webserver/     — Web UI
    dagster-graphql/       — GraphQL API
    libraries/
      dagster-celery/        — Celery 执行器
      dagster-k8s/           — K8s 执行器
      dagster-aws/           — AWS 集成
      dagster-gcp/           — GCP 集成
      dagster-dbt/           — dbt 集成
      dagster-pandas/        — Pandas 类型
      dagster-spark/         — Spark 集成
```

### 3.4 Op 和 Graph（传统模式）

兼容传统任务模式：
```python
from dagster import op, graph, job

@op
def extract():
    return [1, 2, 3]

@op
def transform(data):
    return [x * 2 for x in data]

@graph
def my_graph():
    transform(extract())

my_job = my_graph.to_job()
```

### 3.5 IO Manager

统一管理数据读写：
```python
from dagster import IOManager, io_manager

class MyIOManager(IOManager):
    def handle_output(self, context, obj):
        # 写入数据
        save_to_s3(context.asset_key, obj)
    
    def load_input(self, context):
        # 读取数据
        return load_from_s3(context.upstream_output.asset_key)
```

### 3.6 Resource 和 Config

```python
from dagster import resource, Config

class MyDatabaseResource:
    def __init__(self, connection_string):
        self.conn = connect(connection_string)

@resource(config_schema={"connection_string": str})
def my_database(init_context):
    return MyDatabaseResource(init_context.resource_config["connection_string"])

# 使用
@asset(required_resource_keys={"db"})
def my_asset(context):
    db = context.resources.db
    ...
```

## 四、关键特性

### 4.1 数据血缘追踪

Dagit UI 自动展示资产血缘图：
- 上游/下游依赖
- 资产状态（最新/过期/失败）
- 影响分析（修改某资产影响哪些下游）

### 4.2 Backfill

增量/全量回填：
```python
# 回填特定资产
dagster asset materialize --select my_asset --backfill
```

### 4.3 Schedule 和 Sensor

```python
from dagster import ScheduleDefinition, SensorDefinition, RunRequest

# 定时调度
daily_schedule = ScheduleDefinition(
    job=my_job,
    cron_schedule="0 8 * * *",
)

# 传感器（事件驱动）
@sensor(job=my_job)
def my_sensor(context):
    if new_data_available():
        yield RunRequest(run_key="new-data")
```

### 4.4 Partition

分区资产（时间/分类）：
```python
from dagster import DailyPartitionsDefinition

daily_partitions = DailyPartitionsDefinition(start_date="2024-01-01")

@asset(partitions_def=daily_partitions)
def daily_data(context):
    date = context.partition_time_window
    return fetch_data(date)
```

### 4.5 测试

一流测试体验：
```python
# 单元测试
def test_cleaned_data():
    result = cleaned_data(raw_data_sample())
    assert result is not None

# 集成测试
def test_job():
    result = my_job.execute_in_process()
    assert result.success
```

## 五、关键设计决策

1. **资产思维** — 以数据资产为中心，而非任务，天然支持 ML Pipeline
2. **IO Manager 抽象** — 数据读写统一管理，解耦存储逻辑
3. **类型系统** — DagsterType + Python 类型注解，编译时检查
4. **Dagit 可视化** — 资产图、血缘、运行历史一站式
5. **增量采纳** — 可从 Op/Graph 传统模式开始，逐步迁移到 Asset

## 六、开发命令速查

```bash
# 安装
pip install dagster dagster-webserver

# 启动 UI
dagster dev  # 本地开发（UI + Daemon）

# 部署
dagster-daemon run  # 生产 Daemon

# CLI
dagster job execute -j my_job
dagster asset materialize --select my_asset
dagster run list
```

## 七、与竞品对比

| 维度 | Dagster | [[apache-airflow]] | [[prefect]] |
|------|---------|-------------------|-------------|
| 核心概念 | Asset | DAG + Operator | Flow + Task |
| 数据传递 | IO Manager | XCom | Python 返回值 |
| 血缘追踪 | 原生 | 需手动 | 有限 |
| 动态性 | 运行时动态 | 解析时静态 | 运行时动态 |
| 测试体验 | 一流 | 困难 | 良好 |
| ML 适配 | 天然 | 需适配 | 良好 |

---

## 相关

- [[apache-airflow]] — 传统工作流调度
- [[prefect]] — 现代 Python 工作流编排
- [[mlflow]] — ML 生命周期管理
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
