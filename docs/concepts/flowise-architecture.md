---
title: Flowise 项目架构分析
created: 2026-07-07
updated: 2026-07-07
type: concept
tags: [architecture, typescript, nodejs, express, react, monorepo, ai, workflow-engine, node-system, langchain, multi-tenant, mcp, observability]
sources:
  - https://github.com/FlowiseAI/Flowise
  - ~/Projects/Flowise (v3.1.3, commit bb773ffa)
confidence: high
related:
  - "[[flowise]]"
  - "[[langflow-architecture]]"
  - "[[ai-workflow-landscape]]"
---

# Flowise 项目架构分析

> Flowise 是基于 LangChain.js 的视觉化 AI 应用构建平台，通过拖拽节点组装 Chatflow / Agentflow / Multi-Agent。本文基于 `v3.1.3` 源码（commit `bb773ffa`，2026-07 拉取），从 monorepo 组织、节点系统、执行引擎、队列、企业多租户、前端画布六个维度做一次架构通览。
>
> **核心洞察**：Flowise 的执行引擎不是把 JSON 图编译成单个 LangChain Runnable，而是**自研的有向图 BFS 解释器**（`constructGraphs` + `buildFlow`），逐节点 `require()` → `init()` 实例化、`resolveVariables()` 注入上游输出、再按拓扑调用 `run()`。节点是「一个目录一个文件」的纯 CommonJS 模块（`module.exports = { nodeClass }`），通过**文件系统动态发现**注册——零装饰器、零中央 registry。这套设计牺牲了静态可分析性，换来了极高的可扩展性（278 个内置节点 + Marketplace 社区节点）。

---

## 0. 一张图看懂 Flowise 架构

```
┌──────────────────────────────────────────────────────────────────────┐
│                        浏览器 / SDK / iframe                          │
│   packages/ui (React + React Flow 画布)  ·  flowise-sdk  ·  MCP 客户端 │
└───────────────┬──────────────────────────────────────┬───────────────┘
                │  /api/v1/* (REST + SSE 流式)          │  /api/v1/mcp/* (MCP over HTTP)
┌───────────────▼──────────────────────────────────────▼───────────────┐
│                     packages/server (Express + TS)                    │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────────┐  ┌───────────┐  │
│  │  routes/    │→ │ controllers/ │→ │  services/   │→ │  queue/   │  │
│  │  50+ 路由组  │  │              │  │  业务逻辑     │  │  BullMQ   │  │
│  └─────────────┘  └──────────────┘  └──────┬───────┘  └─────┬─────┘  │
│           │                          ▲    │                 │        │
│           │  middleware:             │    │                 │        │
│           │  cors · sanitize · JWT   │    │                 │        │
│           │  validateAPIKey · rate   │    │                 │        │
│           └──────────────────────────┘    ▼                 ▼        │
│  ┌────────────────────────────┐  ┌──────────────────────────────┐    │
│  │  buildChatflow.ts          │  │  Redis (BullMQ)              │    │
│  │  executeFlow() ──┐         │  │  · PredictionQueue           │    │
│  │                 │         │  │  · UpsertQueue               │    │
│  │  ┌──────────────▼───────┐ │  │  · ScheduleQueue             │    │
│  │  │ utils/index.ts       │ │  └──────────────────────────────┘    │
│  │  │ constructGraphs()    │ │                                      │
│  │  │ buildFlow() (BFS)    │ │  ┌──────────────────────────────┐    │
│  │  │ resolveVariables()   │ │  │  TypeORM (AppDataSource)     │    │
│  │  │ buildAgentGraph()    │ │  │  sqlite / mysql / mariadb    │    │
│  │  └──────────┬───────────┘ │  │  / postgres (+ 企业实体)     │    │
│  └─────────────┼─────────────┘  └──────────────────────────────┘    │
│                │ dynamic require()                                   │
│  ┌─────────────▼─────────────────────────────────────────────────┐  │
│  │   packages/components  (flowise-components)                   │  │
│  │   nodes/<Category>/<Name>/index.ts  ×  278 节点 / 25 类       │  │
│  │   每节点: nodeClass implements INode { inputs, init(), run() } │  │
│  │   封装 LangChain.js + LlamaIndex.ts + 各类 SDK                │  │
│  └───────────────────────────────────────────────────────────────┘  │
└──────────────────────────────────────────────────────────────────────┘
                                ▲
              ┌─────────────────┴──────────────────┐
              │   enterprise/ (可选企业层)          │
              │   Organization · Workspace · RBAC   │
              │   SSO (Google/GitHub/Azure/Auth0)   │
              └────────────────────────────────────┘
```

| 维度 | 选型 |
|---|---|
| 语言 / 运行时 | TypeScript 5.4，Node.js 24（`engines`） |
| Monorepo | pnpm 10 workspace + Turborepo 1.10 |
| 后端 | Express 4（无 Fastify/Nest），TypeORM（`synchronize:false` + migration） |
| 前端 | React + Vite（`packages/ui/vite.config.js`），React Flow 11 画布，MUI，Redux Toolkit |
| LLM 框架 | `@langchain/core@1.1.20` + LlamaIndex.ts（双引擎） |
| 队列 | BullMQ（Redis），3 条队列 |
| 数据库 | sqlite（默认）/ mysql / mariadb / postgres |
| 可观测性 | OpenTelemetry（OTLP trace+metrics）+ Prometheus + Arize/Phoenix/Opik tracer |
| 包数 | 6 个 workspace 包 |

---

## 1. Monorepo 组织

