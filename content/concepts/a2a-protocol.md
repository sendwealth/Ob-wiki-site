---
title: A2A Protocol (Agent-to-Agent) 深度技术参考
created: 2026-05-14
updated: 2026-05-14
type: concept
tags: [a2a, agent-protocol, google, interoperability, mcp, multi-agent]
---

# A2A Protocol (Agent-to-Agent) 深度技术参考

> Google 主导、Linux Foundation 托管的开放协议，让不同框架/厂商构建的 AI Agent 以 **Agent 对等身份**（而非工具）互相通信协作。
> 当前版本：**v1.0.0**（2026-03-12）| GitHub: 23K+ ⭐ | Apache 2.0
> Source: https://github.com/google/A2A | Spec: https://a2a-protocol.org/

## 一、定位与价值

### 1.1 解决什么问题

```
当前 AI Agent 生态碎片化：

┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐
│ LangChain │  │  ADK     │  │ CrewAI   │  │ AutoGen  │
│ Agent    │  │  Agent   │  │  Agent   │  │  Agent   │
└─────┬────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘
      │             │             │              │
      └─────────────┴──────┬──────┴──────────────┘
                           │
                     A2A Protocol
                    （统一通信层）
```

不同框架的 Agent 各自闭环，无法互操作。A2A 提供一个**框架无关**的通信协议，让任何 Agent 都能发现、调用、协作。

### 1.2 与 MCP 的关系

| 维度 | A2A | MCP (Model Context Protocol) |
|------|-----|------------------------------|
| 定位 | Agent ↔ Agent 协作 | Agent ↔ 工具/资源 连接 |
| 类比 | 人与人之间对话 | 人使用工具（锤子、搜索引擎） |
| 粒度 | 应用层协议（对等） | 资源层协议（主从） |
| 核心 | 发现、任务、协商 | 工具描述、调用、结果 |

```
User → Agent A (A2A Client)
         │
         ├── A2A ──→ Agent B (A2A Server)
         │              │
         │              ├── MCP ──→ 数据库
         │              ├── MCP ──→ API
         │              └── MCP ──→ 文件系统
         │
         └── A2A ──→ Agent C
```

**互补关系**：Agent 之间用 A2A 协作，单个 Agent 内部用 MCP 连接工具和资源。

## 二、核心概念

### 2.1 角色模型

```
┌─────────────┐                         ┌─────────────┐
│ A2A Client  │  ──── A2A Protocol ───► │ A2A Server  │
│ (发起方)    │                          │ (Remote     │
│             │  ◄─── A2A Protocol ────  │  Agent)     │
└─────────────┘                         └─────────────┘
```

- **A2A Client**：发起请求的应用或 Agent（代表用户或系统）
- **A2A Server (Remote Agent)**：暴露 A2A 端点、处理任务并返回结果的 Agent

角色是对称的 —— 一个 Agent 可以同时是 Client 和 Server。

### 2.2 核心数据对象

```
┌────────────────────────────────────────────────────────┐
│                    Agent Card                          │
│  身份 + 能力 + 技能 + 端点 + 认证要求                    │
└───────────────────────┬────────────────────────────────┘
                        │ discovery
                        ▼
┌────────────────────────────────────────────────────────┐
│                      Task                              │
│  唯一 ID + 状态机 + 历史消息 + 输出 Artifact            │
│                                                        │
│  ┌─────────┐    ┌──────────┐    ┌────────────────┐   │
│  │ Message │    │ Message  │    │   Artifact     │   │
│  │ (user)  │ →  │ (agent)  │ →  │  (输出结果)     │   │
│  │  Parts  │    │  Parts   │    │    Parts       │   │
│  └─────────┘    └──────────┘    └────────────────┘   │
└────────────────────────────────────────────────────────┘
```

### 2.3 七大核心概念

| 概念 | 说明 |
|------|------|
| **Agent Card** | JSON 元数据文档：身份、能力、技能、端点、认证。发布在 `/.well-known/agent-card.json` |
| **Message** | Client ↔ Server 的一次通信轮次，包含 `role`（user/agent）和一个或多个 `Part` |
| **Task** | 有状态的工作单元，唯一 ID，有明确的生命周期 |
| **Part** | 最小内容单元：文本、文件引用、结构化数据 |
| **Artifact** | Agent 产出的输出（文档、图片、结构化数据），由 `Part` 组成 |
| **Streaming** | 通过 SSE 实时推送任务更新（状态变更、Artifact 片段） |
| **Push Notification** | 异步 webhook 回调，适用于长时间运行或断线场景 |

