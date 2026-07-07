---
title: Langflow 项目架构分析
created: 2026-05-15
updated: 2026-07-06
type: concept
tags: [architecture, python, react, fastapi, monorepo, ai, workflow-engine, component-system, lfx, rbac, plugin-architecture]
sources:
  - https://github.com/langflow-ai/langflow
  - ~/Projects/langflow
confidence: high
related:
  - "[[opensource-project-practices-from-langflow]]"
  - "[[opensource-project-practices-from-temporal]]"
  - "[[ai-workflow-landscape]]"
---

# Langflow 项目架构分析

> Langflow 是一个视觉化 AI 工作流构建平台，用户通过拖拽组件构建 AI Agent 和工作流。本文从整体架构、后端、前端、执行引擎和包管理五个维度分析其架构设计。
>
> **⚠️ 2026-07-06 架构演进**：核心执行引擎已外化到独立包 `lfx`，`backend/base/langflow/graph/` 现为空壳（仅 `re-export` `lfx.graph.*`）。新增 `langflow-stepflow`（备用执行后端）、`langflow_sdk`（HTTP 客户端）、`bundles/`（可选集成）。RBAC 授权层四阶段落地。下文第 0 节为本次演进补充，第 1-8 节为 2026-05-15 原始分析（保留历史视角）。

---

## 0. 架构演进（2026-07-06 补充）

### 0.1 内核/外壳分离：`lfx` 成为真正的执行内核

原先 `lfx` 被定位为"轻量无状态 CLI"，但 2026-07 源码显示**它已是整个项目的执行内核**，主包 `langflow-base` 反而成了壳：

```
src/
├── backend/base/langflow/   # langflow-base：FastAPI 服务 + 路由 + DB + 服务实现
│   ├── graph/__init__.py    # ⚠️ 空壳 —— 仅 from lfx.graph.* re-export Graph/Edge/Vertex
│   ├── api/{v1,v2}/         # HTTP 路由层
│   ├── services/            # 服务实现 + deps.py（FastAPI 依赖注入）
│   ├── custom/              # 自定义组件框架
│   └── components/          # 内置组件
├── lfx/src/lfx/             # ⭐ 真正的内核：图引擎 + 组件库 + 服务接口
│   ├── graph/{graph,vertex,edge,flow_builder,state}/
│   ├── services/            # 服务抽象基类（Base*Service）+ 插件注册
│   ├── components/           # 80+ 供应商集成组件
│   └── custom/              # Component 基类 + code_parser
├── langflow-stepflow/        # Langflow→Stepflow 翻译器（备用执行后端）
├── sdk/                      # langflow_sdk：HTTP 客户端 SDK
└── bundles/{duckduckgo,arxiv,ibm,docling}/  # 可选集成 bundle
```

`backend/base/langflow/graph/__init__.py` 全文就是 shim：

```python
from lfx.graph.edge.base import Edge
from lfx.graph.graph.base import Graph
from lfx.graph.vertex.base import Vertex
from lfx.graph.vertex.vertex_types import CustomComponentVertex, InterfaceVertex, StateVertex
__all__ = ["CustomComponentVertex", "Edge", "Graph", "InterfaceVertex", "StateVertex", "Vertex"]
```

**设计含义**：`lfx` 是"无 UI、无 FastAPI 依赖"的纯执行内核，既能被 `langflow serve` 用，也能被 `lfx serve` / `lfx run` 作为轻量 CLI 直接跑 flow。这是典型的**内核/外壳分离**——AGENTS.md 文档滞后于代码，仍把 graph 描述为 backend 模块。

### 0.2 服务层：工厂反射 DI + 三通道可插拔注册

**`ServiceFactory`**（`factory.py`）用 `get_type_hints(create)` **反射推断依赖**——工厂的 `create()` 参数类型即声明了它依赖哪些其他服务（自动解析为 `ServiceType` 枚举）。依赖不需要手写列表，签名即配置。

```python
class ServiceFactory:
    def __init__(self, service_class: type[Service]):
        self.service_class = service_class
        self.dependencies = infer_service_types(self, import_all_services_into_a_dict())
    def create(self, *args, **kwargs) -> Service:
        return self.service_class(*args, **kwargs)
```

**可插拔服务机制**（`PLUGGABLE_SERVICES.md`）三种注册途径，优先级为 **配置文件 > 装饰器 > entry points**：

