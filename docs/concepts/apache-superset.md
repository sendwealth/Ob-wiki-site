---
title: Apache Superset 完整技术参考
created: 2026-05-11
updated: 2026-05-11
type: concept
tags: [bi, data-visualization, apache, open-source, data-engineering]
---

# Apache Superset 完整技术参考

> **定位**: Apache Superset 是一个现代化的、企业级的数据探索与可视化平台，也是 Apache 软件基金会顶级项目。

## 1. 简介

### 1.1 什么是 Apache Superset

Apache Superset 是一个开源的、现代的数据探索和数据可视化平台。它可以替代或增强专有的商业智能工具。Superset 提供了无代码界面来快速构建图表、强大的基于 Web 的 SQL 编辑器、轻量级的语义层，以及对几乎所有 SQL 数据库和数据引擎的即开即用支持。

### 1.2 历史沿革

- **2015年**: Superset 由 Airbnb 工程团队创建，最初名为 **Panoramix**，后改名 **Caravel**，最终定名 **Superset**
- **2016年**: 进入 Apache 孵化器
- **2021年**: 正式毕业成为 **Apache 顶级项目**（Top-Level Project）
- **当前状态**: 活跃开发中，GitHub 上拥有 **72,000+ Stars**、**17,000+ Forks**

### 1.3 核心价值

- 🎯 **无代码可视化构建器** — 快速拖拽创建图表
- 🔍 **强大的 SQL IDE** — 面向高级用户的 SQL Lab
- 🧩 **语义层** — 定义自定义维度和指标
- 🗄️ **广泛的数据源支持** — 支持 **80+ 种数据库**
- 📊 **40+ 种预装可视化类型** — 从简单柱状图到复杂地理空间可视化
- ⚡ **轻量级缓存层** — 减轻数据库负载
- 🔐 **高度可扩展的安全角色和认证** — RBAC、LDAP、OAuth、SAML 等
- 🌐 **云原生架构** — 为规模化而生
- 📡 **REST API** — 编程化自定义和集成

---

## 2. 架构

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                    Apache Superset 架构                      │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌──────────────┐    ┌──────────────┐    ┌──────────────┐  │
│  │   用户浏览器   │    │   嵌入式 SDK   │    │   REST API    │  │
│  │  (React SPA)  │    │  (iframe)    │    │  (Swagger)   │  │
│  └──────┬───────┘    └──────┬───────┘    └──────┬───────┘  │
│         └───────────────────┼───────────────────┘           │
│                             ▼                               │
│  ┌──────────────────────────────────────────────────────┐  │
│  │            Superset 应用 (Python/Flask)               │  │
│  │  ┌────────────┐ ┌────────────┐ ┌──────────────────┐ │  │
│  │  │ Web Server │ │  API Layer  │ │ React Frontend   │ │  │
│  │  │ (Gunicorn) │ │  (FAB/REST) │ │ (Webpack build)  │ │  │
│  │  └────────────┘ └────────────┘ └──────────────────┘ │  │
│  └──────────────┬──────────────────────┬───────────────┘  │
│                 │                      │                    │
│         ┌───────▼───────┐     ┌───────▼───────┐            │
│         │ 元数据数据库    │     │ 缓存层 (Redis) │            │
│         │ PostgreSQL/    │     │  查询缓存      │            │
│         │ MySQL/SQLite   │     │  会话状态      │            │
│         └───────────────┘     └───────┬───────┘            │
│                                         │                    │
│                                 ┌───────▼───────┐            │
│                                 │ 消息代理       │            │
│                                 │ (Redis/RMQ)   │            │
│                                 └───────┬───────┘            │
│                                         │                    │
│                    ┌────────────────────┼───────────────┐    │
│                    ▼                    ▼               ▼    │
│           ┌──────────────┐  ┌──────────────┐ ┌──────────┐  │
│           │ Celery Worker│  │ Celery Beat  │ │  结果后端  │  │
│           │ (异步查询)    │  │ (定时任务)    │ │ (Redis/S3)│  │
│           └──────────────┘  └──────────────┘ └──────────┘  │
│                                                             │
│                    ┌─────────────────────┐                   │
│                    │    外部数据仓库       │                   │
│                    │ (Snowflake/BigQuery/ │                   │
│                    │  Redshift/ClickHouse │                   │
│                    │  PostgreSQL/etc.)    │                   │
│                    └─────────────────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件

