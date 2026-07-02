---
title: Kagent CRD 能力边界分析
created: 2026-05-26
updated: 2026-05-26
type: concept
tags: [ai, kubernetes, crd, architecture, agent]
sources: [~/Projects/kagent/ 源码研究]
confidence: high
---

# Kagent CRD 能力边界分析

> CRD 是 kagent 的核心抽象层，将 Kubernetes 声明式模型映射到 AI Agent 运行时。本文从 CRD 定义、翻译层、Python 运行时三个维度分析 CRD 对底层框架能力的裁剪程度，以及这种架构权衡的利弊。

---

## 1. 研究方法

数据来源：
- **CRD 类型定义**: `go/api/v1alpha2/agent_types.go`, `modelconfig_types.go`
- **ADK 类型**: `go/api/adk/types.go`, `python/packages/kagent-adk/src/kagent/adk/types.py`
- **翻译层**: `go/core/internal/controller/translator/agent/` (adk_api_translator.go, deployments.go)
- **样本 Agent**: `python/samples/` (OpenAI, CrewAI, LangGraph)

---

## 2. CRD 目前覆盖了什么

### 2.1 多 LLM Provider 支持

CRD ModelConfig 支持 8 种 Provider，字段覆盖较完整：

| Provider | CRD 字段 | 覆盖度 |
|----------|---------|--------|
| **OpenAI** | baseUrl, organization, temperature, maxTokens, topP, frequencyPenalty, presencePenalty, seed, n, timeout, reasoningEffort, tokenExchange | 高 |
| **Azure OpenAI** | azureEndpoint, apiVersion, azureDeployment, azureAdToken, temperature, maxTokens, topP | 中 |
| **Anthropic** | baseUrl, maxTokens, temperature, topP, topK | 中 |
| **Gemini/VertexAI** | projectID, location, temperature, topP, topK, stopSequences, maxOutputTokens, candidateCount, responseMimeType | 中 |
| **Bedrock** | region, additionalModelRequestFields (JSON passthrough) | 中 |
| **Ollama** | host, options (map) | 低 |
| **SAP AI Core** | baseUrl, authUrl, resourceGroup | 低 |
| **Gemini Anthropic VertexAI** | 继承 BaseVertexAIConfig + maxTokens | 低 |

通用字段: APIKeySecret, APIKeyPassthrough, DefaultHeaders, TLS (CA cert/disable verify)

### 2.2 Agent 配置

| 能力 | CRD 字段 | 状态 |
|------|---------|------|
| 系统提示 | systemMessage, systemMessageFrom (ConfigMap/Secret) | 完整 |
| Prompt 模板 | promptTemplate (Go template + DataSource) | 完整 |
| 流式响应 | stream | 完整 |
| 工具 | tools (McpServer + Agent, max 20) | 部分 |
| 技能加载 | skills (容器镜像 + Git 仓库) | 完整 |
| 长期记忆 | memory (TTL + embedding model) | 完整 |
| 上下文压缩 | context.compaction (interval/overlap/summarizer/threshold/retention) | 完整 |
| 网络沙箱 | sandbox.network.allowedDomains | 完整 |
| A2A 协议 | a2aConfig | 完整 |
| 代码执行 | executeCodeBlocks | **已禁用** (ADK bug) |

### 2.3 部署控制 (SharedDeploymentSpec)

完整的 Kubernetes 标准: image, resources, replicas, imagePullPolicy, tolerations, affinity, nodeSelector, securityContext, podSecurityContext, volumes, volumeMounts, env, serviceAccount, extraContainers

---

## 3. CRD 阉割了哪些能力

### 3.1 框架级能力完全丢失 (最关键)

CRD 只有两种 Agent 类型: `Declarative` 和 `BYO`。Declarative 类型将底层框架抽象为 **"单 Agent + MCP 工具"** 的扁平模型。

| 框架 | 丢失的核心能力 |
|------|--------------|
| **OpenAI Agents SDK** | Agent 交接 (handoff)、结构化输出 (structured output)、文件搜索工具、代码解释器工具、追踪 (tracing)、自定义 HTTP client |
| **CrewAI** | 多 Agent 协作流程 (sequential/hierarchical)、Agent 委派、任务优先级、上下文共享、Human-in-the-loop |
| **LangGraph** | 条件边 (conditional edges)、状态图编译、命令执行模式、Tool Node、自定义 checkpoint |

**本质问题**: CRD 无法表达多 Agent 编排（flow/pipeline/graph）。底层框架最强大的编排能力被完全忽略。

### 3.2 工具类型严重受限

CRD 只支持两种工具:
- `McpServer` — MCP 协议的工具服务器 (HTTP/SSE)
- `Agent` — 将另一个 Agent 作为工具