### 1.1 六个包

`pnpm-workspace.yaml` 只声明 `packages/*`，根 `package.json` 的 `workspaces` 额外收编了顶层目录。实际 6 个包：

```
packages/
├── server/            @flowise 主包(flowise on npm)   v3.1.3  Express 后端 + CLI + TypeORM
├── components/        flowise-components              v3.1.3  278 个节点 + 凭证 + handler
├── ui/                flowise-ui                      v3.1.3  React 前端(主应用)
├── agentflow/         @flowiseai/agentflow            0.0.0-dev  可嵌入的 Agent 画布组件
├── observe/           @flowiseai/observe              0.0.0-dev  可嵌入的执行观测/评估组件
└── api-documentation/ flowise-api                     v1.0.3    swagger-ui 自动 API 文档
```

后三个是较新的「可嵌入 SDK 包」：`@flowiseai/agentflow` 和 `@flowiseai/observe` 是独立的 React 组件库（走 Domain-Driven Modular 四层架构：`atoms/features/core/infrastructure`，见各自 `ARCHITECTURE.md`），让 Flowise 的画布与观测面板能被嵌进第三方应用。它们与主 `ui` 包**不共享代码**，是平行的、面向不同消费者的产品线。

### 1.2 构建编排

```jsonc
// turbo.json
"pipeline": {
  "build": { "dependsOn": ["^build"], "outputs": ["dist/**"] },
  "dev":   { "cache": false }
}
```

依赖方向是 `ui` / `server` → `components`（节点包是底层依赖）。`build:docker` 脚本特意 `--filter=!@flowiseai/agentflow --filter=!@flowiseai/observe`，因为 Docker 镜像只跑主应用，不需要这两个 SDK 包——这是个值得注意的「瘦身」实践。

### 1.3 关键版本锁

根 `package.json` 用 `resolutions` / `pnpm.overrides` 强制锁了一批安全敏感依赖（`axios@1.15`、`ws@8.18.3`、`path-to-regexp@0.1.12`、`tar-fs@3.1.0` 等），并对 LLM SDK 收口：`@langchain/core@1.1.20`、`openai@6.19.0`、`@anthropic-ai/sdk@^0.73`。pnpm 还限制了 `onlyBuiltDependencies: [faiss-node, sqlite3]`——只允许这两个原生模块跑 install 脚本，是供应链防护。

---

## 2. 节点系统（components 包的核心）

> 这是 Flowise 最值得学习的部分。节点定义极其轻量，却撑起了 278 个集成。

### 2.1 节点不是分散文件，而是「一个目录一个节点」

```
packages/components/nodes/
├── chatmodels/ChatOpenAI/
│   ├── ChatOpenAI.ts          # 主逻辑(inputs + init + loadMethods)
│   ├── FlowiseChatOpenAI.ts   # 扩展的 LangChain ChatOpenAI 子类
│   ├── ChatOpenAI_LlamaIndex.ts  # LlamaIndex 引擎变体
│   └── openai.svg
├── tools/Calculator/
│   ├── Calculator.ts
│   └── calculator.svg
└── ...
```

每个节点是一个**目录**，可含多个 `.ts`、一个图标、辅助文件。构建后编译成 `dist/nodes/<cat>/<Name>/*.js`。

### 2.2 节点分类与数量（v3.1.3 实测）

共 **25 类、278 个节点**：

| 类别 | 数 | 类别 | 数 | 类别 | 数 |
|---|---|---|---|---|---|
| documentloaders | 39 | tools | 40 | chatmodels | 29 |
| vectorstores | 24 | embeddings | 16 | agentflow | 15 |
| retrievers | 15 | sequentialagents | 11 | chains | 11 |
| memory | 12 | llms | 12 | analytic | 7 |
| textsplitters | 6 | utilities | 5 | outputparsers | 4 |
| prompts | 4 | cache | 4 | responsesynthesizer | 4 |
| agents | 8 | engine | 3 | recordmanager | 3 |
| multiagents | 2 | moderation | 2 | graphs | 1 |
| speechtotext | 1 | | | | |

注意 `sequentialagents`（11）和 `multiagents`（2）是较新的 **Agent 编排原语**（Agent / Condition / Loop / State / Start / End / ExecuteFlow / ToolNode / LLMNode / CustomFunction），对标 LangGraph 的图式 agent，这是 Flowise 从「Chain 编辑器」向「Agent 编辑器」演进的关键。

### 2.3 INode 契约 —— 节点的「接口规范」

`packages/components/src/Interface.ts:150`：

```ts
export interface INode extends INodeProperties {
    credential?: INodeParams                    // 凭证绑定
    inputs?: INodeParams[]                      // 参数面板(驱动 UI 渲染)
    output?: INodeOutputsValue[]
    loadMethods?: {                             // 异步选项加载(如拉模型列表)
        [key: string]: (nodeData: INodeData, options?: ICommonObject) => Promise<INodeOptionsValue[]>
    }
    vectorStoreMethods?: { upsert; search; delete }  // 向量库专用
    init?(nodeData: INodeData, input: string, options?: ICommonObject): Promise<any>  // 实例化
    run?(nodeData: INodeData, input: string, options?: ICommonObject): Promise<string | ICommonObject>
}
```

`INodeProperties` 提供 UI 元数据：`label / name / type / icon / version / category / baseClasses / color / badge / tags / deprecateMessage / author / documentation`。`baseClasses` 尤其关键——它声明节点产出的类型（如 `['ChatOpenAI', 'BaseChatModel']`），**画布的类型系统靠它判断哪些节点能连到一起**。

