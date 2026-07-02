---
title: Kubernetes 原生 AI Agent 管理平台竞品对比
created: 2026-05-22
updated: 2026-05-22
type: comparison
tags: [kubernetes, ai-agent, competitive-analysis, platform, mcp, a2a]
sources: [Exa 神经搜索 + GitHub 调研]
confidence: medium
---

# Kubernetes 原生 AI Agent 管理平台竞品对比

> 对比 GitHub 上与 [[kagent]] 定位类似的 K8s-native AI Agent 管理平台。赛道非常早期（大多数 <1 年），核心分化点在于：CRD 深度、协议支持（MCP/A2A）、安全模型、社区背书。
> 调研时间：2026-05-22

---

## 一、竞品总览

```
                        赛道成熟度
                           ▲
                           │
            k8s-sigs ◄────┤
            Agent Sandbox  │
            (基础设施层)    │
                           │
                           │        kagent ◄── CNCF (Solo.io)
                           │        kagenti ◄── Red Hat
                           │        (全栈平台层)    │
                           │                       │
            kubectl-ai ◄───┤                       │
            (CLI 工具)      │                       │
                           │                       │
            KAITO ◄────────┤                       │
            (模型推理层)    │                       │
                           │                       │
                           └───────────────────────┘──► 功能广度
```

---

## 二、核心竞品详细对比

### 2.1 Kagenti（最直接竞品）