#### Superset 应用

核心应用程序，由 Python (Flask) 后端 + API 层 + React 前端组成。

**技术栈:**
- **后端**: Python + Flask + Flask AppBuilder (FAB)
- **前端**: React + TypeScript + Ant Design + Redux
- **API 层**: REST API（Swagger 文档可用）
- **ORM**: SQLAlchemy
- **异步任务**: Celery + Redis/RabbitMQ

**数据流:**
```
用户请求 → Flask 路由 → 检查缓存 → 缓存未命中 → 生成 SQL →
  发送到数据仓库 → 获取结果 → 缓存结果 → 返回前端渲染
```

#### 元数据数据库

存储图表和仪表盘定义、用户信息、日志等。

| 数据库 | 支持版本 |
|--------|---------|
| PostgreSQL | 10.X ~ 16.X |
| MySQL | 5.7, 8.X |

> ⚠️ 生产环境不推荐使用 SQLite（默认用于开发/快速启动）

#### 缓存层

1. **查询结果缓存** — 图表被加载两次时从缓存拉取
2. **消息代理** — 为 Worker 启用 Alerts & Reports、异步查询、缩略图缓存

推荐使用 **Redis**，也支持 Memcached、SimpleCache 或文件系统。

#### Celery Worker & Beat

- **Worker**: 执行长时间运行的查询、报告生成、缩略图渲染等异步任务
- **Beat**: 调度周期性后台作业

---

## 3. 核心功能

### 3.1 可视化图表类型（40+）

| 分类 | 图表类型 |
|------|---------|
| **基础图表** | 柱状图、折线图、面积图、散点图、饼图、环形图 |
| **高级图表** | 瀑布图、漏斗图、桑基图 (Sankey)、旭日图、树图、雷达图 |
| **时间序列** | 时间序列折线/柱状图、百分比堆叠图、Echarts 时间序列 |
| **地理空间** | 散点地图、等值线图、多边形地图、deck.gl (Grid/Hex/Arc) |
| **表格** | 数据表格、透视表 |
| **其他** | 词云、直方图、箱线图、玫瑰图、子弹图、日历热力图 |

### 3.2 仪表盘

- 拖拽式仪表盘构建器
- **交叉过滤器** — 图表之间联动过滤
- **Drill-to-detail** — 下钻到明细数据
- **Drill-by** — 按维度下钻
- 全局过滤器栏、Tab 页签、Markdown 组件
- Jinja 模板支持、CSS 自定义品牌外观

### 3.3 SQL Lab

内置的强大 SQL IDE：

- 多标签编辑、查询历史、数据库浏览器
- 异步查询（通过 Celery）、Jinja 模板
- 自动格式化、成本估算（Presto/BigQuery/PostgreSQL）

### 3.4 语义层

轻量级语义层，定义自定义维度和指标：

- **计算列** — SQL 表达式定义派生列
- **自定义指标** — SUM、COUNT、AVG 等聚合
- **虚拟数据集** — 基于 SQL 查询定义

### 3.5 Alerts & Reports

- **Alerts**: SQL 条件满足时发送通知
- **Reports**: 按计划发送仪表盘/图表截图
- 通知渠道: Email、Slack、Webhook
- 需要 Celery Beat + 无头浏览器（Selenium/Playwright）

---

## 4. 支持的数据库（80+）

