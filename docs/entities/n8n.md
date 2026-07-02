---
title: n8n
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [automation, workflow, low-code, typescript, ai-agent]
sources:
  - https://github.com/n8n-io/n8n
confidence: 0.9
---

# n8n

> 开源自动化工作流工具 — 400+ 集成 + AI Agent 节点 + Fair-code 许可，AI 与业务系统深度集成的自动化首选。

---

## 一、项目定位

n8n 是 Fair-code 模式的开源自动化工具，定位为技术团队的自动化工作流平台。2024 年增加原生 AI 能力（AI Agent 节点、LangChain 集成），从传统自动化扩展到 AI 自动化。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 50k+ |
| 许可证 | Sustainable Use (Fair-code) |
| 语言 | TypeScript (Node.js) |
| 创建者 | Jan Oberhauser |
| 公司 | n8n GmbH |
| 官网 | https://n8n.io |

核心定位：
- **技术团队优先** — 低代码但不排斥代码
- **400+ 集成** — 覆盖企业级 SaaS 和自部署服务
- **AI 原生** — AI Agent 节点融入工作流
- **Fair-code** — 开源但限制商业转售

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                  前端（Vue.js）                       │
│   Canvas Editor · Node Panel · Execution View        │
├─────────────────────────────────────────────────────┤
│                  n8n Core                            │
│   Workflow Engine · Node Registry · Credential Mgr   │
│   Execution Engine · Queue System                    │
├─────────────────────────────────────────────────────┤
│                  AI 层                               │
│   AI Agent Node · LangChain Nodes · Vector DB Nodes  │
├─────────────────────────────────────────────────────┤
│                  集成层（400+ 节点）                    │
│   CRM · 邮件 · 数据库 · 消息 · 存储 · AI/ML           │
├─────────────────────────────────────────────────────┤
│                  存储层                               │
│   SQLite / PostgreSQL / MySQL · Redis                 │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | Vue.js + TypeScript | Canvas 编辑器 |
| 后端 | Express + TypeScript | API + 执行引擎 |
| 执行模式 | Main (单线程) / Queue (Redis) | 扩展模式 |
| 数据库 | SQLite / PostgreSQL / MySQL | 元数据存储 |
| 队列 | Redis + BullMQ | Queue 模式 |
| 部署 | Docker / npm / K8s Helm | 多种方式 |

## 三、核心架构

### 3.1 目录结构

```
n8n/
  packages/
    workflow/              — 工作流核心
      src/
        Workflow.ts          — 工作流定义
        Node.ts              — 节点定义
        Connection.ts        — 连接定义
        ExecuteWorkflow.ts   — 执行引擎
    core/                 — n8n 核心
      src/
        WorkflowExecuteAdditionalData.ts
        NodeExecuteFunctions.ts
    cli/                  — CLI 入口
    editor-ui/            — Vue.js 前端
    nodes-base/           — 内置节点（400+）
      nodes/
        Google/
        Slack/
        Postgres/
        OpenAi/
        ... (400+ 节点)
    @n8n/ai-sdk/          — AI SDK 抽象
    @n8n/chat/            — 聊天组件
```

### 3.2 工作流引擎

```
┌──────────────────────────────────────────────────┐
│              n8n Workflow                          │
│                                                  │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐  │
│  │Trigger│───>│ HTTP │───>│ IF   │───>│Slack │  │
│  │ Node  │    │Request│   │ Node │    │ Node │  │
│  └──────┘    └──────┘    └──┬───┘    └──────┘  │
│                              │                   │
│                         ┌────┴────┐             │
│                    ┌────▼───┐┌────▼───┐         │
│                    │Database││  AI    │          │
│                    │ Node   ││ Agent  │          │
│                    └────────┘└────────┘          │
└──────────────────────────────────────────────────┘
```

触发器类型：
- **Webhook** — HTTP 触发
- **Scheduled** — Cron 定时
- **Polling** — 定期轮询
- **Manual** — 手动触发
- **Event** — 事件驱动

### 3.3 AI Agent 节点

2024 年新增的原生 AI 能力：