## 三、Agent Card（发现机制）

### 3.1 发现途径

1. **Well-Known URI**：`https://{domain}/.well-known/agent-card.json`（标准化）
2. **注册中心/目录**：查询 Agent 目录服务
3. **直接配置**：预配置 Agent Card URL

### 3.2 Agent Card 结构

```json
{
  "name": "GeoRoute Agent",
  "description": "AI agent for route planning and navigation",
  "supportedInterfaces": [
    {
      "url": "https://geo.example.com/a2a/v1",
      "protocolBinding": "JSONRPC",
      "protocolVersion": "1.0"
    },
    {
      "url": "https://geo.example.com/a2a/grpc",
      "protocolBinding": "GRPC",
      "protocolVersion": "1.0"
    },
    {
      "url": "https://geo.example.com/a2a/json",
      "protocolBinding": "HTTP+JSON",
      "protocolVersion": "1.0"
    }
  ],
  "provider": {
    "organization": "Example Geo Services Inc.",
    "url": "https://www.example.com"
  },
  "iconUrl": "https://geo.example.com/icon.png",
  "version": "1.2.0",
  "documentationUrl": "https://docs.example.com",
  "capabilities": {
    "streaming": true,
    "pushNotifications": true,
    "stateTransitionHistory": false,
    "extendedAgentCard": true
  },
  "securitySchemes": {
    "google": {
      "openIdConnectSecurityScheme": {
        "openIdConnectUrl": "https://accounts.google.com/.well-known/openid-configuration"
      }
    }
  },
  "security": [{ "schemes": ["google"] }],
  "skills": [
    {
      "id": "route-planning",
      "name": "Route Planning",
      "description": "Plan optimal routes between locations",
      "examples": ["Plan a route from Tokyo to Osaka"]
    }
  ]
}
```

### 3.3 关键字段说明

| 字段 | 必需 | 说明 |
|------|------|------|
| `name` | ✅ | Agent 名称 |
| `description` | ✅ | 功能描述 |
| `supportedInterfaces` | ✅ | 支持的协议绑定列表（URL + 协议 + 版本） |
| `provider` | ❌ | 提供者信息（组织、URL） |
| `version` | ❌ | Agent 版本号 |
| `capabilities` | ✅ | 能力声明：streaming、pushNotifications、stateTransitionHistory、extendedAgentCard |
| `securitySchemes` | ❌ | 支持的认证方案 |
| `security` | ❌ | 安全要求声明 |
| `skills` | ✅ | 技能列表（id + name + description + examples） |

### 3.4 Extended Agent Card

公开 Agent Card 可能不包含所有信息。认证后可通过 `GetExtendedAgentCard` 获取更详细的卡片（额外技能、速率限制、配额等）。

## 四、Task 生命周期

### 4.1 状态机

```
                    ┌──────────────┐
                    │   SUBMITTED  │  ← 初始状态（新 Task 创建）
                    └──────┬───────┘
                           │
                           ▼
                    ┌──────────────┐
              ┌────►│    WORKING   │  ← Agent 正在处理
              │     └──┬───┬───┬──┘
              │        │   │   │
              │        │   │   ▼
              │        │   │  ┌──────────────┐
              │        │   │  │INPUT_REQUIRED│  ← 需要用户输入
              │        │   │  └──────┬───────┘
              │        │   │         │ (用户提供输入)
              │        │   └─────────┘
              │        │
              │        ▼   ┌──────────────┐
              │        └──►│ AUTH_REQUIRED│  ← 需要认证/授权
              │            └──────┬───────┘
              │                   │ (用户提供凭据)
              │                   └──────────┐
              │                              │
              │    ┌─────────────────────────┘
              │    │
              │    ▼
              │  ┌───────────┐     ┌───────────┐
              └──│ COMPLETED │     │  FAILED   │
                 └───────────┘     └───────────┘
                 ┌───────────┐     ┌───────────┐
                 │ CANCELED  │     │ REJECTED  │
                 └───────────┘     └───────────┘
```