| 通道 | 机制 | 优先级 | 场景 |
|------|------|--------|------|
| 配置文件 | `lfx.toml` / `pyproject.toml` `[tool.lfx.*]` | 最高（部署期覆盖） | 现场替换不需改代码 |
| 装饰器 | `@register_service`（import 时即时注册，`override=True` 默认） | 中 | 代码内声明 |
| Entry points | `lfx.<type>.adapters` Python entry point | 最低 | 第三方包分发 |

实例懒创建、单例缓存、随 `ServiceManager` 关闭自动 `teardown`。OSS 版与商业版共用同一壳，只替换 `auth_service` / `authorization_service` 等实现。Adapter 注册同样三通道（`@register_adapter(AdapterType.DEPLOYMENT, "local")`）。

**已知技术债**：`deps.py` 的 `get_service()` 里有 `are_factories_registered()` 检查 + 懒注册 workaround，注释自承 "not optimal, but it works"——启动顺序存在循环依赖隐患。另外 FastAPI 的 `eval_str=True` 强制部分 import 放在 `TYPE_CHECKING` 之外（注释明确指出），削弱了延迟 import 的收益。

### 0.3 RBAC 授权层（四阶段落地，认证 vs 授权严格分离）

授权是独立于认证的**可插拔层**，定义在 `lfx/services/authorization/base.py`：

```
BaseAuthorizationService (抽象)
├── SUPPORTS_CROSS_USER_FETCH: ClassVar[bool]  # 是否支持跨用户取资源
├── is_enabled() → bool
├── enforce(user_id, domain, obj, action) → 决策
└── invalidate_user/invalidate_all()           # 缓存失效
```

OSS 默认 `LANGFLOW_AUTHZ_ENABLED=false`，注册 **pass-through stub**（`LangflowAuthorizationService`）——所有检查返回 allow，但路由守卫和审计行仍照常走通。真正决策需注册插件读 `authz_*` admin 表、写编译规则到 `casbin_rule`。

**请求模型**是四元组 `(subject, domain, object, action)`：

| 维度 | 取值 |
|------|------|
| subject | `user:{uuid}` |
| domain | `project:{uuid} → workspace:{uuid} → *`（更具体的域优先） |
| object | `flow:{uuid}` / `deployment:{uuid}` / `flow:*` 等 |
| action | `read / write / create / delete / execute / deploy` |

**路由守卫**（`services/authorization/guards.py`）按资源类型分函数：`ensure_flow_permission` / `ensure_deployment_permission` / `ensure_project_permission` / `ensure_knowledge_base_permission` / `ensure_variable_permission` / `ensure_file_permission` / `ensure_share_permission`，外加列表过滤 `filter_visible_resources`。

**Phase 3 Share-aware fetch** 是安全关键设计：路由 fetcher 调用 `supports_cross_user_fetch()` 分支。OSS stub 返回 `False` → 保留 owner-scoped 查询；插件返回 `True` → 按 id 加载，由 `ensure_*_permission` 决策，且 `deny_to_404` 工具把 403 转成 404 以保护 UUID 隐私。这避免了"开启 AUTHZ 但没装插件反而放大可见性"的安全回归。

配套：`authz_audit_log`（Phase 4 审计查询 API，超管专用，页大小上限 200）、`authz_share` CRUD（OSS floor：资源 owner 或超管才能管理 share 行）、`7c8d9e0f1a2b_authz_foundations` 迁移种子三个系统角色（viewer/developer/admin，`is_system=True`，`"{resource}:{action}"` 权限 slug）。

### 0.4 图执行引擎：数据驱动调度（非静态 DAG）

引擎核心在 `lfx/graph/`，`Graph` 类约 2500 行：