```
┌─────────────────────────────────────┐
│          AI Agent Node               │
│                                     │
│  Agent Type:                        │
│    • Conversational Agent           │
│    • OpenAI Functions Agent         │
│    • ReAct Agent                    │
│    • Plan and Execute Agent         │
│                                     │
│  Connected Sub-Nodes:               │
│    • Language Model (OpenAI, etc.)  │
│    • Memory (Buffer, Window)        │
│    • Tools (SerpAPI, Code, HTTP...) │
│    • Output Parser                  │
│                                     │
│  Advanced:                          │
│    • System Message                 │
│    • Max Iterations                 │
│    • Return Intermediate Steps      │
└─────────────────────────────────────┘
```

AI 子节点类型：
- **Language Models** — OpenAI、Anthropic、Ollama、Azure
- **Chat Models** — 同上，对话式
- **Memory** — Buffer Window、Summary
- **Tools** — SerpAPI、Calculator、Code、HTTP Request、Vector Store
- **Embeddings** — OpenAI、Ollama
- **Vector Stores** — Pinecone、Qdrant、Supabase、Postgres
- **Text Splitters** — Recursive、Character

### 3.4 凭证管理

- 加密存储（AES-256）
- 支持 OAuth2 认证
- API Key 管理
- 凭证共享和权限

### 3.5 执行模式

**Main 模式**（默认）：
- 单进程执行
- 适合小规模使用
- SQLite 存储

**Queue 模式**：
- Redis + BullMQ
- Worker 进程池
- 适合大规模生产
- PostgreSQL 存储

## 四、关键特性

### 4.1 400+ 集成节点

| 类别 | 节点 |
|------|------|
| 通信 | Slack、Discord、Telegram、Email、Twilio |
| CRM | Salesforce、HubSpot、Pipedrive |
| 数据库 | PostgreSQL、MySQL、MongoDB、Redis、Snowflake |
| 存储 | S3、Google Drive、Dropbox、OneDrive |
| AI/ML | OpenAI、Anthropic、Hugging Face、Stability AI |
| 监控 | GitHub、GitLab、Jira、PagerDuty |
| 营销 | Mailchimp、SendGrid、HubSpot |
| 电商 | Shopify、WooCommerce、Stripe |

### 4.2 表达式系统

在节点参数中使用表达式：
```
{{ $json.email }}          — 引用上游数据
{{ $now.format('yyyy') }}  — 日期函数
{{ $('Node Name').item }}  — 引用特定节点输出
```

### 4.3 子工作流

支持嵌套工作流：
```
主工作流 → Execute Workflow 节点 → 子工作流
```

### 4.4 错误处理

- Try/Catch 节点
- Error Trigger 工作流
- 自动重试（可配置）
- 错误通知（Slack/Email）

### 4.5 Fair-code 许可

- 源码开放可见
- 允许内部商业使用
- 禁止作为竞品转售
- 企业版额外功能

## 五、关键设计决策

1. **Fair-code 而非开源** — 保护商业模式，允许大多数使用场景
2. **技术团队优先** — 低代码但不限制代码，支持自定义节点（JavaScript）
3. **AI 节点后置** — AI 是节点之一，不是核心抽象，与传统自动化平级
4. **Queue 模式扩展** — 从单进程到分布式只需加 Redis
5. **节点即集成** — 每个第三方服务是一个独立节点，社区可贡献

## 六、开发命令速查

```bash
# 快速开始
npx n8n

# Docker
docker run -d -p 5678:5678 n8nio/n8n

# 开发
git clone https://github.com/n8n-io/n8n.git
cd n8n
pnpm install
pnpm start

# 自定义节点开发
n8n-node-dev setup
n8n-node-dev build
```

## 七、与竞品对比

| 维度 | n8n | [[dify]] | [[apache-airflow]] |
|------|-----|----------|-------------------|
| 定位 | 自动化 + AI | AI 全栈平台 | 工作流调度 |
| 集成数 | 400+ | 内置 | 1000+ Provider |
| AI 能力 | AI Agent 节点 | 原生 | 需集成 |
| 非技术用户 | 友好 | 友好 | 不友好 |
| 代码扩展 | JS 自定义节点 | Python/API | Python DAG |
| 许可 | Fair-code | Apache 2.0 | Apache 2.0 |

---

## 相关

- [[dify]] — 全栈 LLMOps 平台
- [[langchain]] — AI Agent 节点底层框架
- [[apache-airflow]] — 工作流调度（传统编排）
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