### 4.2 状态分类

| 类型 | 状态 | 说明 |
|------|------|------|
| 终态 | `COMPLETED` | 任务成功完成 |
| 终态 | `FAILED` | 任务失败 |
| 终态 | `CANCELED` | 任务被取消 |
| 终态 | `REJECTED` | 任务被拒绝 |
| 中断态 | `INPUT_REQUIRED` | 需要用户提供更多输入 |
| 中断态 | `AUTH_REQUIRED` | 需要用户提供认证/授权 |
| 活跃态 | `WORKING` | Agent 正在处理 |
| 初始态 | `SUBMITTED` | 任务已提交 |

### 4.3 执行模式

```python
# 阻塞模式（默认）：等待任务到达终态或中断态
response = client.send_message(message, config={"return_immediately": False})

# 非阻塞模式：立即返回，由调用者轮询或订阅
response = client.send_message(message, config={"return_immediately": True})
# 后续通过 get_task() 轮询，或 subscribe_to_task() SSE 订阅
```

### 4.4 Context（上下文分组）

`contextId` 将多个 Task 和 Message 逻辑分组为同一会话：

```
Context: "session-abc"
├── Task 1 (route planning)     ← contextId = "session-abc"
├── Task 2 (hotel booking)      ← contextId = "session-abc"
└── Message (preference update)  ← contextId = "session-abc"
```

Agent 可以用 contextId 维护跨多次交互的内部状态和对话历史。

## 五、协议操作

### 5.1 核心操作

| 操作 | 说明 | 对应 REST |
|------|------|-----------|
| `SendMessage` | 发送消息，创建/延续 Task | `POST /message:send` |
| `SendStreamingMessage` | 流式发送消息（SSE 响应） | `POST /message:stream` |
| `GetTask` | 获取 Task 当前状态 | `GET /tasks/{id}` |
| `ListTasks` | 列出所有 Task | `GET /tasks` |
| `CancelTask` | 取消 Task | `POST /tasks/{id}:cancel` |
| `SubscribeToTask` | 订阅 Task 更新（SSE） | `POST /tasks/{id}:subscribe` |
| `GetAgentCard` | 获取公开 Agent Card | `GET /.well-known/agent-card.json` |
| `GetExtendedAgentCard` | 获取扩展 Agent Card（需认证） | `GET /extendedAgentCard` |
| Push Notification 配置 | 管理 webhook 回调 | CRUD `/tasks/{id}/pushNotificationConfigs` |

### 5.2 SendMessage 流程

```
Client                              Server (Remote Agent)
  │                                       │
  │  SendMessage(message, config)         │
  │──────────────────────────────────────►│
  │                                       │  创建/更新 Task
  │                                       │  执行 Agent 逻辑
  │                                       │
  │  返回 Task (含状态 + Artifact)         │
  │◄──────────────────────────────────────│
  │
  │  或直接返回 Message（无需 Task）
  │◄──────────────────────────────────────│
```

### 5.3 Streaming 模式

```
Client                              Server
  │  SendStreamingMessage              │
  │──────────────────────────────────►│
  │                                    │
  │  SSE: TaskStatusUpdate (working)   │
  │◄──────────────────────────────────│
  │  SSE: ArtifactUpdate (partial)     │
  │◄──────────────────────────────────│
  │  SSE: TaskStatusUpdate (working)   │
  │◄──────────────────────────────────│
  │  SSE: ArtifactUpdate (final)       │
  │◄──────────────────────────────────│
  │  SSE: TaskStatusUpdate (completed) │
  │◄──────────────────────────────────│
  │  [stream closes]                   │
```

### 5.4 Push Notification 模式

适用于长时间运行的任务（Agent 处理可能数小时）：

```
Client                              Server                    Webhook URL
  │                                    │                         │
  │  SendMessage(return_immediately)   │                         │
  │──────────────────────────────────►│                         │
  │                                    │                         │
  │  返回 Task (working)               │                         │
  │◄──────────────────────────────────│                         │
  │                                    │                         │
  │  CreatePushNotificationConfig      │                         │
  │──────────────────────────────────►│                         │
  │                                    │                         │
  │  ... 客户端断开，做其他事情 ...      │                         │
  │                                    │  任务完成                │
  │                                    │────────────────────────►│
  │                                    │  POST webhook           │
  │                                    │  {taskId, status, ...}  │
  │                                    │                         │
```