`INodeParams`（参数定义）字段极丰富（`type / default / options / optional / additionalParams / loadMethod / show / hide / acceptVariable / acceptNodeOutputAsVariable / tabs / array / datagrid / credentialNames ...`），本质是一套**声明式表单 schema**，前端据此动态渲染输入控件、条件显隐、级联加载。

### 2.4 一个完整节点长什么样（ChatOpenAI）

```ts
// packages/components/nodes/chatmodels/ChatOpenAI/ChatOpenAI.ts
class ChatOpenAI_ChatModels implements INode {
    label = 'OpenAI'
    name = 'chatOpenAI'
    version = 8.3                          // ⬅ 版本号，用于破坏性变更
    type = 'ChatOpenAI'
    icon = 'openai.svg'
    category = 'Chat Models'
    baseClasses = [this.type, ...getBaseClasses(LangchainChatOpenAI)]
    credential = { label: 'Connect Credential', type: 'credential', credentialNames: ['openAIApi'] }
    inputs = [
        { label: 'Cache', name: 'cache', type: 'BaseCache', optional: true },
        { label: 'Model Name', name: 'modelName', type: 'asyncOptions',
          loadMethod: 'listModels', default: 'gpt-4o-mini' },
        { label: 'Temperature', name: 'temperature', type: 'number', step: 0.1, default: 0.9, optional: true },
        { label: 'Streaming', name: 'streaming', type: 'boolean', default: true, optional: true },
        { label: 'Reasoning Effort', name: 'reasoningEffort', type: 'options',
          options: [/* low/medium/high/xhigh */],
          show: { reasoning: true } },      // ⬅ 条件显隐:仅 reasoning=true 时出现
        // ...
    ]

    loadMethods = {
        async listModels() { return await getModels(MODEL_TYPE.CHAT, 'chatOpenAI') }
    }

    async init(nodeData, _, options) {
        const temperature = nodeData.inputs?.temperature as string
        const modelName = nodeData.inputs?.modelName as string
        // ...从 nodeData.inputs 取所有参数
        const credentialData = await getCredentialData(nodeData.credential ?? '', options)
        const openAIApiKey = getCredentialParam('openAIApiKey', credentialData, nodeData)
        const obj: ChatOpenAIFields = { temperature: parseFloat(temperature), modelName,
                                        openAIApiKey, apiKey: openAIApiKey, streaming: streaming ?? true }
        // ...推理模型特殊处理(gpt-5/o-series):删 temperature/stop,加 reasoning
        const model = new ChatOpenAI(nodeData.id, obj)   // FlowiseChatOpenAI 子类
        model.setMultiModalOption(multiModalOption)
        return model
    }
}
module.exports = { nodeClass: ChatOpenAI_ChatModels }   // ⬅ CommonJS,这是注册的唯一约定
```

设计要点：
- **参数从 `nodeData.inputs` 读**，类型都是 `string`（UI 序列化的），节点内部 `parseFloat` / `JSON.parse` 自己转。
- **`loadMethods`** 让 UI 在编辑时异步拉选项（模型列表、向量库索引名等），避免硬编码。
- **`init()` 返回真正的 LangChain/LlamaIndex 对象**，`run()` 才是执行。对于「组件型」节点（LLM、向量库、embedding），`run()` 往往为空，真正执行在下游 chain/agent 调用它返回的实例时发生。

### 2.5 节点注册：文件系统动态发现（NodesPool）

`packages/server/src/NodesPool.ts` —— 这是 Flowise 可扩展性的根基：

```ts
async initializeNodes() {
    const packagePath = getNodeModulesPackagePath('flowise-components')
    const nodesPath = path.join(packagePath, 'dist', 'nodes')
    const nodes = await this.loadNodesFromDir(nodesPath)
    Object.assign(this.componentNodes, nodes)
}

async loadNodesFromDir(dir) {
    const disabled_nodes = process.env.DISABLED_NODES?.split(',') ?? []
    const nodes: IComponentNodes = {}
    const nodeFiles = await this.getFiles(dir)        // 递归拿所有文件
    await Promise.all(nodeFiles.map(async (file) => {
        if (file.endsWith('.js')) {
            const nodeModule = await require(file)    // ⬅ 动态 require 每个文件
            if (nodeModule.nodeClass) {
                const inst = new nodeModule.nodeClass()
                inst.filePath = file                   // 记下路径,执行时再 require
                // ...图标绝对路径处理
                const skip = ['Analytic', 'SpeechToText']
                const communityOk = appConfig.showCommunityNodes || !inst.author
                const notDisabled = !disabled_nodes.includes(inst.name)
                if (!skip.includes(inst.category) && communityOk && notDisabled)
                    nodes[inst.name] = inst
            }
        }
    }))
    return nodes
}
```

**关键设计**：
1. **零 registry、零装饰器**——只要文件 `module.exports = { nodeClass }`，就被发现。新增节点零改服务端代码。
2. **`author` 字段 = 社区节点标识**——有 `author` 的节点默认隐藏（`showCommunityNodes` 控制），这是 Marketplace 社区节点的安全闸门。
3. **`DISABLED_NODES` 环境变量**可按名禁用节点——运维级开关。
4. **凭证图标路径映射**：节点声明的 `credential.credentialNames` 会被反向挂上该节点的图标，供凭证 UI 复用。
5. **`filePath` 被保存**——`buildFlow` 执行时用 `await import(nodeInstanceFilePath)` 再次动态加载并 `new nodeClass()`，保证每次执行拿到干净实例（避免跨请求状态泄漏）。