| 维度 | 详情 |
|------|------|
| **GitHub** | [kagenti/kagenti](https://github.com/kagenti/kagenti) (213⭐) |
| **背书** | Red Hat（Red Hat Next 博客多次推荐） |
| **语言** | Python + Go Operator |
| **协议** | A2A ✅ / MCP ❌ |
| **安全** | SPIFFE 零信任 mTLS + Istio Ambient Mesh |
| **CRD** | Component CRD |
| **UI** | Web UI ✅ |
| **Agent 发现** | Agent Card 系统 |

**与 kagent 对比：**
- 架构几乎一致（CRD + Operator + UI + A2A）
- Kagenti 安全更强：SPIFFE 身份 + Istio Ambient 零信任网络
- Kagent 社区更大：2.8K vs 213 stars
- Kagent 协议更广：MCP + A2A vs 仅 A2A
- Kagent 多运行时：ADK/CrewAI/LangGraph/Go ADK vs Kagenti ADK

**关键参考：**
- [Red Hat: Zero Trust AI Agents on Kubernetes](https://next.redhat.com/2026/03/05/zero-trust-ai-agents-on-kubernetes-what-i-learned-deploying-multi-agent-systems-on-kagenti/)
- [Red Hat Developers: How Kagenti ADK Simplifies Production](https://developers.redhat.com/articles/2026/05/04/how-kagenti-adk-simplifies-production-ai-agent-management)

---

### 2.2 Agent Sandbox（k8s-sigs 官方）

| 维度 | 详情 |
|------|------|
| **GitHub** | [kubernetes-sigs/agent-sandbox](https://github.com/kubernetes-sigs/agent-sandbox) (2,308⭐) |
| **背书** | Kubernetes SIG 官方项目 |
| **语言** | Go |
| **协议** | 无 MCP/A2A |
| **安全** | 沙箱隔离 + 稳定身份 + 持久存储 |
| **CRD** | CRD-based Agent 生命周期 |
| **UI** | 无 |
| **定位** | Agent 运行时基础设施层 |

**与 kagent 对比：**
- 更底层 — 专注沙箱化、身份保持、存储持久化
- 不做 Agent 编排/LLM 管理/UI
- kagent 的 SandboxAgent CRD 功能有重叠
- **可能是互补关系** — kagent 可在 Agent Sandbox 上层运行
- k8s-sigs 官方身份 = 潜在底层标准

**关键参考：**
- [Kubernetes Blog: Running Agents on Kubernetes](https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/)
- [InfoQ: Agent Sandbox Enables Secure Deployment](https://www.infoq.com/news/2025/12/agent-sandbox-kubernetes/)

---

### 2.3 AgentField

| 维度 | 详情 |
|------|------|
| **GitHub** | [Agent-Field/agentfield](https://github.com/Agent-Field/agentfield) (1,944⭐) |
| **背书** | 独立项目 |
| **语言** | Go |
| **协议** | 无 MCP/A2A |
| **安全** | 内置 IAM + 身份管理 |
| **架构** | Agent-as-microservice（HTTP/队列/指标） |
| **UI** | Web UI ✅ |

**与 kagent 对比：**
- "Kubernetes-style" 而非真正 CRD 原生
- 专注 Agent 作为可调用微服务（API 优先）
- 6 个月 1.9K stars — 增长速度快
- kagent 更深度集成 K8s（CRD/Operator/Helm/Controller）
- AgentField 更通用部署（不限于 K8s）

---

### 2.4 KAOS

| 维度 | 详情 |
|------|------|
| **GitHub** | [axsaucedo/kaos](https://github.com/axsaucedo/kaos) (253⭐) |
| **语言** | TypeScript |
| **定位** | K8s 多 Agent 层级编排 |
| **特色** | 层级 Agent 拓扑 + 自动委派 |
| **协议** | 无 MCP/A2A，OpenAI-compatible API |

**与 kagent 对比：**
- TypeScript vs Go+Python — 不同的技术栈偏好
- 无 MCP/A2A 协议支持是明显短板
- 层级委派模式有一定创新性

---

### 2.5 值得关注的新项目

#### EdgeCore
- [raphaelmansuy/edgecore](https://github.com/raphaelmansuy/edgecore) — 2026-05-19 创建（3天前）
- 自称 "self-hosted AWS Bedrock AgentCore / Google Agent Engine"
- K8s-native + MCP + A2A + **Firecracker/Kata 微 VM 隔离**
- 技术选型与 kagent 高度一致，但加了微 VM 安全隔离
- 0 采用，但方向值得关注

#### Agent Runtime Operator
- [agentic-layer/agent-runtime-operator](https://github.com/agentic-layer/agent-runtime-operator) — Go, Operator SDK
- 框架无关的 Agent 运行时部署 Operator
- 范围更窄，仅做部署层

---

## 三、功能矩阵对比

| 功能 | kagent | Kagenti | Agent Sandbox | AgentField | KAOS | EdgeCore |
|------|--------|---------|---------------|------------|------|----------|
| K8s CRD | ✅ 8个 | ✅ | ✅ | ❌ (style) | ❌ | ✅ |
| Operator/Controller | ✅ 7个 | ✅ | ✅ | ❌ | ❌ | ✅ |
| MCP 协议 | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ |
| A2A 协议 | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ |
| 多 LLM Provider | ✅ 6个 | ✅ | ❌ | ✅ | ✅ OpenAI | ✅ |
| 多 Agent 框架 | ✅ 4个 | ✅ | ❌ | ❌ | ❌ | ❌ |
| Web UI | ✅ | ✅ | ❌ | ✅ | ❌ | ❌ |
| Helm Charts | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ |
| OIDC/Auth | ✅ | SPIFFE | ❌ | IAM | ❌ | ❌ |
| OpenTelemetry | ✅ | ❌ | ❌ | ✅ | ❌ | ✅ |
| 沙箱隔离 | ✅ SandboxAgent | ❌ | ✅ 核心 | ❌ | ❌ | Firecracker |
| 记忆系统 | 🔜 设计中 | ❌ | ❌ | ❌ | ❌ | ❌ |
| Stars | 2,824 | 213 | 2,308 | 1,944 | 253 | 1 |

---

## 四、战略分析

### 4.1 kagent 的竞争优势

1. **CNCF 背书**（Solo.io 赞助）— 品牌信任度
2. **最广协议支持** — 同时支持 MCP（工具）+ A2A（Agent 间）
3. **多运行时** — ADK/CrewAI/LangGraph/OpenAI/Go ADK，用户不被锁定
4. **预置 Agent 生态** — 8 个 Helm Agent Charts（K8s/Istio/Cilium/Argo/Prometheus）
5. **社区活跃度** — 20+ 贡献者，每天 2-5 个 PR

### 4.2 kagent 的风险

1. **Agent Sandbox (k8s-sigs)** 可能标准化底层 — kagent 的 SandboxAgent CRD 需与之对齐或依赖
2. **Kagenti (Red Hat)** 企业安全更强 — SPIFFE 零信任在政企场景有优势
3. **AgentField 增速快** — "Agent-as-Service" 更易上手，可能吸引不想深度用 K8s 的用户
4. **赛道太早期** — 所有项目都在 v0.x，API 可能大幅变动

### 4.3 可能的演进方向

```
当前格局:
┌─────────────┐  ┌─────────────┐  ┌──────────────┐
│  kagent     │  │  Kagenti    │  │ Agent Sandbox│
│  (全栈)     │  │  (全栈+安全) │  │  (基础设施)  │
└─────────────┘  └─────────────┘  └──────────────┘

可能的整合:
┌──────────────────────────────────────┐
│         上层 Agent 平台              │
│  kagent / Kagenti / AgentField       │
├──────────────────────────────────────┤
│         底层运行时标准               │
│  Agent Sandbox (k8s-sigs)            │
├──────────────────────────────────────┤
│         协议层                       │
│  MCP (工具) + A2A (Agent 间)         │
└──────────────────────────────────────┘
```

---

## 五、相关生态（非直接竞品）

| 项目 | Stars | 定位 | 与 kagent 关系 |
|------|-------|------|---------------|
| [kubectl-ai](https://github.com/GoogleCloudPlatform/kubectl-ai) | 7,470 | AI 辅助 kubectl CLI | 不同赛道（用 AI 操作 K8s vs 管理 AI Agent） |
| [KAITO](https://github.com/kaito-project/kaito) | 942 | LLM 推理/微调 GPU Operator | 互补（KAITO 管模型，kagent 管 Agent） |
| [kmcp](https://github.com/kagent-dev/kmcp) | 462 | MCP Server 生命周期管理 | kagent 同组织附属项目 |
| [Kubeflow](https://github.com/kubeflow/kubeflow) | 15,652 | MLOps 全平台 | 不同赛道（ML 训练 vs Agent 管理） |

---

## 关联

- [[kagent]] — 本次调研的主要分析对象
- [[adk-python]] — kagent 和 Kagenti 共用的 Google ADK 运行时
- [[a2a-protocol]] — kagent 和 Kagenti 共同采用的 Agent 间通信协议
- [[superpowers]] — AI Agent 工程流程规范，适用于所有 Agent 平台
- [[context-mode]] — Agent 开发工具链通用优化方案