## 六、协议绑定（三层架构）

A2A 规范分为三层：

```
Layer 1: Data Model (ProtoBuf)  ← 所有绑定的规范源
    │
Layer 2: Abstract Operations    ← 框架无关的操作定义
    │
Layer 3: Protocol Bindings      ← 具体传输映射
    ├── JSON-RPC 2.0 over HTTP(S)  ← 默认绑定
    ├── gRPC (ProtoBuf)            ← 高性能场景
    └── HTTP+JSON/REST             ← 简单集成
```

### 6.1 JSON-RPC 绑定（默认）

```json
// 请求
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "ROLE_USER",
      "parts": [{"text": "Plan a route from Tokyo to Osaka"}]
    },
    "configuration": {
      "return_immediately": false
    }
  }
}

// 响应
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "task": {
      "id": "task-uuid-123",
      "status": {"state": "COMPLETED"},
      "artifacts": [
        {"parts": [{"text": "Route: Tokyo → Nagoya → Osaka, 5h 30m"}]}
      ]
    }
  }
}
```

### 6.2 版本协商

通过 HTTP Header 传递协议版本：

```http
POST /rpc HTTP/1.1
Host: agent.example.com
A2A-Version: 1.0
A2A-Extensions: https://example.com/extensions/geolocation/v1
```

- Client 发送 `A2A-Version` header
- Server 按请求版本处理，不支持则返回 `VersionNotSupportedError`
- 扩展通过 `A2A-Extensions` header 声明

### 6.3 三种绑定对比

| 特性 | JSON-RPC | gRPC | HTTP+JSON/REST |
|------|----------|------|----------------|
| 传输 | HTTP(S) | HTTP/2 (TLS) | HTTP(S) |
| 格式 | JSON | ProtoBuf | JSON |
| 流式 | SSE | Server Streaming | SSE |
| 方法命名 | PascalCase | PascalCase | RESTful URL |
| 适用场景 | 通用 | 高性能/低延迟 | 简单集成/浏览器 |

## 七、数据模型

### 7.1 Part 类型（最小内容单元）

```jsonc
// 文本 Part
{"text": "Hello, world!"}

// 文件 Part（内联）
{"raw": "iVBORw0KGgo...", "filename": "diagram.png", "mediaType": "image/png"}

// 文件 Part（引用）
{"url": "https://example.com/file.pdf", "filename": "report.pdf"}

// 结构化数据 Part
{"data": {"key": "value"}, "mediaType": "application/json"}
```

### 7.2 Message vs Artifact

| 维度 | Message | Artifact |
|------|---------|----------|
| 用途 | 通信（输入/对话） | 输出（结果/产出物） |
| 方向 | 双向（user/agent） | 单向（agent → client） |
| 持久化 | 不保证全量持久 | 与 Task 绑定持久化 |
| 典型内容 | 用户指令、Agent 回复 | 文档、图片、结构化数据 |

### 7.3 Extension 机制

Agent Card 中声明支持的扩展：

```json
{
  "capabilities": {
    "extensions": [
      {
        "uri": "https://standards.org/extensions/citations/v1",
        "description": "Citation formatting and source verification",
        "required": false
      }
    ]
  }
}
```

Client 通过 `A2A-Extensions` header 协商使用哪些扩展。

## 八、安全模型

### 8.1 传输安全

- 生产环境 **必须** HTTPS/TLS
- 推荐 TLS 1.3+
- Server 身份通过 TLS 证书验证

### 8.2 认证流程

```
1. Client 读取 Agent Card → securitySchemes
2. Client 获取凭据（out-of-band）
3. Client 在请求中携带凭据（Authorization header）
4. Server 验证凭据
```

支持的认证方案：OpenID Connect、OAuth 2.0、API Key、自定义方案。

### 8.3 Agent Card 签名

Agent Card 可通过 JWS (JSON Web Signatures) 签名，防止篡改：

```json
{
  "agentCardSignature": {
    "payload": "<base64-encoded-card>",
    "signature": "<base64-signature>",
    "signingAlgorithm": "RS256"
  }
}
```