凭证（`credentials/*.credential.js`）走完全相同的发现机制，单独的 `initializeCredentials()`。

### 2.6 handler.ts —— 回调与流式层（不是执行引擎）

注意 `packages/components/src/handler.ts`（2049 行）**不是** flow 执行器，而是 LangChain 的 `BaseCallbackHandler` 实现集合：
- `ConsoleCallbackHandler`（`BaseTracer` 子类）—— 记录链执行的 token / 耗时 / 工具调用，写日志与 telemetry。
- `CustomChainHandler`（`BaseCallbackHandler`）—— 把 LangChain 的流式 token 中继成 SSE 推给前端。
- `CustomStreamingHandler` —— 流式细分处理。
- `additionalCallbacks()` —— 按 nodeData 配置挂 Arize / Phoenix / Opik 这些第三方 tracer。
- `AnalyticHandler` —— 分析事件上报。

执行引擎在 `packages/server/src/utils/`，下一节。

---

## 3. 执行引擎 —— 自研有向图 BFS 解释器

> 这是 Flowise 与 Langflow 最大的架构分野。Langflow 把图编译成单个 LangChain Runnable 后 `.invoke()`；Flowise 自己写图遍历器，**逐节点**实例化和执行。

### 3.1 入口：prediction 路由 → executeFlow

```
POST /api/v1/prediction/:id
  → routes/predictions → predictionsController.createPrediction
  → (同步路径) utilBuildChatflow()   →  executeFlow()
  → (异步路径) PredictionQueue.add() →  worker → processJob() → executeFlow()
```

`packages/server/src/utils/buildChatflow.ts:990` 的 `utilBuildChatflow` 是请求编排层：拿 chatflow 实体、校验、解析上传文件、决定同步还是入队、处理 SSE 流。真正干活的是 `executeFlow`（同文件 `:301`）。

### 3.2 executeFlow 的五步流水线

```ts
// buildChatflow.ts:301
export const executeFlow = async ({ componentNodes, incomingInput, chatflow, ... }) => {
    // ① 处理上传:图片/音频(语音转文字)/文件(RAG 注入)/表单文件
    //    → 存到 storage,把 FILE-STORAGE::path 塞进 overrideConfig

    // ② 区分流类型
    if (chatflow.type === 'AGENTFLOW')
        return executeAgentFlow(...)        // 新版 agentflow 走另一条路

    // ③ 解析保存的图 JSON
    const { nodes, edges } = JSON.parse(chatflow.flowData)

    // ④ 构建有向图,定位起点/终点
    const { graph, nodeDependencies } = constructGraphs(nodes, edges)       // 正向
    const endingNodes = getEndingNodes(nodeDependencies, graph, nodes)      // 入度≠0 的是终点
    const reversed = constructGraphs(nodes, edges, { isReversed: true })    // 反向
    for (const endId of endingNodeIds) {
        const { startingNodeIds, depthQueue } = getStartingNodes(reversed.graph, endId)
        // ⬆ 从终点反推起点,并算出每个节点的"深度"(离终点多远)
    }

    // ⑤ BFS 实例化所有节点
    const reactFlowNodes = await buildFlow({ startingNodeIds, graph, depthQueue, ... })

    // ⑥ 按流类型执行
    if (isAgentFlow)              // Multi Agents / Sequential Agents
        return buildAgentGraph(...)        // 走 LangGraph 式 agent 图
    else                          // 普通 Chatflow / Chain
        const { endingNodeInstance } = initEndingNode(...)
        return endingNodeInstance.run(...)  // 跑终点节点(它会消费已实例化的上游)
}
```

### 3.3 constructGraphs —— 极简邻接表

`packages/server/src/utils/index.ts:155`，逻辑直白到几乎是教科书：

```ts
export const constructGraphs = (nodes, edges, options?) => {
    const nodeDependencies = {}   // 入度
    const graph = {}              // 邻接表: nodeId -> [targetId...]
    for (const n of nodes) { graph[n.id] = []; nodeDependencies[n.id] = 0 }
    for (const e of edges) {
        graph[e.source].push(e.target)
        if (options?.isReversed) graph[e.target].push(e.source)  // 反向图
        nodeDependencies[e.target] += 1
    }
    return { graph, nodeDependencies }
}
```

- **正向图** → 找终点（`nodeDependencies[id] !== 0` 即被依赖→是终点）。等等，实际 `getEndingNodes` 用的是「没有出边」的判定变体，但思想一致。
- **反向图** → 从终点 BFS 反推到起点，同时算 `depthQueue`（每个节点离终点的层级），用于决定 BFS 执行顺序。
- **`isNonDirected`** 选项用于环检测。

### 3.4 buildFlow —— BFS 节点实例化器（心脏）

`packages/server/src/utils/index.ts:516`：

