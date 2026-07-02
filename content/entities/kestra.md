---
title: Kestra
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [workflow, orchestration, yaml, declarative, java, event-driven]
sources:
  - https://github.com/kestra-io/kestra
confidence: 0.9
---

# Kestra

> 声明式工作流编排平台 — YAML 声明式定义、600+ 插件、事件驱动 + 定时触发、混合技术栈友好。

---

## 一、项目定位

Kestra 是声明式工作流编排平台，独特之处在于 YAML 声明式工作流定义，易于版本控制和协作。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 8k+ |
| 许可证 | Apache 2.0 |
| 语言 | Java (Micronaut) + Vue.js |
| 创建者 | Kestra 团队 |
| 官网 | https://kestra.io |

核心定位：
- **YAML 声明式** — 工作流用 YAML 定义，Git 友好
- **600+ 插件** — 覆盖云服务、数据库、消息队列等
- **事件驱动 + 定时** — 多种触发模式
- **任务重放** — 失败后可从断点继续

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                  前端（Vue.js）                       │
│   Flow Editor · Topology · Executions · Logs          │
├─────────────────────────────────────────────────────┤
│                  Kestra Core（Java/Micronaut）         │
│   Flow Engine · Task Runner · Scheduler · Trigger     │
│   Plugin Registry · Execution Store                   │
├─────────────────────────────────────────────────────┤
│                  插件层（600+）                        │
│   AWS · GCP · Azure · Database · AI/ML · ...          │
├─────────────────────────────────────────────────────┤
│                  存储层                               │
│   PostgreSQL / MySQL · Kafka / RabbitMQ · MinIO        │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 后端 | Java + Micronaut | 高性能微服务框架 |
| 前端 | Vue.js + TypeScript | 管理界面 |
| 数据库 | PostgreSQL / MySQL | 元数据存储 |
| 消息队列 | Kafka / RabbitMQ | 内部事件总线 |
| 对象存储 | MinIO / S3 | 任务 Artifact |
| 部署 | Docker / K8s Helm | 多种方式 |

## 三、核心架构

### 3.1 YAML 工作流定义

```yaml
id: my-workflow
namespace: production
description: "数据处理流水线"

inputs:
  - name: date
    type: DATE
    defaults: "{{ now() | date('yyyy-MM-dd') }}"

tasks:
  - id: extract
    type: io.kestra.plugin.fs.http.Download
    uri: "https://api.example.com/data?date={{ inputs.date }}"

  - id: transform
    type: io.kestra.plugin.scripts.python.Commands
    commands:
      - python transform.py {{ outputs.extract.uri }}
    
  - id: load
    type: io.kestra.plugin.jdbc.postgresql.Copy
    from: "{{ outputs.transform.outputFiles['result.csv'] }}"
    table: analytics.data

errors:
  - id: alert
    type: io.kestra.plugin.notifications.slack.SlackIncomingWebhook
    url: "{{ secret('SLACK_WEBHOOK') }}"
    payload: |
      {"text": "Flow {{ flow.id }} failed!"}
```

### 3.2 核心概念

| 概念 | 说明 |
|------|------|
| Flow | 工作流定义（YAML） |
| Task | 任务单元 |
| Trigger | 触发器（Schedule/Webhook/Event/Flow） |
| Input | 流程输入参数 |
| Output | 任务输出 |
| Namespace | 命名空间（组织 Flow） |
| Label | 标签（分类/过滤） |
| Variable | 变量系统（PEB 模板） |

### 3.3 触发器类型

```yaml
# 定时触发
triggers:
  - id: schedule
    type: io.kestra.core.models.triggers.types.Schedule
    cron: "0 8 * * *"

# Webhook 触发
triggers:
  - id: webhook
    type: io.kestra.core.models.triggers.types.Webhook
    key: my-secret-key

# 事件触发
triggers:
  - id: kafka
    type: io.kestra.plugin.kafka.Trigger
    topic: my-topic
    properties:
      bootstrap.servers: localhost:9092

# Flow 触发（上游完成触发下游）
triggers:
  - id: flow
    type: io.kestra.core.models.triggers.types.Flow
    conditions:
      - type: io.kestra.core.models.conditions.types.ExecutionFlowCondition
        namespace: production
        flowId: upstream-flow
```