- **`Graph`**（`graph/graph/base.py`）：`async_start()` / `start()` / `arun()` / `astep()`。执行流：`initialize_run` → 按 `RunnableVerticesManager` 取下一批可运行点 → `build_vertex` 构建并 `process` → 推进 → 事件回调。
- **`Vertex`**：`VertexStates` 状态机。四种子类型（`vertex_types.py`）：`CustomComponentVertex`（用户代码）、`ComponentVertex` / `InterfaceVertex`（内置/入出接口）、`StateVertex`（状态节点）。
- **`Edge`**：`CycleEdge` 支持循环图，不只是 DAG。
- **`RunnableVerticesManager`**：用 `run_map`（后继）、`run_predecessors`（前驱）、`vertices_to_run`（就绪集）、`vertices_being_run`（运行中）四个集合动态推进，支持 cycle 检测与 `ran_at_least_once` 跟踪。这是**数据驱动的调度器**，而非静态拓扑排序——天然支持循环、条件分支、人工中断后续跑。
- **事件流**：`ag_ui.core` 的 `StepStartedEvent` / `StepFinishedEvent` + `EventManager`，前端 SSE 实时收每步构建结果。`build_vertex` 内置 `get_cache_func` / `set_cache_func` 钩子，节点级结果可缓存。

执行模型本质是**异步、流式、增量调度**：每个 vertex 构建完触发 `get_next_runnable_vertices` 计算下一批，`_execute_tasks` 并发执行。`create_subgraph` 支持子图流式迭代。

### 0.5 多执行后端：v2 Workflow API + Stepflow

- **v1**（`api/v1/`，40+ 路由）：完整 CRUD——flows、deployments、projects、folders、knowledge_bases、variables、files、traces、mcp、authz_* 全家桶。
- **v2**（`api/v2/`）：精简执行导向 API，核心 `workflow.py`：`POST /workflow`（sync/stream/background 三模式）、`GET /workflow`（按 job_id 查状态）、`POST /workflow/stop`。300s 同步超时、Developer API 保护、API key 认证。`workflow_reconstruction.py` 从已存 flow 重建可执行图。
- **Stepflow 备用后端**（`langflow-stepflow/`）：`LangflowConverter` 把 Langflow JSON 翻译成 Stepflow YAML（`dependency_analyzer` 做依赖分析、`schema_mapper` 做字段映射、`node_processor` 处理节点），再由 `worker/core_executor.py` 用 `stepflow_py.worker.FlowBuilder` 执行。这是**并行执行后端**，可能是未来替换内置引擎的伏笔，或为特定部署场景（wasm/边缘）准备。

### 0.6 SDK 与 Bundle

- **`langflow_sdk`**（`sdk/`）：同步 + 异步 HTTP 客户端（`client.py` / `_async_client.py` / `_client_common.py`），含 `background_job.py`、`serialization.py`、`testing.py`。让用户用代码而非 UI 驱动 flow。
- **`bundles/`**：duckduckgo / arxiv / ibm / docling 等重依赖集成拆成独立 workspace 包，主包按需引入——避免默认安装拖入巨大依赖。

### 0.7 一句话总结

Langflow 用"**内核外化 + 服务工厂反射 DI + 可插拔 RBAC + 数据驱动图调度**"四件套，把可视化 AI 工作流产品拆成了"可独立复用的引擎 + 可替换的服务实现 + 可插拔的执行后端"，OSS 与商业版共用同一壳。

```
┌─────────────────────────────────────────────────────────────┐
│  frontend (React 19 + @xyflow + Zustand)                    │
└───────────────┬─────────────────────────────────────────────┘
                │ HTTP/SSE
┌───────────────▼─────────────────────────────────────────────┐
│  langflow-base (FastAPI 壳)                                 │
│  ├─ api/v1 (CRUD 40+ 路由)   ├─ api/v2 (workflow 执行)      │
│  ├─ services/deps.py → Depends 注入                          │
│  └─ services/authorization/guards.py (RBAC 守卫)            │
└───────────────┬─────────────────────────────────────────────┘
                │  ServiceManager 单例 + 工厂反射 DI
┌───────────────▼─────────────────────────────────────────────┐
│  lfx (执行内核，无 Web 依赖)                                 │
│  ├─ graph/   Graph + Vertex(4 类) + Edge(cycle) + 调度器    │
│  ├─ services/  Base*Service 抽象 + @register_service 插件   │
│  ├─ custom/   Component 基类 + code_parser                  │
│  └─ components/  80+ 供应商集成                              │
└───────────────┬─────────────────────────────────────────────┘
                │  可选并行后端
┌───────────────▼────────────────┐  ┌─────────────────────────┐
│  langflow-stepflow              │  │  langflow_sdk (HTTP)    │
│  JSON→YAML 翻译 + worker 执行   │  │  sync/async 客户端      │
└─────────────────────────────────┘  └─────────────────────────┘
```

