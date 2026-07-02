---
title: Flowise
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [llm, workflow, low-code, nodejs, langchain]
sources:
  - https://github.com/FlowiseAI/Flowise
confidence: 0.85
---

# Flowise

> 低代码 LLM 应用构建器 — 基于 LangChain.js 的拖拽式 LLM 平台，快速原型首选。

---

## 一、项目定位

Flowise 是基于 LangChain.js 构建的开源低代码 LLM 平台。通过拖拽节点构建 Chatbot、RAG、Agent 等工作流，无需编写代码即可创建 LLM 应用。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 30k+ |
| 许可证 | Apache 2.0 |
| 语言 | TypeScript (Node.js) |
| 创建者 | FlowiseAI 团队 |
| 官网 | https://flowiseai.com |

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                  UI 层（React）                       │
│   Canvas · Node Panel · Chat Window · API Testing    │
├─────────────────────────────────────────────────────┤
│                  Flowise Core                        │
│   Flow Engine · Node Registry · Variable System      │
├─────────────────────────────────────────────────────┤
│              LangChain.js + LlamaIndex.ts            │
│   Chains · Agents · Tools · VectorStores · LLMs     │
├─────────────────────────────────────────────────────┤
│                  存储层                               │
│   SQLite · PostgreSQL · 加密凭证                      │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | React + React Flow | 拖拽画布 |
| 后端 | Express + TypeScript | API 服务 |
| LLM 框架 | LangChain.js + LlamaIndex.ts | 底层 LLM 抽象 |
| 数据库 | SQLite / PostgreSQL | 流程存储 |
| 部署 | Docker / npm | 多种方式 |

## 三、核心架构

### 3.1 目录结构

```
packages/
  flowise/              — 主包
    src/
      cli.ts              — CLI 入口
      index.ts             — 服务入口
      package-swagger/     — API 文档
  nodes/                — 节点定义
    chatmodels/            — LLM 节点
      OpenAI/
      Anthropic/
      Google VertexAI/
      Ollama/
      HuggingFace/
    chains/               — Chain 节点
    agents/               — Agent 节点
    tools/                — Tool 节点
    vectorstores/         — 向量库节点
    embeddings/           — Embedding 节点
    documentloaders/      — 文档加载器
    textsplitters/        — 文本分片器
    retrievers/           — 检索器
    memories/             — 记忆节点
    outputparsers/        — 输出解析器
    utilities/            — 工具节点
  ui/                   — React 前端
    src/
      components/          — UI 组件
      pages/              — 页面
      utils/              — 工具函数
```

### 3.2 节点系统

每个节点是独立的 TypeScript 模块，定义了：
- **输入端口** — 接收上游数据
- **输出端口** — 输出到下游
- **配置面板** — 节点参数设置
- **执行逻辑** — 调用 LangChain.js 组件

节点分类：

| 类别 | 节点示例 |
|------|---------|
| Chat Models | OpenAI、Anthropic、Google、Azure、Ollama、HuggingFace |
| LLM Chains | LLM Chain、Conversation Chain、Sequential Agent |
| Agents | AutoGPT、BabyAGI、ReAct、Tool Calling Agent |
| Tools | SerpAPI、Calculator、Web Browser、Code Interpreter |
| Vector Stores | Pinecone、Chroma、Weaviate、Qdrant、FAISS |
| Embeddings | OpenAI、HuggingFace、Cohere |
| Document Loaders | PDF、CSV、Web、Notion、GitHub |
| Text Splitters | Recursive、Character、Token |
| Memory | Buffer、Conversation Summary、Vector Store |
| Output Parsers | Structured、Custom |

### 3.3 工作流执行

```
用户拖拽节点 → 连接端口 → 配置参数
                    ↓
           保存为 JSON 图定义
                    ↓
        Flow Engine 解析图拓扑
                    ↓
     按拓扑顺序初始化 LangChain.js 组件
                    ↓
           执行 Chain/Agent 调用
                    ↓
          返回结果（流式/非流式）
```

### 3.4 部署模式

**嵌入式**（iframe）：
```html
<iframe
  src="http://localhost:3000/chatbot/<flow-id>"
  width="400" height="600"
></iframe>
```

**API 模式**：
```bash
# 预测 API
curl -X POST http://localhost:3000/api/v1/prediction/<flow-id> \
  -H "Content-Type: application/json" \
  -d '{"question": "Hello"}'
```

**SDK 调用**：
```javascript
import { Flowise } from 'flowise-sdk';

const client = new Flowise({ baseUrl: 'http://localhost:3000' });
const result = await client.createPrediction({
  chatflowId: 'flow-id',
  question: 'Hello',
});
```

## 四、关键特性

### 4.1 Chatflow vs Agentflow

- **Chatflow** — 对话流，有记忆，适合聊天机器人
- **Agentflow** — Agent 流，有工具，适合自主任务

### 4.2 多模态支持

- 图片上传和识别
- 音频处理
- 文件上传和解析

### 4.3 凭证管理

- 加密存储 API Key
- 支持环境变量
- 共享凭证跨 Chatflow

### 4.4 API 测试

内置 API 测试面板，可直接在 UI 中测试 Chatflow 的 API 端点。

## 五、关键设计决策

1. **LangChain.js 封装** — 不自研 LLM 抽象，直接封装 LangChain.js 组件
2. **节点即组件** — 每个节点对应 LangChain.js 的一个组件类
3. **JSON 图存储** — 工作流保存为 JSON，可版本控制
4. **轻量优先** — SQLite 默认，单进程部署，不依赖 Redis/消息队列
5. **无代码导出** — 不支持导出为代码（与 [[langflow]] 的关键区别）

## 六、开发命令速查

```bash
# 快速开始
npx flowise start

# 或全局安装
npm install -g flowise
flowise start

# 开发模式
git clone https://github.com/FlowiseAI/Flowise.git
cd Flowise
pnpm install
pnpm build
pnpm start

# Docker
docker run -d -p 3000:3000 flowiseai/flowise
```

## 七、与竞品对比

| 维度 | Flowise | [[langflow]] | [[dify]] |
|------|---------|-------------|----------|
| 底层框架 | LangChain.js | LangChain Python | 自研 |
| 语言 | TypeScript | Python | Python + TS |
| 代码导出 | 无 | Python/JSON | 无 |
| 部署复杂度 | 低（单进程） | 中 | 高（多服务） |
| 多租户 | 无 | 无 | 原生 |
| 生产级功能 | 较少 | 中等 | 丰富 |
| 适合场景 | 快速原型 | 开发者工具 | 生产平台 |

---

## 相关

- [[langchain]] — 底层框架
- [[langflow]] — 可视化 LangChain 工作流编辑器（竞品）
- [[dify]] — 全栈 LLMOps 平台
- [[n8n]] — 开源自动化工作流工具
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
