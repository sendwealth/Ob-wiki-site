---
title: Langflow 项目架构分析
created: 2026-05-15
updated: 2026-05-15
type: concept
tags: [architecture, python, react, fastapi, monorepo, ai, workflow-engine, component-system]
sources:
  - https://github.com/langflow-ai/langflow
  - ~/Projects/langflow
confidence: high
related:
  - "[[opensource-project-practices-from-langflow]]"
  - "[[opensource-project-practices-from-temporal]]"
---

# Langflow 项目架构分析

> Langflow 是一个视觉化 AI 工作流构建平台，用户通过拖拽组件构建 AI Agent 和工作流。本文从整体架构、后端、前端、执行引擎和包管理五个维度分析其架构设计。

---

## 1. 整体架构概览

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