---

## 1. 整体架构概览（2026-05-15 原始分析）

```
┌─────────────────────────────────────────────────────────┐
│                     用户界面 (React)                      │
│         @xyflow/react 图编辑器 + Zustand 状态管理          │
├─────────────────────────────────────────────────────────┤
│                     API 网关 (FastAPI)                    │
│              V1 API (稳定) │ V2 API (简化)                │
├─────────────────────────────────────────────────────────┤
│                     服务层 (Services)                     │
│  Auth │ Database │ Cache │ Storage │ Chat │ Tracing      │
├─────────────────────────────────────────────────────────┤
│                   图执行引擎 (Graph Engine)                │
│           Vertex │ Edge │ State │ Async Executor          │
├─────────────────────────────────────────────────────────┤
│                   组件系统 (Components)                    │
│        LLM │ Tool │ Memory │ VectorStore │ Custom        │
├─────────────────────────────────────────────────────────┤
│              数据层 (SQLAlchemy + Alembic)                 │
│                  PostgreSQL / SQLite                      │
└─────────────────────────────────────────────────────────┘
```

### 技术栈

| 层次 | 技术选型 |
|------|---------|
| 前端框架 | React 19 + TypeScript 5.4 |
| 构建工具 | Vite 7 + SWC |
| UI 组件 | Radix UI + shadcn/ui + Tailwind CSS |
| 状态管理 | Zustand 4 |
| 图可视化 | @xyflow/react 12 (ReactFlow) |
| 数据获取 | React Query 5 + Axios |
| 后端框架 | FastAPI (Python) |
| ORM | SQLAlchemy + SQLModel (异步) |
| 数据库迁移 | Alembic (expand-contract 模式) |
| 包管理 | uv (Python) + npm (Node.js) |
| 容器化 | Docker 多阶段构建 |

---

## 2. Monorepo 结构

### 目录布局

```
langflow/                         # 根目录 = langflow 主包
├── src/
│   ├── backend/
│   │   ├── base/langflow/        # langflow-base 核心包
│   │   │   ├── api/              # FastAPI 路由 (v1/, v2/)
│   │   │   ├── components/       # 内置组件 (100+)
│   │   │   ├── custom/           # 自定义组件框架
│   │   │   ├── services/         # 服务层
│   │   │   ├── graph/            # 图执行引擎
│   │   │   └── helpers/          # 工具函数
│   │   ├── langflow/             # langflow 主包扩展
│   │   └── tests/                # 后端测试
│   ├── frontend/                 # React 前端
│   │   └── src/
│   │       ├── components/       # UI 组件
│   │       ├── stores/           # Zustand 状态
│   │       ├── controllers/API/  # API 层
│   │       ├── CustomNodes/      # 自定义节点
│   │       └── pages/            # 页面组件
│   ├── lfx/                      # LFX 轻量执行器
│   │   └── src/lfx/
│   │       ├── components/       # LFX 组件 (460+)
│   │       ├── graph/            # 独立图引擎
│   │       └── __main__.py       # CLI 入口
│   └── sdk/                      # Python SDK
│       └── langflow_sdk/         # API 客户端
├── docs/                         # Docusaurus 文档站
├── docker/                       # Docker 构建
└── Makefile                      # 统一构建入口
```

### 包依赖关系

```
langflow (1.9.2)                  # 主包：完整 Web 应用
  └── langflow-base[complete]     # 核心框架

langflow-base (0.9.2)             # 核心：API、服务、图引擎、组件系统
  ├── langchain-core              # LLM 编排
  ├── pydantic                    # 数据验证
  ├── sqlalchemy                  # ORM
  └── fastapi                     # Web 框架

lfx (0.4.2)                       # 轻量 CLI 执行器
  ├── langchain-core              # 直接依赖（不依赖 langflow-base）
  └── langflow-sdk                # 用于远程操作

langflow-sdk (0.1.2)              # Python API 客户端
  ├── httpx                       # HTTP 客户端
  └── pydantic                    # 类型定义
```

### uv Workspace 配置

```toml
[tool.uv.workspace]
members = [
    "src/backend/base",   # langflow-base
    ".",                  # langflow 主包
    "src/lfx",            # LFX 执行器
    "src/sdk",            # Python SDK
]
```

### 版本同步