| 类别 | 数据库 |
|------|--------|
| **云数据仓库** | BigQuery、Redshift、Aurora、Snowflake、Databricks |
| **查询引擎** | Presto、Trino、Starburst、Hive、Spark SQL |
| **关系型数据库** | PostgreSQL、MySQL、SQLite、Oracle、MS SQL、Db2 |
| **分析型数据库** | ClickHouse、Druid、Pinot、Greenplum、Vertica |
| **云原生** | Supabase、AlloyDB、Neon |
| **时序** | TimescaleDB |
| **嵌入式** | DuckDB |
| **数据湖** | Iceberg、Kudu、Hudi |

### 连接示例

```python
# PostgreSQL
postgresql+psycopg2://user:password@host:5432/database

# MySQL
mysql+mysqlclient://user:password@host:3306/database

# BigQuery
bigquery://project_id/dataset?credentials_path=/path/to/sa.json

# Snowflake
snowflake://user:password@account/database/schema?warehouse=wh&role=role

# ClickHouse
clickhouse+native://user:password@host:9000/database

# Trino
trino://user@host:8080/catalog/schema

# Databricks
databricks+connector://token@server:443/database?http_path=/sql/1.0/warehouses/id
```

> 💡 Superset 不预装数据库驱动，需要单独安装对应 Python 包

---

## 5. 安装与部署

### 5.1 Docker Compose（推荐开发/测试）

```bash
git clone https://github.com/apache/superset.git
cd superset

# 4种模式可选:
docker compose up                                    # 开发模式
docker compose -f docker-compose-light.yml up        # 轻量模式
docker compose -f docker-compose-non-dev.yml up      # 非开发模式
docker compose -f docker-compose-image-tag.yml up    # 预构建镜像
```

> ⚠️ Docker Compose 不支持高可用，**不推荐用于生产**

### 5.2 pip 安装

```bash
pip install apache-superset
pip install psycopg2-binary  # PostgreSQL 驱动

superset db upgrade
superset fab create-admin --username admin --firstname Admin \
  --lastname User --email admin@superset.com --password admin
superset load_examples  # 可选
superset init
superset run -p 8088 --with-threads --reload --debug
```

### 5.3 Kubernetes + Helm（推荐生产）

```bash
helm repo add superset https://apache.github.io/superset
```

```yaml
# superset-values.yaml
supersetNode:
  replicaCount: 2

supersetWorker:
  replicaCount: 2

supersetCeleryBeat:
  enabled: true

postgresql:
  enabled: true
  auth:
    username: superset
    password: superset
    database: superset

redis:
  auth:
    password: superset

extraConfig: |
  SECRET_KEY = 'your-secure-secret-key-here'
  SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://superset:superset@superset-postgresql:5432/superset'
  FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "EMBEDDED_SUPERSET": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
  }

ingress:
  enabled: true
  ingressClassName: nginx
  hostname: superset.example.com
  tls: true

resources:
  requests:
    cpu: "500m"
    memory: "1Gi"
  limits:
    cpu: "2"
    memory: "4Gi"
```

```bash
helm install superset superset/superset -f superset-values.yaml
```

### 5.4 自定义 Dockerfile

```dockerfile
FROM apache/superset:latest

COPY --chown=superset superset_config.py /app/
ENV SUPERSET_CONFIG_PATH /app/superset_config.py

# 安装额外数据库驱动
RUN pip install psycopg2-binary snowflake-connector-python \
    clickhouse-driver google-cloud-bigquery
```

### 5.5 生产部署检查清单

- [ ] 设置强 `SECRET_KEY`（`openssl rand -base64 42`）
- [ ] 使用 PostgreSQL/MySQL 作为元数据数据库（非 SQLite）
- [ ] 配置 Redis 缓存层
- [ ] 配置 Celery Worker 和 Beat
- [ ] 启用 HTTPS
- [ ] 配置 CSP（Content Security Policy）
- [ ] 设置 `ENABLE_PROXY_FIX = True`
- [ ] 定期备份元数据数据库
- [ ] 启用 CSRF 保护
- [ ] 设置适当的 RBAC 角色

---