```ts
export const buildFlow = async ({ startingNodeIds, reactFlowNodes, reactFlowEdges, componentNodes, ... }) => {
    const flowNodes = cloneDeep(reactFlowNodes)
    const nodeQueue = []
    const exploredNode = {}        // 记录每个节点已访问 + 剩余循环次数
    const dynamicVariables = {}
    const maxLoop = 3              // ⬅ 环路保护:同一节点最多执行 3 次(支持 Loop 节点)

    for (const id of startingNodeIds) {
        nodeQueue.push({ nodeId: id, depth: 0 })
        exploredNode[id] = { remainingLoop: maxLoop, lastSeenDepth: 0 }
    }
    const initializedNodes = new Set()
    const reversedGraph = constructGraphs(reactFlowNodes, reactFlowEdges, { isReversed: true }).graph

    while (nodeQueue.length) {
        const { nodeId, depth } = nodeQueue.shift()
        const reactFlowNode = flowNodes.find(n => n.id === nodeId)

        // ① 动态加载节点类(每次执行都 new 一个新实例!)
        const filePath = componentNodes[reactFlowNode.data.name].filePath
        const nodeModule = await import(filePath)
        const newNodeInstance = new nodeModule.nodeClass()

        let flowNodeData = cloneDeep(reactFlowNode.data)

        // ② 应用 overrideConfig(API 调用方覆盖节点参数)
        if (overrideConfig && apiOverrideStatus)
            flowNodeData = replaceInputsWithConfig(flowNodeData, overrideConfig, nodeOverrides, variableOverrides)

        // ③ 解析变量:把 ${flow.chatId} / 上游节点输出 / 文件内容 注入参数
        const reactFlowNodeData = await resolveVariables(
            flowNodeData, flowNodes, question, chatHistory, flowData,
            uploadedFilesContent, availableVariables, variableOverrides)

        // ④ 向量库 upsert 特殊路径
        if (isUpsert && stopNodeId && nodeId === stopNodeId)
            return await newNodeInstance.vectorStoreMethods!.upsert!.call(newNodeInstance, reactFlowNodeData, {...})

        // ⑤ 实例化:调 init() 拿到真正的 LangChain 对象
        const newInstance = await newNodeInstance.init?.(reactFlowNodeData, input, options)

        // ⑥ 存回 flowNodes,供下游节点通过 resolveVariables 取用
        reactFlowNode.data.instance = newInstance
        reactFlowNode.data = reactFlowNodeData
        initializedNodes.add(nodeId)

        // ⑦ 把后继节点按 depth 入队(拓扑顺序)
        for (const successorId of graph[nodeId]) {
            // ...环检测 + depth 控制
            if (!initializedNodes.has(successorId)) nodeQueue.push({ nodeId: successorId, depth: depth + 1 })
        }
    }
    return flowNodes   // 所有节点都 instance 化完毕
}
```

**设计精髓**：
1. **实例化 ≠ 执行**。`buildFlow` 只是把每个节点的 `init()` 跑一遍，拿到 LangChain 对象塞回 `node.data.instance`。真正的「执行」（调 LLM、跑检索）发生在第六步对**终点节点**调 `run()` 时——而终点节点（如 Conversational Retrieval QA Chain）在 `run()` 内部会按需触发它依赖的上游实例。
2. **`resolveVariables` 是数据流核心**：节点的参数值可以是字面量，也可以是 `${flow.xxx}` / `${节点输出}` / 文件占位符。这一步把图里的「连接」物化成参数注入——Flowise 的「连线」语义=「把上游 `.instance` 或输出塞进下游某个 input 字段」。
3. **环路与循环**：`maxLoop=3` + `remainingLoop` 让 `Loop` / `Condition` 节点能有限循环，但防死循环。
4. **`cloneDeep`** 保证并发请求间节点数据不互染。

### 3.5 Agent 路径：buildAgentGraph

当终点节点是 `Multi Agents`（Supervisor/Worker）或 `Sequential Agents`（LangGraph 式）时，走 `packages/server/src/utils/buildAgentGraph.ts`。它接收 `buildFlow` 已实例化的节点，再组装成 LangGraph 的 `StateGraph` 跑——这部分把 Flowise 节点图**翻译**成 LangGraph 的 agent 图，是较新的能力（`sequentialagents` 11 节点全是图原语：Start/End/Agent/Condition/Loop/State/ToolNode/LLMNode/ExecuteFlow/CustomFunction）。

### 3.6 agentflow v2：从 prompt 生成图

`packages/server/src/services/agentflowv2-generator/`（`index.ts` + `prompt.ts`）—— 调 LLM 把自然语言 prompt 直接生成一个 Agentflow 图 JSON，再交给 `executeAgentFlow` 跑。这是「AI 建 Agent」的入口，被 `PredictionQueue` 的 `isAgentFlowGenerator` 分支调用。

---

## 4. 数据库与多租户

### 4.1 TypeORM + 四种数据库

`packages/server/src/DataSource.ts` 按 `DATABASE_TYPE` 切 sqlite / mysql / mariadb / postgres。注意几个细节：
- **`synchronize: false` + `migrationsRun: false`**——不在启动时自动建表/迁移，而是在 `index.ts` 的 `initDatabase()` 里显式 `runMigrations({ transaction: 'each' })`，让迁移失败可观测。
- **每种库一套独立 migration 集**（`database/migrations/{sqlite,mysql,mariadb,postgres}.ts`）——迁移 SQL 因方言而异。
- postgres 额外配 `applicationName: 'Flowise'`、`idleTimeoutMillis`、`poolErrorHandler`——面向生产。
- 默认 sqlite 落在 `~/.flowise/database.sqlite`。

### 4.2 核心实体（23 个）