一条命令 `make patch v=X.Y.Z` 同步更新所有包版本，确保发布一致性。

---

## 3. 后端架构

### 3.1 应用启动流程

```
langflow 命令
  → __main__.py (CLI 入口)
    → main.py → setup_app() (FastAPI 工厂)
      → 加载配置 (pydantic-settings)
      → 注册中间件栈
      → 初始化服务管理器
      → 挂载 API 路由
      → 启动 lifespan 上下文
```

### 3.2 中间件栈（按执行顺序）

1. **ContentSizeLimitMiddleware** — 请求大小限制
2. **SentryAsgiMiddleware** — 错误追踪（条件启用）
3. **CORSMiddleware** — 跨域（可配置 origins）
4. **JavaScriptMIMETypeMiddleware** — MIME 类型处理
5. **check_boundary** — 自定义边界检查
6. **forwarded_prefix_middleware** — 反向代理前缀

### 3.3 API 层

**双版本 API 并行**：

```
/api/v1/  ← 稳定版（30+ 路由）
  ├── flows/          # 工作流 CRUD
  ├── chat/           # 聊天接口
  ├── variables/      # 变量管理
  ├── users/          # 用户管理
  ├── api_key/        # API 密钥
  ├── login/          # 认证
  ├── knowledge_bases/# 知识库
  ├── monitor/        # 监控
  └── mcp/            # Model Context Protocol

/api/v2/  ← 简化版（新架构）
  ├── workflow/       # 工作流执行
  ├── files/          # 文件处理
  ├── mcp/            # MCP
  └── registration/   # 组件注册
```

**路由模式**：FastAPI Router 嵌套，主路由 → v1/v2 → 具体路由。Pydantic schema 验证请求/响应。

### 3.4 服务层

**服务工厂模式**（依赖注入）：

```python
class ServiceFactory:
    def __init__(self, service_class: type[Service]):
        self.service_class = service_class
        # 自动推断依赖关系
        self.dependencies = infer_service_types(self, available_services)

    def create(self, *args, **kwargs) -> Service:
        return self.service_class(*args, **kwargs)
```

**服务分类**：

| 类别 | 服务 | 职责 |
|------|------|------|
| 核心 | Database | 数据库会话管理 |
| 核心 | Cache | 缓存层 (Redis) |
| 核心 | Auth | 认证/授权 |
| 核心 | Settings | 配置管理 |
| 功能 | Chat | 聊天会话 |
| 功能 | Flow | 工作流管理 |
| 功能 | Session | 用户会话 |
| 基础设施 | Storage | 文件存储 |
| 基础设施 | Tracing | 链路追踪 |
| 基础设施 | TaskOrchestration | 任务队列 |

**依赖解析**：基于类型提示的自动注入，`ServiceType` 枚举标识服务，工厂模式延迟实例化，支持循环依赖检测。

### 3.5 图执行引擎

**核心概念**：

```
Graph（图）
  ├── Vertex（顶点 = 组件实例）
  │     ├── IDLE → BUILDING → BUILT → ERROR
  │     ├── 输入值管理
  │     └── 结果收集
  ├── Edge（边 = 数据连接）
  │     └── 定义数据流方向
  └── State（状态）
        └── 持久化执行上下文
```

**执行模型**：

- **全异步**：基于 async/await，支持并发执行
- **状态机**：Vertex 有明确的状态转换（IDLE → BUILDING → BUILT/ERROR）
- **锁机制**：防止并发冲突
- **Session 隔离**：每次执行独立的上下文

```python
# Vertex 的核心接口
class Vertex:
    def set_input_value(self, name: str, value: Any) -> None
    def add_result(self, name: str, result: Any) -> None
    def set_state(self, state: str) -> None
    def get_built_result(self)
```

### 3.6 组件系统

**组件是 Langflow 的核心抽象**——每个组件封装一个 AI 功能单元（LLM、工具、记忆等）。

```python
class MyComponent(Component):
    display_name = "My Component"
    description = "What it does"
    icon = "component-icon"  # Lucide 图标名

    inputs = [
        MessageTextInput(name="input_value", display_name="Input"),
    ]
    outputs = [
        Output(display_name="Output", name="output", method="process"),
    ]

    def process(self) -> Message:
        return Message(text=self.input_value)
```