## 6. 核心概念

### 6.1 数据集

**物理数据集** — 直接映射到数据库表或视图：
```
数据库 → Schema → 表/视图 → 物理数据集
```

**虚拟数据集** — 通过 SQL 查询定义：
```sql
SELECT o.order_id, o.order_date, o.total_amount,
       c.customer_name, c.region
FROM orders o
JOIN customers c ON o.customer_id = c.customer_id
WHERE o.status = 'completed'
```

### 6.2 指标与计算列

```sql
-- 指标（聚合度量）
SUM(revenue)                                        → 总收入
COUNT(DISTINCT user_id)                             → 活跃用户数

-- 计算列（派生列）
profit_margin = profit / revenue * 100
age_group = CASE WHEN age < 25 THEN '18-24' ELSE '25+' END
```

### 6.3 行级安全（RLS）

基于用户角色过滤数据行，支持两种类型：
- **Regular**: 属于指定角色时应用过滤
- **Base**: 对所有用户应用，豁免角色除外

```
Group Key 组合逻辑:
(dept) department='Finance'      ─┐
(dept) department='Marketing'    ├─ OR
(region) region='Europe'         ─┘ AND

结果: (dept='Finance' OR dept='Marketing') AND (region='Europe')
```

### 6.4 缓存策略

缓存超时优先级（从高到低）：单个图表 → 数据集 → 数据库 → `DATA_CACHE_CONFIG` 默认值

```python
# 必需缓存
FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
}

EXPLORE_FORM_DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_explore_',
    'CACHE_REDIS_URL': 'redis://localhost:6379/0'
}

# 图表数据缓存
DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 3600,
    'CACHE_KEY_PREFIX': 'superset_data_',
    'CACHE_REDIS_URL': 'redis://localhost:6379/1'
}
```

---

## 7. 自定义与扩展

### 7.1 自定义可视化插件

```javascript
import { t, ChartMetadata, ChartPlugin } from '@superset-ui/core';
import transformProps from './transformProps';
import ExampleChart from './ExampleChart';

export default class ExampleChartPlugin extends ChartPlugin {
  constructor() {
    const metadata = new ChartMetadata({
      description: 'Example chart plugin',
      name: t('Example Chart'),
      thumbnail: 'path/to/thumbnail.png',
    });
    super({
      loadChart: () => import('./ExampleChart'),
      metadata,
      transformProps,
    });
  }
}
```

### 7.2 嵌入式 SDK

```javascript
import { embedDashboard } from '@superset-ui/embedded-sdk';

embedDashboard({
  id: 'dashboard-uuid',
  supersetDomain: 'https://superset.example.com',
  mountPoint: document.getElementById('superset-container'),
  fetchGuestToken: () => fetchTokenFromBackend(),
  dashboardUiConfig: {
    hideTitle: true,
    filters: { expanded: false },
  },
});
```

后端获取 Guest Token：

```python
import requests

def fetch_guest_token():
    # 登录
    login = requests.post(
        'https://superset.example.com/api/v1/security/login',
        json={'username': 'svc', 'password': 'pwd', 'provider': 'db'}
    )
    token = login.json()['access_token']

    # 获取 guest token
    resp = requests.post(
        'https://superset.example.com/api/v1/security/guest_token/',
        headers={'Authorization': f'Bearer {token}'},
        json={
            'user': {'username': 'embedded_user'},
            'resources': [{'type': 'dashboard', 'id': 'uuid'}],
            'rls': [],
        }
    )
    return resp.json()['token']
```

> 需要启用 `FEATURE_FLAGS = {"EMBEDDED_SUPERSET": True}`

### 7.3 REST API

Swagger 文档: `https://your-superset/swagger/v1`

```bash
# 认证
POST /api/v1/security/login

# CRUD
GET/POST   /api/v1/chart/
GET/PUT/DEL /api/v1/chart/{id}
GET/POST   /api/v1/dashboard/
GET/POST   /api/v1/dataset/
GET/POST   /api/v1/database/

# 安全
POST /api/v1/security/guest_token/
```