### 3.4 任务类型

| 类别 | 任务示例 |
|------|---------|
| 脚本 | Python、Node.js、Shell、R |
| 云 | AWS S3、GCS、Azure Blob |
| 数据库 | PostgreSQL、MySQL、MongoDB、Snowflake |
| 消息 | Kafka、RabbitMQ、Redis |
| AI/ML | OpenAI、Vertex AI |
| HTTP | HTTP Request、Download |
| 文件 | CSV、JSON、Parquet、Avro |
| 数据转换 | DuckDB、dbt |

### 3.5 子流程

```yaml
tasks:
  - id: call-subflow
    type: io.kestra.core.tasks.flows.Subflow
    namespace: production
    flowId: sub-flow
    inputs:
      param: "{{ inputs.date }}"
```

### 3.6 条件分支和循环

```yaml
tasks:
  - id: if-check
    type: io.kestra.core.tasks.flows.If
    condition: "{{ inputs.size > 100 }}"
    then:
      - id: big-data
        type: io.kestra.plugin.scripts.python.Commands
        commands: [python big_process.py]
    else:
      - id: small-data
        type: io.kestra.plugin.scripts.python.Commands
        commands: [python small_process.py]

  - id: parallel
    type: io.kestra.core.tasks.flows.Parallel
    tasks:
      - id: task-a
        type: ...
      - id: task-b
        type: ...
```

## 四、关键特性

### 4.1 任务重放

从失败点重试：
- 可重跑整个流程
- 可从失败任务开始
- 可重跑特定任务

### 4.2 变量系统

PEB（Pebble）模板引擎：
```
{{ inputs.date }}                — 输入参数
{{ outputs.extract.uri }}        — 任务输出
{{ trigger.date }}               — 触发器数据
{{ secret('API_KEY') }}          — 加密密钥
{{ now() | date('yyyy-MM-dd') }} — 函数
```

### 4.3 可观测性

- 实时执行日志
- 任务输出和 Artifact
- 拓扑图可视化
- 执行历史和指标
- 告警通知

### 4.4 插件系统

每个插件是独立的 JAR 包：
```xml
<dependency>
    <groupId>io.kestra.plugin</groupId>
    <artifactId>plugin-aws</artifactId>
</dependency>
```

自定义插件：Java 类实现 TaskInterface。

### 4.5 多租户

- Namespace 隔离
- RBAC 权限
- 审计日志
- 密钥管理

## 五、关键设计决策

1. **YAML 声明式** — 工作流用 YAML 定义，Git 版本控制友好
2. **Java 核心** — 高性能、强类型、企业级稳定
3. **插件即 JAR** — Java 生态插件机制，600+ 开箱即用
4. **事件驱动 + 定时** — 双触发模式，覆盖批量和实时场景
5. **PEB 模板** — 变量和表达式系统统一

## 六、开发命令速查

```bash
# Docker 启动
docker run -p 8080:8080 kestra/kestra:latest server local

# Helm（K8s）
helm install kestra kestra/kestra

# 插件开发
git clone https://github.com/kestra-io/kestra.git
cd kestra
./gradlew build
```

## 七、与竞品对比

| 维度 | Kestra | [[apache-airflow]] | [[prefect]] | [[n8n]] |
|------|--------|-------------------|-------------|---------|
| 定义方式 | YAML | Python | Python | UI + JSON |
| 语言 | Java | Python | Python | TypeScript |
| 插件数 | 600+ | 1000+ | Python 生态 | 400+ |
| AI 能力 | 有插件 | 需集成 | 需集成 | 原生节点 |
| Git 友好 | 是（YAML） | 是（Python） | 是（Python） | 有限 |
| 非技术用户 | 中等 | 困难 | 困难 | 友好 |

---

## 相关

- [[apache-airflow]] — 传统工作流调度
- [[prefect]] — 现代 Python 工作流编排
- [[n8n]] — 开源自动化工作流工具
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