**组件发现机制**：
- 内置组件：`src/backend/base/langflow/components/`（100+）
- 自定义组件：`src/backend/base/langflow/custom/`
- Bundle 组件：通过配置路径动态加载
- 开发模式：`LFX_DEV=1` 动态热加载

**关键约束**：组件的类名是持久化标识符，**绝不能重命名**，否则会破坏所有使用该组件的已保存 Flow。

**Input/Output 类型系统**：
- 动态类型推断（从方法签名推导）
- Schema 验证
- 自定义类型和嵌套结构支持
- 运行时类型检查和转换

### 3.7 数据库层

**技术选型**：SQLAlchemy + SQLModel（类型安全 ORM），异步会话管理。

**CRUD 模式**：

```python
async def get_api_keys(session: AsyncSession, user_id: UUID) -> list[ApiKeyRead]
async def create_api_key(session: AsyncSession, api_key_create: ApiKeyCreate, user_id: UUID) -> UnmaskedApiKeyRead
async def delete_api_key(session: AsyncSession, api_key_id: UUID, user_id: UUID) -> None
```

**迁移策略**：Alembic + expand-contract 模式，通过自定义 AST 校验器强制执行。

---

## 4. 前端架构

### 4.1 应用入口和路由

```
index.tsx → i18n 初始化
  → App.tsx → 暗色模式、全局 Provider
    → routes.tsx → React Router v6
      ├── / → 主页（懒加载）
      ├── /flow/:id → 流程编辑器（懒加载）
      ├── /settings → 设置页
      └── Route Guards → ProtectedRoute / ProtectedAdminRoute / ProtectedLoginRoute
```

**路由守卫**：ProtectedRoute、ProtectedAdminRoute、ProtectedLoginRoute 分别控制访问权限。

### 4.2 状态管理（Zustand）

**模块化 Store 设计**：

| Store | 职责 |
|-------|------|
| `flowStore` | 核心：节点、边、构建状态 |
| `authStore` | 认证状态 |
| `darkStore` | 主题管理 |
| `flowsManagerStore` | Flow CRUD |
| `typesStore` | 组件类型和模板 |
| `alertStore` | 全局通知 |

**模式**：

```typescript
// Selector-based 状态访问
const nodes = useFlowStore((state) => state.nodes);

// Action 解构
const { addNode, deleteNode, onConnect } = useFlowStore((state) => ({
  addNode: state.addNode,
  deleteNode: state.deleteNode,
  onConnect: state.onConnect,
}));
```

Store 之间通过直接 import 通信，Middleware 支持 cookie/localStorage 持久化。

### 4.3 组件组织

```
components/
├── common/              # 跨领域通用组件
│   ├── pageLayout/     # 布局容器
│   └── loadingComponent/ # 加载状态
├── core/               # 核心业务组件
│   ├── flowToolbarComponent/ # 编辑器工具栏
│   ├── playgroundComponent/  # 侧边栏
│   └── assistantPanel/      # AI 助手
└── ui/                 # UI 原子组件 (Radix-based)
    ├── button/
    ├── dialog/
    └── input/
```

**设计原则**：组合优于继承，每个组件独立目录 + index.tsx，严格 TypeScript 接口。

### 4.4 图可视化编辑器

**基于 @xyflow/react (ReactFlow)**：

```
CustomNodes/
├── genericNode/    # 组件节点（LLM、Tool 等）
└── noteNode/       # 注释节点

CustomEdges/        # 自定义连接线渲染
```

**交互特性**：
- 辅助线对齐（Helper Lines）
- 节点分组（嵌套组件）
- 键盘快捷键（复制/粘贴/撤销/重做）
- 类型安全连接验证
- 构建状态可视化（动画指示器）
- 拖拽添加组件

```typescript
// 拖拽添加组件
const onDrop = useCallback((event: React.DragEvent) => {
  const data = JSON.parse(event.dataTransfer.getData(dataKey));
  addComponent(data.node, data.type, { x: event.clientX, y: event.clientY });
}, [addComponent]);
```

### 4.5 API 集成层

```
controllers/API/
├── api.tsx            # Axios 实例 + 拦截器
├── queries/           # React Query hooks
│   ├── flows/        # 工作流操作
│   ├── vertex/       # 节点操作
│   ├── components/   # 组件管理
│   └── auth/         # 认证
└── helpers/           # API 工具
```