---

## 8. 安全模型

### 8.1 RBAC 内置角色

| 角色 | 描述 |
|------|------|
| **Admin** | 所有权限，可授予/撤销其他用户权限 |
| **Alpha** | 访问所有数据源，只能修改自己的对象 |
| **Gamma** | 有限访问，只能消费授权的数据源 |
| **sql_lab** | SQL Lab 访问权限 |
| **Public** | 匿名用户查看仪表盘 |

> ⚠️ 不要修改内置角色的权限，`superset init` 会重置

### 8.2 认证后端

| 认证方式 | 配置 |
|---------|------|
| 数据库 | 默认 |
| LDAP | `AUTH_TYPE = AUTH_LDAP` |
| OAuth 2.0 | Google、GitHub、Keycloak 等 |
| SAML | `AUTH_TYPE = AUTH_SAML` |
| OpenID Connect | 通过 OAuth 配置 |
| API Key | `FAB_API_KEY_ENABLED = True` |

OAuth 配置示例（Google + Keycloak）：

```python
from flask_appbuilder.security.manager import AUTH_OAUTH

AUTH_TYPE = AUTH_OAUTH

OAUTH_PROVIDERS = [
    {
        'name': 'google',
        'token_key': 'access_token',
        'icon': 'fa-google',
        'remote_app': {
            'client_id': 'your-client-id',
            'client_secret': 'your-client-secret',
            'api_base_url': 'https://www.googleapis.com/oauth2/v2/',
            'client_kwargs': {'scope': 'email profile'},
            'access_token_url': 'https://accounts.google.com/o/oauth2/token',
            'authorize_url': 'https://accounts.google.com/o/oauth2/auth',
        }
    },
    {
        'name': 'keycloak',
        'token_key': 'access_token',
        'icon': 'fa-key',
        'remote_app': {
            'client_id': 'superset',
            'client_secret': 'your-client-secret',
            'api_base_url': 'https://keycloak.example.com/realms/your-realm/protocol/openid-connect/',
            'client_kwargs': {'scope': 'openid profile email'},
            'access_token_url': 'https://keycloak.example.com/realms/your-realm/protocol/openid-connect/token',
            'authorize_url': 'https://keycloak.example.com/realms/your-realm/protocol/openid-connect/auth',
        }
    }
]
```

---

## 9. 最佳实践

### 9.1 Celery 异步查询

```python
class CeleryConfig:
    broker_url = "redis://redis:6379/0"
    imports = ("superset.sql_lab", "superset.tasks.scheduler")
    result_backend = "redis://redis:6379/2"
    worker_prefetch_multiplier = 10
    task_acks_late = True
    task_annotations = {
        "sql_lab.get_sql_results": {"rate_limit": "100/s"},
    }

CELERY_CONFIG = CeleryConfig
```

```bash
# 启动 Worker
celery --app=superset.tasks.celery_app:app worker --pool=prefork -O fair -c 4

# 启动 Beat（只运行一个实例）
celery --app=superset.tasks.celery_app:app beat

# 监控（可选）
pip install flower
celery --app=superset.tasks.celery_app:app flower
```

### 9.2 性能调优

| 方面 | 建议 |
|------|------|
| Gunicorn | `-w 10 -k gevent --worker-connections 1000` |
| 数据库连接池 | 配置 SQLAlchemy 连接池大小 |
| 缓存策略 | 热点数据长 TTL，按图表/数据集精细控制 |
| 分布式协调 | 启用 `DISTRIBUTED_COORDINATION_CONFIG` |
| 查询超时 | 设置合理 SQL 超时时间 |
| 数据仓库端 | 物化视图、分区表、聚合表 |

### 9.3 生产配置模板