```
ChatFlow          — 主实体,flowData(JSON 图)/type(CHATFLOW|AGENTFLOW|MULTIAGENT|ASSISTANT)
                     /chatbotConfig/apiConfig/analytic/speechToText/textToSpeech
                     /followUpPrompts/mcpServerConfig/webhookSecret/workspaceId
ChatMessage       — 对话历史(role/chatId/sessionId/sourceDocuments/artifacts/usedTools/agentReasoning/action)
Credential        — 加密的 API Key 存储
ApiKey            — 对外 API Key(绑定 chatflow)
Tool              — 可复用的 Tool 节点
Assistant         — OpenAI Assistants 集成
DocumentStore(+FileChunk) — 独立文档库(向量库的内容管理)
Dataset(+Row)     — 评估数据集
Evaluation(+Run)  — 评估任务与运行
Evaluator         — 评估器配置
Execution         — 执行记录(观测)
Variable          — 流程级变量(workspace 隔离)
Lead / ChatMessageFeedback — 业务侧(线索收集、消息反馈)
UpsertHistory     — 向量库 upsert 历史
ScheduleRecord(+TriggerLog) — 定时触发
CustomMcpServer   — 用户自定义 MCP server
CustomTemplate    — 自定义模板
```

`ChatFlow.flowData` 存的是**整个 React Flow 画布的 JSON**（nodes + edges + viewport），即「图即数据」。`type` 字段是 v3 的关键演进——同一套存储承载了四种产品形态。

### 4.3 企业层：Organization → Workspace → RBAC

`packages/server/src/enterprise/` 是独立子模块（有自己的 `LICENSE.md`，企业版）：

```
enterprise/
├── database/entities/   Organization · Workspace · User · Role
│                        · OrganizationUser · WorkspaceUser
│                        · LoginMethod · LoginSession
├── rbac/                PermissionCheck.ts · Permissions.ts    (RBAC 权限矩阵)
├── sso/                 GoogleSSO · GithubSSO · AzureSSO · Auth0SSO (继承 SSOBase)
├── routes/ + controllers/ + services/                          (企业 API)
├── middleware/passport.ts                                       (JWT + cookie)
└── emails/                                                     (邮件)
```

**多租户模型**：`Organization` (顶层) → `Workspace` (工作空间，资源隔离边界) → 资源。所有核心实体（ChatFlow 等）都带 `workspaceId` 列，查询走 `getWorkspaceSearchOptions(workspaceId)` 做行级隔离。这与 [[dify]] 的原生多租户、[[langflow]] 的无多租户形成对比——Flowise 通过**可选企业包**叠加多租户，主包保持单租户简单。

`IdentityManager`（单例）管加密密钥与认证秘密，支持从 env / AWS Secrets Manager / 文件系统加载（`initAuthSecrets`），是云端部署的安全基建。

---

## 5. 队列、定时与可观测性

### 5.1 BullMQ 三队列

`packages/server/src/queue/`：

| 队列 | 用途 |
|---|---|
| `PredictionQueue` | 异步推理（`processJob` 分发到 `executeFlow` / `generateAgentflowv2` / `executeCustomNodeFunction`） |
| `UpsertQueue` | 向量库批量 upsert（文档入库） |
| `ScheduleQueue` | 定时触发 chatflow（配合 `ScheduleBeat` 心跳） |

`QueueManager`（单例）统一管 Redis 连接（支持 `REDIS_URL` / `rediss://` TLS / 独立 host+port+cert），并挂 Bull Board（`/admin/queues`，受 `verifyTokenForBullMQDashboard` 保护）。

**同步 vs 异步**：默认走 `REDIS_URL` 时启用队列；无 Redis 时 `utilBuildChatflow` 直接同步调 `executeFlow`（单进程）。这是 Flowise 「轻量起步、按需扩展」的典型设计——`docker-compose.yml` vs `docker-compose-queue-*.yml` 两套部署形态。

**Worker 模式**：`packages/server/bin/run worker` 单独起一个只跑队列消费的进程（`start-worker` 脚本），支持水平扩展推理算力而不复制 UI。

### 5.2 事件中继

`RedisEventPublisher` / `RedisEventSubscriber` —— Worker 进程把 SSE 事件经 Redis pub/sub 回传给 Web 进程，再由 `SSEStreamer` 推给客户端。这样**流式推理可以在独立 Worker 跑、流式 token 仍能实时回浏览器**，是分离部署的关键粘合层。

### 5.3 可观测性：OpenTelemetry 一等公民

`packages/server/src/metrics/`：
- `OpenTelemetry` —— `@opentelemetry/sdk-node` + `auto-instrumentations-node`，trace 与 metrics 都支持 OTLP（grpc / http / proto 三种 exporter）。
- `Prometheus` —— 暴露 `/metrics`。
- 节点侧（components）：`handler.ts` 的 `additionalCallbacks` 按 nodeData 挂 **Arize / Phoenix / Opik** tracer——对接专业 LLM 可观测平台。
- `Telemetry`（`utils/telemetry.ts`）——产品使用遥测（可关）。

`@flowiseai/observe` 这个 SDK 包就是把执行轨迹、评估结果可视化成可嵌入面板。

---

## 6. 前端（ui 包）

### 6.1 技术栈

Vite + React + React Flow 11 + MUI（Material）+ Redux Toolkit。路由用 React Router（`routes/index.jsx` 分 `MainRoutes / CanvasRoutes / ChatbotRoutes / ExecutionRoutes / AuthRoutes`，每条都包 `<RequireAuth permission='...' />`——前端也做 RBAC 权限闸门）。

### 6.2 画布 = React Flow

```
src/views/canvas/            — 主画布(Chatflow)
src/views/agentflowsv2/Canvas — Agentflow v2 画布
```

节点元数据（`label/icon/category/baseClasses/inputs`）直接驱动 React Flow 的自定义节点渲染——`inputs` 数组每项 → 一个表单控件（`asyncOptions` → 下拉、`number` → 数字框、`show:{...}` → 条件显隐）。连线合法性靠两端 `baseClasses` 类型匹配判断。