**模式**：
- Axios 实例统一处理认证（HttpOnly Cookie）
- React Query 管理服务端状态（缓存、乐观更新、后台刷新）
- 自动 token 刷新和重试
- 流式传输支持（实时构建进度）

### 4.6 国际化

使用 i18next + react-i18next，支持多语言界面。

---

## 5. LFX 轻量执行器

### 定位

LFX 是 Langflow 的**无状态 CLI 版本**——从 JSON 文件执行 AI Flow，无需完整 Web 应用栈。

### 与主包的关键区别

| 维度 | Langflow 主包 | LFX |
|------|--------------|-----|
| 状态 | 有状态（数据库持久化） | 无状态（NoopSession） |
| 依赖 | langflow-base[complete]（全部集成） | langchain-core + langflow-sdk（最小化） |
| 启动 | Web 服务器 + 前端 | CLI 命令 |
| 组件加载 | 数据库驱动 + 动态加载 | 文件加载（JSON/Python 脚本） |
| 用途 | 可视化构建 + 运行 | 纯执行 / CI/CD 集成 |

### CLI 命令结构

```
lfx
├── setup      # init, login
├── authoring  # create, validate, requirements
├── running    # run, serve
└── remote     # status, push, pull, export
```

- `lfx run` — 本地执行 Flow，结果输出到 stdout
- `lfx serve` — 启动 FastAPI 服务，暴露 `/flows/{flow_id}/run` 端点

### 无状态实现

```python
class NoopSession:
    """所有数据库操作都是空操作"""
    async def add(self, *args, **kwargs): pass
    async def commit(self): pass
    async def query(self, *args, **kwargs): return []
```

LFX 有自己的组件实现（460+ 目录），与主包保持接口兼容但独立维护。

---

## 6. 关键架构模式

### 6.1 服务工厂 + 依赖注入

```
ServiceManager
  → ServiceFactory(AuthService)
    → 自动推断依赖 (DatabaseService, CacheService)
      → 延迟实例化
        → 缓存单例
```

基于类型提示的自动解析，无需手动装配。

### 6.2 组件注册与发现

```
多个路径 → 组件发现 → 注册到组件注册表
  → 前端获取组件列表 → 拖拽到画布
    → 后端序列化为 Graph JSON → 图引擎执行
```

### 6.3 异步优先

全栈 async/await：
- FastAPI 异步路由
- SQLAlchemy 异步会话
- 图引擎异步执行 + 锁机制
- 前端 React Query 异步数据获取

### 6.4 事件驱动

事件管理器实现服务间解耦通信，Flow 事件用于实时更新，异步事件处理。

### 6.5 插件/扩展架构

- 组件动态加载（`LFX_DEV=1`）
- MCP (Model Context Protocol) 集成
- 自定义组件支持
- Bundle 路径扩展

---

## 7. Docker 部署架构

### 多阶段构建

```
Stage 1: Builder
  ├── Python 3.12 slim
  ├── uv install（带缓存挂载）
  ├── npm build（前端静态资源）
  └── 创建虚拟环境

Stage 2: Runtime
  ├── Python 3.12 slim (Trixie)
  ├── 复制虚拟环境
  ├── Node.js（前端资源服务）
  └── 非 root 用户 (user:1000)
```

**优化特性**：BuildKit 缓存挂载、多架构支持（AMD64/ARM64）、前后端分离构建。

---

## 8. 架构亮点与权衡

### 亮点

1. **组件系统**：统一抽象，输入/输出类型安全，动态发现——是整个平台的核心竞争力
2. **双版本 API**：V1 稳定 + V2 简化，渐进式演进不破坏现有用户
3. **LFX 分离**：将执行能力独立为轻量 CLI，适合 CI/CD 和自动化场景
4. **Monorepo 管理**：清晰分层，依赖方向明确，版本同步一致

### 权衡

1. **LFX 独立组件**：460+ 组件与主包独立维护，增加了同步成本
2. **NoopSession 模式**：无状态执行牺牲了持久化能力（设计取舍，非缺陷）
3. **双 API 版本**：维护两套路由增加了复杂度（过渡期策略）

---

## 参考

- 项目仓库：https://github.com/langflow-ai/langflow
- 相关笔记：[[opensource-project-practices-from-langflow]]
- 技术栈参考：FastAPI, React 19, @xyflow/react, SQLAlchemy, Zustand, uv