```python
# superset_config.py
import os
from redis import Redis

SECRET_KEY = os.environ.get('SUPERSET_SECRET_KEY', 'CHANGE_ME')
SQLALCHEMY_DATABASE_URI = 'postgresql+psycopg2://superset:pwd@db:5432/superset'
ROW_LIMIT = 5000

REDIS_URL = 'redis://localhost:6379/0'

FILTER_STATE_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 86400,
    'CACHE_KEY_PREFIX': 'superset_filter_',
    'CACHE_REDIS_URL': REDIS_URL,
}

DATA_CACHE_CONFIG = {
    'CACHE_TYPE': 'RedisCache',
    'CACHE_DEFAULT_TIMEOUT': 3600,
    'CACHE_KEY_PREFIX': 'superset_data_',
    'CACHE_REDIS_URL': REDIS_URL,
}

WTF_CSRF_ENABLED = True
ENABLE_PROXY_FIX = True
SESSION_SERVER_SIDE = True
SESSION_TYPE = "redis"
SESSION_REDIS = Redis.from_url(REDIS_URL)

FEATURE_FLAGS = {
    "ALERT_REPORTS": True,
    "EMBEDDED_SUPERSET": True,
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_RBAC": True,
    "DRILL_BY": True,
}
```

---

## 10. 与其他工具对比

| 特性 | **Superset** | **Metabase** | **Redash** | **Tableau** | **Grafana** |
|------|-------------|-------------|-----------|------------|------------|
| 开源 | ✅ Apache 2.0 | ✅ AGPL v3 | ✅ Apache 2.0 | ❌ 商业 | ✅ AGPL v3 |
| 语言 | Python/React | Clojure/React | Python/React | C++/JS | Go/React |
| 可视化类型 | 40+ | ~15 | ~10 | 50+ | 25+ |
| SQL 编辑器 | ✅ SQL Lab | ✅ | ✅ 核心功能 | ❌ 有限 | ✅ |
| 语义层 | ✅ 轻量 | ✅ 内置 | ❌ | ✅ 强大 | ❌ |
| 嵌入能力 | ✅ SDK | ✅ | ✅ iframe | ✅ | ✅ iframe |
| RBAC | ✅ 精细 | ✅ 基础 | ✅ 基础 | ✅ 精细 | ✅ 基础 |
| 数据库支持 | 80+ | 20+ | 30+ | 80+ | 30+ |
| 适用场景 | 通用 BI | 业务用户 | SQL 聚焦 | 企业级 BI | 监控/时序 |
| 学习曲线 | 中等 | 低 | 低 | 高 | 中等 |
| GitHub Stars | 72K+ | 40K+ | 26K+ | N/A | 65K+ |

**选择建议:**
- **Superset**: 丰富可视化 + 强大 SQL + 企业级安全 + 广泛数据源
- **Metabase**: 非技术用户，简单易用
- **Redash**: SQL 为核心的团队
- **Tableau**: 预算充足，最强可视化
- **Grafana**: 基础设施监控、时序数据

---

## 11. 学习资源

### 官方

| 资源 | 链接 |
|------|------|
| 官方网站 | https://superset.apache.org |
| 用户文档 | https://superset.apache.org/user-docs/ |
| 管理员文档 | https://superset.apache.org/admin-docs/ |
| 开发者文档 | https://superset.apache.org/developer-docs/ |
| GitHub | https://github.com/apache/superset |
| Helm Chart | https://github.com/apache/superset/tree/master/helm/superset |

### 社区

- **Slack**: https://join.slack.com/t/apache-superset/
- **GitHub Discussions**: https://github.com/apache/superset/discussions
- **邮件列表**: dev@superset.apache.org
- **Stack Overflow**: 标签 `#apache-superset`

---

> 📝 更新时间: 2026-05-11 | 📚 来源: Apache Superset 官方文档
> GitHub Stars: 72K+ | 支持数据库: 80+ | 可视化类型: 40+

## 相关页面

- [[agentic-rag]] — AI Agent 与数据系统的结合
- [[tanzhen]] — 探真平台，涉及数据验证与可视化需求