### 6.3 Redux 状态

`store/reducers/canvasReducer.js` 管 canvas 状态：`SET_CHATFLOW / SET_DIRTY / SET_COMPONENT_NODES / SET_COMPONENT_CREDENTIALS / SHOW_CANVAS_DIALOG ...`。节点列表（`componentNodes`）从后端 `/api/v1/components-credentials` 拉一次缓存进 Redux，画布渲染与参数面板都读它。

### 6.4 API 客户端

`src/api/client.js` —— 单例 axios（`baseURL: /api/v1`），拦截器处理 401 + token 刷新（`/auth/refreshToken`）。`api/` 下每个资源一个文件（`chatflows.js / credentials.js / documentstore.js / custommcpservers.js ...`），函数式封装。

### 6.5 与 agentflow / observe 包的关系

`packages/ui`（flowise-ui）是**主应用**，自己实现了 canvas。而 `@flowiseai/agentflow` / `@flowiseai/observe` 是**独立可嵌入组件**（四层 DDD 架构），服务于「把 Flowise 画布/观测嵌进别人的产品」的场景。三者代码不共享，是面向不同消费者的平行产品线——这是 Flowise 走向平台化（embeddable）的信号。

---

## 7. 关键集成与新特性（v3 演进）

### 7.1 MCP（Model Context Protocol）双向

- **作为 MCP Server**：`routes/mcp-server/` + `services/mcp-server/` —— 给 chatflow 生成 token，把它**暴露成一个 MCP tool**供 Claude Desktop / 其他 MCP 客户端调用。`mcpServerConfig` 存在 ChatFlow 实体上。
- **作为 MCP Client**：`nodes/tools/MCP/`（MCPToolkit / MCPTool）—— Flowise 节点去连外部 MCP server 拿工具。`nodes/index.ts` 导出 `validateCommandInjection / validateEnvironmentVariables / validateCommandFlags / validateMCPServerConfig` 等安全校验（stdio 命令 allowlist）——近期安全加固（见 commit `f5d16835` "Make Custom MCP stdio command allowlist operator-controlled"）。

### 7.2 Agent 编排三层

1. **经典 Agents**（`agents/` 8 节点）—— ReAct / Tool Calling 等传统 LangChain agent。
2. **Multi Agents**（`multiagents/` 2 节点）—— Supervisor + Worker 模式。
3. **Sequential Agents**（`sequentialagents/` 11 节点）—— LangGraph 式显式状态图（Start/End/Condition/Loop/State），最新能力，配合 `buildAgentGraph` 执行。

### 7.3 Document Store

独立于向量库节点的**文档管理层**（`services/documentstore/`）：把 loader → splitter → embedding → vectorstore 的 upsert 流程产品化成 UI 可操作的「文档库」，支持预览、增量、按文件管理 chunk，并查「Where Used」（哪些 chatflow 用了这个库）。

### 7.4 评估（Evaluations）

`Dataset` + `Evaluation` + `Evaluator` + `EvaluationRun` 四实体支撑——把 chatflow 跑数据集、用评估器（LLM-as-judge / 规则）打分，结果进 `Execution` 与 observe 包可视化。对标 LangFuse / Promptfoo 的能力。

### 7.5 Marketplace

`services/marketplaces/` + `routes/marketplaces/` —— 社区节点与模板的市场。`NodesPool` 的 `author` 字段 + `showCommunityNodes` 开关是它的安全边界。

### 7.6 OpenAI Assistants / Realtime

专门的 `openai-assistants*` / `openai-realtime` 路由组——对接 OpenAI 的 Assistant API 与 Realtime（语音）API。

---

## 8. API 与部署形态

### 8.1 路由规模

`packages/server/src/routes/` 有 **50+ 路由组**（chatflows / predictions / chatflows-streaming / credentials / tools / assistants / documentstore / dataset / evaluations / executions / marketplaces / mcp-server / custom-mcp-servers / openai-realtime / variables / vectors / webhook / pricing / oauth2 ...），全部挂在 `/api/v1`。Swagger 文档由 `api-documentation` 包用 `swagger-jsdoc` 生成。

### 8.2 中间件链（index.ts）

```
cors(getCorsOptions())            — CORS,配置可校验
cookieParser()
expressRequestLogger              — 请求日志
sanitizeMiddleware                — XSS 防护
[JWT cookie / validateAPIKey]     — 认证(API key 走 WHITELIST/blacklist)
rateLimiterManager                — 按 chatflow 维度的限流
flowiseApiV1Router                — 业务路由
/admin/queues (BullBoard)         — 受保护的管理面板
express.static(uiBuildPath)       — 前端静态资源(SPA fallback)
errorHandlerMiddleware
```

### 8.3 三种部署形态

| 形态 | 命令 | 适用 |
|---|---|---|
| 单进程（默认） | `npx flowise start` / `pnpm start` | 开发、小规模 |
| Web + Worker 分离 | `pnpm start` + `pnpm start-worker` | 生产，水平扩展推理 |
| Docker Compose | `docker/docker-compose*.yml` | 容器化（含 queue 变体） |

Dockerfile 基于 `node:24-alpine`，装 chromium（puppeteer 用）、cairo/pango（图片渲染），`NODE_OPTIONS=--max-old-space-size=8192`，非 root 运行。

### 8.4 调用方式