## 九、SDK 生态

| 语言 | 包 | 安装 |
|------|-----|------|
| Python | `a2a-sdk` | `pip install a2a-sdk` |
| Go | `a2a-go` | `go get github.com/a2aproject/a2a-go` |
| JavaScript | `@a2a-js/sdk` | `npm install @a2a-js/sdk` |
| Java | Maven | A2A Java SDK |
| .NET | NuGet | `dotnet add package A2A` |

### 9.1 第三方集成

- **LangChain**：`a2a-langgraph`（LangGraph 上的 A2A 实现）
- **NestJS**：`nestjs-a2a`
- **Java**：`a2a4j`
- **ADK**：`google-adk[a2a]`（原生 A2A 支持）
- **Web 自动化**：`a2awebagent`（Selenium + A2A）

## 十、设计原则

| 原则 | 说明 |
|------|------|
| **基于现有标准** | HTTP、SSE、JSON-RPC 2.0、ProtoBuf、gRPC |
| **安全默认** | 生产必须 HTTPS/TLS，认证方案在 Agent Card 中声明 |
| **异步优先** | 长时间运行任务 + Human-in-the-loop 原生支持 |
| **多模态无关** | 文本、文件、音频/视频、结构化数据、嵌入式 UI |
| **不透明执行** | Agent 之间只交换能力和信息，不暴露内部 thoughts/plans/tools |
| **可扩展** | Extension 机制允许在不修改核心协议的情况下扩展功能 |

## 十一、版本历史

| 版本 | 日期 | 关键变化 |
|------|------|---------|
| v0.1.0 | 2025-04 | 初始发布，50+ 合作伙伴 |
| v0.2.6 | 2025 | 迭代改进 |
| v0.3.0 | 2025 | 协议增强 |
| **v1.0.0** | **2026-03** | **生产就绪版**：三层架构、多绑定、Extension、安全增强 |

## 十二、未来路线图

- **Agent 发现**：Agent Card 中正式加入认证方案和凭据
- **动态技能查询**：`QuerySkill()` 方法（运行时检查未知技能）
- **动态 UX 协商**：任务内动态切换音频/视频/表单
- **Client 方法扩展**：支持 Client 端主动方法（超出任务管理）
- **流式可靠性**：改进 SSE 和 Push Notification 的可靠性

## 十三、实战示例

### 13.1 最简 A2A Server（Python）

```python
from a2a.server.apps import A2AStarletteApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import AgentCard, AgentSkill

agent_card = AgentCard(
    name="Hello Agent",
    description="A simple greeting agent",
    skills=[
        AgentSkill(
            id="greet",
            name="Greeting",
            description="Greets the user",
        )
    ],
)

# 自定义 RequestHandler 处理消息...
task_store = InMemoryTaskStore()
request_handler = DefaultRequestHandler(task_store=task_store)

app = A2AStarletteApplication(
    agent_card=agent_card,
    request_handler=request_handler,
)
```

### 13.2 最简 A2A Client

```python
from a2a.client import A2AClient
from a2a.types import SendMessageRequest, Message, TextPart

async def call_agent():
    client = A2AClient(agent_card_url="https://agent.example.com/.well-known/agent-card.json")

    response = await client.send_message(
        SendMessageRequest(
            message=Message(
                role="user",
                parts=[TextPart(text="Hello! Can you help me?")],
            )
        )
    )

    if response.task:
        print(f"Task created: {response.task.id}")
        print(f"Status: {response.task.status.state}")
    elif response.message:
        print(f"Direct reply: {response.message.parts}")
```

## 十四、关键参考

| 资源 | 链接 |
|------|------|
| 规范 | https://a2a-protocol.org/ |
| GitHub | https://github.com/google/A2A |
| Proto 定义 | `specification/a2a.proto` |
| Python SDK | `pip install a2a-sdk` |
| ADK A2A 集成 | [[adk-python]] §八 |
| 与 MCP 对比 | Spec Appendix B |
| 官方博客 | https://developers.googleblog.com/en/a2a-a-new-era-of-agent-interoperability/ |
| 关联 | [[agentic-rag]]、[[multica]]、[[heuristic-learning]] |