**缺失的工具类型**:
- 函数工具 (Function tools) — 直接调用 Python 函数
- 内置工具 (Built-in tools) — 文件搜索、代码执行、网页搜索
- 自定义工具注册 — 没有扩展机制

这意味着 Agent 只能通过 MCP 协议使用外部工具，不能直接注册本地 Python 函数。

### 3.3 硬编码数量限制

```
Tools per agent:     max 20
ToolNames per MCP:   max 50
Skills per agent:    max 20
ImagePullSecrets:    max 20
```

对于需要连接 30+ 个微服务的复杂生产场景，20 个工具上限可能不够。

### 3.4 功能性缺陷

| 问题 | 影响 | 来源 |
|------|------|------|
| ExecuteCodeBlocks 被禁用 | 代码执行能力不可用 | ADK bug #3921 |
| 只支持 Python/Go 运行时 | 不支持 Node.js、Java 等 | runtime enum 只有 python/go |
| BYO 无法使用内置特性 | Memory/Compaction/Sandbox 只对 Declarative | 架构限制 |
| 没有 Session CRD | 会话管理依赖 HTTP API，无声明式管理 | 缺失 |
| 没有 MCP Server CRD | MCP 服务器不能作为 K8s 资源管理 | 缺失 |
| 只支持 IPv4 | 绑定地址硬编码 0.0.0.0 | deployments.go |
| 默认资源过低 | CPU 100m / Memory 128Mi | 生产可能不够 |

### 3.5 翻译层信息损失

Controller 将 CRD 翻译为 ADK Config 时，部分字段被忽略或简化:

| CRD 字段 | 处理方式 | 原因 |
|----------|---------|------|
| `spec.Type` | 仅路由，不传递给运行时 | 控制面字段 |
| `spec.AllowedNamespaces` | 仅安全约束，运行时不知道 | 控制面字段 |
| `spec.Skills` | 通过 init container 处理 | 不在 ADK config |
| Provider 高级设置 | 如果 ADK 没有对应字段则丢弃 | Schema 不匹配 |
| `spec.A2AConfig` | 单独处理 | 不在 ADK config |

翻译层还施加了硬限制: **MAX_DEPTH = 10**（防止无限 Agent 链）。

---

## 4. BYO 模式的逃生舱口

BYO (Bring Your Own) 模式让用户自带容器镜像，理论上可以使用任何框架的全部能力:

**获得**: 完整部署控制、自定义运行时/镜像、复杂架构
**失去**: 自动部署管理、Memory、Context Compaction、Sandbox、A2A 协议兼容、MCP 工具自动集成

BYO 模式本质上退化为"在 K8s 上跑一个 Pod"，kagent 的核心价值大打折扣。

---

## 5. 设计权衡分析

### 5.1 为什么这样设计

这是**有意的架构权衡**，不是疏忽:

1. **统一抽象层**: 类似 Kubernetes 对容器的抽象——跨框架一致性必然要裁剪特殊能力
2. **声明式运维**: CRD 带来自动部署、健康检查、滚动更新、密钥管理
3. **协议标准化**: A2A + MCP 双协议保证互操作性
4. **企业友好**: RBAC、namespace 隔离、TLS、审计日志

### 5.2 核心差距总结

| 差距 | 严重度 | 影响 |
|------|--------|------|
| 缺少多 Agent 编排的 CRD 表达 | **高** | 无法声明式定义 Agent 协作流程 |
| 工具模型过于简单 | **高** | 只有 MCP + Agent，无函数工具/内置工具 |
| Session/MCPServer 不是 CRD | **中** | 无法声明式管理生命周期 |
| 数量限制 (20 tools) | **中** | 复杂场景受限 |
| ExecuteCode 禁用 | **低** | 临时 bug，可修复 |

---

## 6. 演进方向

如果 kagent 要从"单 Agent 管理工具"进化为"Agent 编排平台":

1. **Flow/Pipeline CRD** — 定义多 Agent 编排流程（类似 Argo Workflows 的 DAG 模式）
2. **Tool CRD 扩展** — 支持函数工具、内置工具注册
3. **Session CRD** — 声明式会话管理
4. **MCPServer CRD** — MCP 服务器作为一级资源
5. **框架特定注解** — 通过 annotation 暴露框架特定能力，翻译层按需处理

---

## 关联

- [[kagent]] — Kagent 项目实体页
- [[kagent-documentation-system]] — Kagent 文档体系分析
- [[adk-python]] — Google ADK Python 框架（底层运行时之一）
- [[a2a-protocol]] — A2A 协议技术参考
- [[orloj]] — Orloj 多 Agent 平台（有 8 CRD + 治理审批，可对比编排能力）
- [[kubernetes-agent-platforms]] — K8s Agent 平台竞品对比
