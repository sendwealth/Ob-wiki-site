---
title: Prefect
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [workflow, orchestration, python, data, scheduling]
sources:
  - https://github.com/PrefectHQ/prefect
confidence: 0.9
---

# Prefect

> 现代 Python 数据工作流编排引擎 — 原生 Python 定义、运行时动态、事件驱动，Airflow 的现代替代品。

---

## 一、项目定位

Prefect 由 Jeremiah Lowin 于 2018 年创建，定位为 Airflow 的现代替代品。核心优势：原生 Python 定义工作流、运行时动态参数和分支、强大可观测性。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 17k+ |
| 许可证 | Apache 2.0 |
| 语言 | Python |
| 创建者 | Jeremiah Lowin |
| 公司 | Prefect Technologies, Inc. |
| 官网 | https://prefect.io |

定位演进：
- **Prefect 1.x** — 强类型、显式 API
- **Prefect 2.x** — 简化 API、增量采纳、动态工作流
- **当前** — 事件驱动 + 自动化 + 云托管

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                Prefect Cloud / Server                 │
│   Dashboard · Automations · Work Pools · Deployments │
├─────────────────────────────────────────────────────┤
│                Prefect Core                          │
│   Flow · Task · State · Runtime Engine                │
│   Events · Automations · Artifacts                   │
├─────────────────────────────────────────────────────┤
│                执行层                                 │
│   ProcessPool · Dask · Ray · K8s · Modal             │
├─────────────────────────────────────────────────────┤
│                存储层                                 │
│   SQLite（本地） · PostgreSQL（Server/Cloud）          │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 核心框架 | `prefect` | Flow/Task/State |
| 服务器 | `prefect-server` | 自托管 API + UI |
| 云服务 | Prefect Cloud | 托管服务（商业） |
| 执行器 | 多种 | Process/Dask/Ray/K8s |
| 数据库 | SQLite / PostgreSQL | 状态存储 |

## 三、核心架构

### 3.1 目录结构

```
prefect/
  src/prefect/
    client/                — API 客户端
    deployments/           — 部署管理
    events/                — 事件系统
    infrastructure/        — 基础设施抽象
    runner/                — Runner 执行
    runtime/               — 运行时
    server/                — 服务器
      api/                  — REST API
      database/             — 数据库
      services/             — 后台服务
    testing/               — 测试工具
    utility/               — 工具函数
    workers/               — Worker 进程
    _internal/             — 内部模块
```

### 3.2 核心概念

**Flow** — 工作流定义：
```python
from prefect import flow, task

@task
def extract():
    return [1, 2, 3]

@task
def transform(data):
    return [x * 2 for x in data]

@flow
def my_pipeline():
    data = extract()
    result = transform(data)
    return result

my_pipeline()
```

**Task** — 可复用的工作单元：
- 自动重试
- 超时控制
- 缓存
- 并发限制
- 结果持久化

**State** — 状态管理：
```
Pending → Running → Completed
                 → Failed → Retrying → Running
                 → Cancelled
```

### 3.3 动态工作流（关键差异化）

与 Airflow 的关键区别——运行时动态：

```python
@flow
def dynamic_pipeline():
    # 运行时决定执行哪些任务
    items = extract()
    for item in items:  # 运行时循环！
        process(item)   # 动态创建任务
```

Airflow 必须在 DAG 解析时确定结构，Prefect 允许运行时动态生成任务。

### 3.4 部署模型

**本地执行**：
```python
my_flow()  # 直接调用
```

**部署到 Prefect Cloud/Server**：
```bash
prefect deploy my_flow.py:my_flow -n my-deployment
prefect worker start -p my-pool
```

**Work Pool + Worker 模型**：
```
┌──────────────────┐     ┌──────────────────┐
│  Prefect Server  │────>│   Work Pool      │
│  (调度+API)      │     │   (队列)         │
└──────────────────┘     └────────┬─────────┘
                                  │
                    ┌─────────────┼─────────────┐
                    │             │             │
              ┌─────▼─────┐┌─────▼─────┐┌─────▼─────┐
              │  Worker 1 ││  Worker 2 ││  Worker 3 │
              │ (Process) ││  (K8s)    ││  (Docker) │
              └───────────┘└───────────┘└───────────┘
```

### 3.5 事件驱动 + 自动化

```python
from prefect import automate

# 自动化规则
automate(
    name="on-failure-notify",
    trigger={"type": "event", "match": {"event": "FLOW_RUN_FAILED"}},
    actions=[{"type": "notification", "slack": "#alerts"}],
)
```

### 3.6 Artifact 和结果

```python
from prefect import artifact

@task
def generate_report():
    # 创建可查看的 Artifact
    artifact(
        type="markdown",
        key="report",
        markdown="# Report\n...",
    )
```

## 四、关键特性

### 4.1 增量采纳

从本地脚本到生产部署的渐进路径：
1. **纯 Python 函数** — 加 `@flow` 装饰器即可
2. **本地执行** — 直接调用
3. **部署** — `prefect deploy` 推送到 Cloud/Server
4. **Worker** — 启动 Worker 执行
5. **监控** — Dashboard 查看状态

### 4.2 可观测性

- 内置 Dashboard — Flow/Task 状态、Timeline
- Artifact — 中间结果可视化
- Log — 结构化日志
- Event — 事件流
- Notification — Slack/Email/Webhook 通知

### 4.3 缓存和结果

```python
@task(cache_key_fn=lambda *args: "my-key", cache_expiration=timedelta(hours=1))
def expensive_computation():
    ...
```

### 4.4 并发控制

```python
@task(tags=["gpu"], concurrency_limit=2)
def gpu_task():
    ...
```

## 五、关键设计决策

1. **原生 Python** — 工作流就是 Python 函数，无 DSL
2. **运行时动态** — 允许循环、条件、动态任务创建（vs Airflow 静态 DAG）
3. **增量采纳** — 从 `@flow` 装饰器开始，逐步增加生产级功能
4. **事件驱动** — 内置事件系统和自动化规则
5. **云+自托管双模式** — Prefect Cloud 商业化，自托管免费

## 六、开发命令速查

```bash
# 安装
pip install prefect

# 本地运行
python my_flow.py

# 部署
prefect init
prefect deploy my_flow.py:my_flow -n prod
prefect worker start -p my-pool

# 服务器（自托管）
prefect server start

# CLI
prefect flow ls
prefect deployment ls
prefect work-pool ls
```

## 七、与竞品对比

| 维度 | Prefect | [[apache-airflow]] | [[dagster]] | [[temporal]] |
|------|---------|-------------------|-------------|--------------|
| 核心概念 | Flow + Task | DAG + Operator | Asset + Job | Workflow + Activity |
| 动态性 | 运行时动态 | 解析时静态 | 运行时动态 | 运行时动态 |
| API 风格 | Python 原生 | Python DSL | Python 原生 | 多语言 |
| 数据传递 | Python 返回值 | XCom | IO Manager | 原生序列化 |
| 容错 | 重试 | 重试 | 重试 | 最强（持久化） |
| 学习曲线 | 平缓 | 陡峭 | 中等 | 中等 |

---

## 相关

- [[apache-airflow]] — 传统工作流调度（Prefect 替代目标）
- [[dagster]] — 现代数据编排器（资产思维）
- [[temporal]] — 分布式工作流引擎
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