```bash
# REST 预测(同步或 SSE 流式)
curl -X POST http://localhost:3000/api/v1/prediction/<chatflowId> \
  -H "Authorization: Bearer <apikey>" \
  -d '{"question":"...","streaming":true}'

# SDK
import { Flowise } from 'flowise-sdk'
const res = await new Flowise({baseUrl}).createPrediction({chatflowId, question})

# iframe 嵌入
<iframe src="http://host/chatbot/<id>" />

# MCP — 把 chatflow 当成 MCP tool 给 Claude Desktop 用
```

---

## 9. 设计决策与取舍

| 决策 | 收益 | 代价 |
|---|---|---|
| **自研 BFS 解释器**而非编译成单个 Runnable | 可中断、可逐节点观测、支持 Loop/Condition 等控制流节点、agentflow 灵活 | 性能不如编译型；状态管理复杂；需自管环路/深度 |
| **文件系统动态注册节点** | 加节点零改框架；社区节点零摩擦 | 无静态类型检查；IDE 跳转弱；bundle 体积大（156 deps） |
| **节点 `init()` + `run()` 二段式** | 组件型节点（LLM/向量库）与执行型节点（chain）统一模型 | 概念略绕——执行其实在终点 `run()` 内隐式触发上游 |
| **TypeORM + 四库** + migration | 部署灵活；生产可用 | 四套 migration 维护成本 |
| **企业能力独立成包** | 主包保持简单；商业化的清晰边界 | 两套代码路径；社区版功能受限 |
| **LangChain.js + LlamaIndex.ts 双引擎** | 节点可二选一框架；能力最大化 | 依赖膨胀；抽象层重叠 |
| **Redis 可选** | 单进程起步友好 | 同步路径与异步路径两套代码（`utilBuildChatflow` 内分支） |

---

## 10. 与竞品的架构对比

| 维度 | Flowise | [[langflow]] | [[dify]] |
|---|---|---|---|
| 语言 | TypeScript / Node.js | Python / FastAPI | Python + TS |
| 底层框架 | LangChain.js + LlamaIndex.ts | LangChain Python（内核已外化到 `lfx`） | 自研 + LangChain |
| 执行模型 | **自研 BFS 解释器**，逐节点 init/run | 图编译成单个 Runnable 后 invoke | 自研工作流引擎 |
| 节点注册 | 文件系统动态发现（CJS export） | 装饰器 + Python 类注册 | 代码 + YAML 声明 |
| 节点数 | 278（25 类） | 200+ | ~100 |
| 多租户 | 企业包（Org/Workspace/RBAC） | 无（v1）/ RBAC（v2 规划中） | 原生 |
| 代码导出 | ❌ 无 | ✅ Python/JSON | ❌ 无 |
| 队列 | BullMQ（可选 Redis） | Celery（必依赖 Redis） | Celery + Redis（必依赖） |
| Agent 编排 | 三层（经典/Multi/Sequential Agents） | LangGraph | 自研 |
| MCP | 双向（server + client） | 双向 | 客户端 |
| 可观测 | OTel + Arize/Phoenix/Opik | OTel | LangSmith / 自研 |
| 部署起步 | `npx flowise start`（单进程，零依赖） | `langflow run`（需 Redis） | docker compose（多服务） |
| 产品定位 | 快速原型 → 可生产（企业版） | 开发者工具 → 企业 | 全栈 LLMOps 平台 |

**一句话区分**：Flowise = **JS 生态、最轻起步、自研图引擎**；Langflow = **Python 生态、内核/外壳分离、代码导出**；Dify = **全栈平台、原生多租户、生产优先**。

---

## 11. 可借鉴的工程实践

1. **节点契约极简即王道**——`INode { inputs, init, run }` + `module.exports = { nodeClass }`，零装饰器零注册，扩展性极强。代价是失去静态分析，但用 TS interface 弥补类型契约。
2. **`baseClasses` 做类型系统**——用字符串数组表达产出类型，画布据此判连线合法性，比强类型 DAG 简单且足够。
3. **`loadMethods` 异步选项**——模型列表、索引名等不硬编码，编辑时动态拉，用户体验好。
4. **`filePath` + 每次 `import()` 重建实例**——避免跨请求状态泄漏的简洁方案（牺牲一点性能换隔离）。
5. **`DISABLED_NODES` + `author` 双闸门**——运维禁用 + 社区节点安全隔离，两道防线。
6. **企业能力独立包**——开源核心 + 商业增量的清晰边界，主包不背多租户复杂度。
7. **Redis 可选的渐进部署**——单进程能跑，加 Redis 水平扩展，`docker-compose` 与 `docker-compose-queue` 两套，照顾不同规模用户。
8. **MCP 双向**——既消费外部 MCP 工具，也把自家 chatflow 暴露成 MCP tool，融入更大的 agent 生态。
9. **OTel + 第三方 tracer（Arize/Phoenix/Opik）**——不自己造可观测轮子，对接专业平台。
10. **agentflow / observe 可嵌入 SDK 包**——把核心能力（画布、观测）做成可嵌入组件，从「应用」走向「平台/组件」。

---

## 相关

- [[flowise]] — 项目实体页（定位、快速开始、与竞品速览）
- [[langflow-architecture]] — Python 侧竞品的深度架构（内核 `lfx` 外化、装饰器注册、FastAPI）
- [[langflow]] / [[dify]] / [[n8n]] — 同类可视化工作流平台
- [[langchain]] — Flowise 的底层 LLM 抽象
- [[lobechat-architecture]] — 另一类 JS AI 应用架构（多 agent 会话产品）
- [[ai-workflow-landscape]] — AI Workflow 开源生态全景
