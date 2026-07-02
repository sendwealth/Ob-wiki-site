---
title: Agent Sandbox (kubernetes-sigs)
created: 2026-05-26
updated: 2026-06-28
type: entity
tags: [ai, kubernetes, platform, sandbox, open-source]
sources:
  - https://kubernetes.io/blog/2026/03/20/running-agents-on-kubernetes-with-agent-sandbox/
  - https://github.com/kubernetes-sigs/agent-sandbox
confidence: high
---

# Agent Sandbox

> Kubernetes SIG Apps 官方项目，为 AI Agent 提供隔离、有状态、单例的运行环境。Sandbox CRD 解决了传统 K8s 原语（Deployment/StatefulSet）无法完美匹配 Agent 工作负载的问题——Agent 需要稳定身份、持久存储、代码执行隔离、以及"大部分时间空闲+偶尔突发"的生命周期管理。

---

## 1. 项目定位

- **组织**: kubernetes-sigs / SIG Apps
- **作者**: Janet Kuo (Kubernetes SIG Apps Chair), Justin Santa Barbara
- **版本**: v1beta1 (API), 507 commits, 活跃开发中
- **核心论点**: AI Agent 是**隔离的、有状态的、单例工作负载**，与传统无状态/副本化模型不匹配。用 StatefulSet(replicas=1) + headless Service + PVC 拼装，规模化后运维成本爆炸。

**一句话**: Agent Sandbox = 为 Agent 量身定做的 "StatefulSet of 1"，加上安全隔离、生命周期管理、预热池。

---

## 2. 架构

```
┌─────────────────────────────────────────────────┐
│                  用户 / AI Agent                  │
│              (Python SDK / kubectl)               │
└───────────┬─────────────────────────────────────┘
            │ create Sandbox / SandboxClaim
            ▼
┌─────────────────────────────────────────────────┐
│           Agent Sandbox Controller               │
│        (controller-runtime, Go)                  │
│                                                  │
│  ┌──────────┐ ┌───────────────┐ ┌────────────┐  │
│  │ Sandbox  │ │ SandboxClaim  │ │ WarmPool   │  │
│  │ Reconcile│ │ Reconcile     │ │ Reconcile  │  │
│  └────┬─────┘ └──────┬────────┘ └─────┬──────┘  │
│       │              │                 │          │
│       ▼              ▼                 ▼          │
│  ┌─────────────────────────────────────────────┐ │
│  │           SandboxTemplate                   │ │
│  │    (PodTemplate + PVC + NetworkPolicy)      │ │
│  └─────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────┘
            │ creates / manages
            ▼
┌─────────────────────────────────────────────────┐
│              Kubernetes Cluster                   │
│  ┌─────────┐  ┌─────────┐  ┌────────────────┐  │
│  │   Pod   │  │  PVC    │  │ Headless Svc   │  │
│  │(gVisor/ │  │(persist │  │ (stable DNS)   │  │
│  │ Kata)   │  │ scratch)│  │                │  │
│  └─────────┘  └─────────┘  └────────────────┘  │
└─────────────────────────────────────────────────┘
```

---

## 3. CRD 资源模型

### 3.1 核心 CRD: Sandbox

```yaml
apiVersion: agents.x-k8s.io/v1beta1
kind: Sandbox
metadata:
  name: my-agent
spec:
  podTemplate:
    spec:
      containers:
      - name: agent
        image: python:3.12
  volumeClaimTemplates:        # 持久化 scratch 空间
  - spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi
  replicas: 1                  # 只允许 0 或 1
  service: true                # 自动创建 headless Service
  shutdownTime: "2026-04-01T00:00:00Z"  # 定时过期
  shutdownPolicy: Retain       # 或 Delete
```

**SandboxSpec 关键字段**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `podTemplate` | PodTemplate | Pod 定义（必填），嵌套 PodSpec + metadata |
| `volumeClaimTemplates` | []PVC template | 持久卷声明，数据跨重启保留 |
| `replicas` | 0 或 1 | Scale to zero 暂停，1 运行 |
| `service` | *bool | 自动创建 headless Service |
| `lifecycle.shutdownTime` | Time | 绝对过期时间 |
| `lifecycle.shutdownPolicy` | Retain/Delete | 过期后是否删除 CR 对象 |

**SandboxStatus**:

| 字段 | 说明 |
|------|------|
| `serviceFQDN` | 稳定的集群内 DNS 名 |
| `conditions` | Ready / Suspended / Finished 三种状态 |
| `podIPs` | 底层 Pod IP |
| `replicas` | 实际副本数 |

### 3.2 扩展 CRD

#### SandboxTemplate — 可复用模板

```yaml
apiVersion: agents.x-k8s.io/v1beta1
kind: SandboxTemplate
metadata:
  name: python-agent
spec:
  podTemplate:
    spec:
      containers:
      - name: agent
        image: python-agent:latest
  volumeClaimTemplates: [...]
  networkPolicy:              # 安全默认：仅允许 Router 入站 + 公网出站
    ingress: [...]
    egress: [...]
```

关键特性:
- **Secure-by-default**: `AutomountServiceAccountToken` 默认 false
- **网络策略**: 默认严格策略（仅 Router 入站 + 仅公网出站，阻塞 RFC1918 内网和 Metadata Server）
- **NetworkPolicyManagement**: Managed（默认）/ Unmanaged

#### SandboxClaim — 从模板申请沙箱

```yaml
apiVersion: agents.x-k8s.io/v1beta1
kind: SandboxClaim
metadata:
  name: my-task
spec:
  sandboxTemplateRef:
    name: python-agent
  lifecycle:
    shutdownTime: "2026-04-01T00:00:00Z"
    ttlSecondsAfterFinished: 3600  # 完成后 1h 自动清理
    shutdownPolicy: Delete
  warmpool: default             # 使用预热池加速启动
  env:                          # 注入环境变量
  - name: API_KEY
    value: "xxx"
    containerName: agent
```

关键特性:
- **TTL 清理**: `ttlSecondsAfterFinished` 自动回收
- **WarmPool 策略**: none / default / 指定池名
- **额外元数据**: 可注入 labels/annotations 到 Pod

#### SandboxWarmPool — 预热池

```yaml
apiVersion: agents.x-k8s.io/v1beta1
kind: SandboxWarmPool
metadata:
  name: fast-pool
spec:
  replicas: 5                  # 保持 5 个预热沙箱
  sandboxTemplateRef:
    name: python-agent
  updateStrategy:
    type: OnReplenish           # 池变更时的更新策略
```

关键特性:
- **预热**: 预创建 Sandbox，Claim 直接领用，零等待
- **HPA 集成**: `replicas` 可被 HPA 控制
- **更新策略**: OnReplenish（补充时更新）

---

## 4. 核心设计决策

### 4.1 三大核心能力

| 能力 | 实现 | 与 kagent 对比 |
|------|------|---------------|
| **安全隔离** | gVisor / Kata Containers 内核级隔离 | kagent 用 Docker + network allowlist（较弱） |
| **生命周期管理** | Scale to zero（replicas=0）+ PVC 保持 + 自动 resume | kagent 无此概念，Agent 始终运行 |
| **稳定身份** | 自动 headless Service + FQDN | kagent 通过 Service 暴露（类似） |

### 4.2 理想的沙箱特性 (Roadmap)

- Strong Isolation (gVisor / Kata / QEMU / Firecracker)
- Deep hibernation（状态持久化 + 对象归档）
- Automatic resume（网络连接触发恢复）
- Efficient persistence（弹性快速分配存储）
- Memory sharing across sandboxes（同主机内存共享）
- Rich identity & connectivity（双身份 + 无 Service 路由）
- Programmable（鼓励 Agent 通过 API 消费 Sandbox）

### 4.3 Sandbox vs 传统 K8s 原语

| 维度 | Deployment | StatefulSet | **Sandbox** |
|------|-----------|-------------|-------------|
| 副本模型 | 水平扩展 | 有序编号 | **严格单例 (0 或 1)** |
| 身份 | 随机 Pod 名 | 稳定编号名 | **稳定 hostname** |
| 存储 | 临时/共享 | PVC 模板 | **PVC 模板 + 跨重启** |
| 生命周期 | 滚动更新 | 有序更新 | **暂停/恢复/过期** |
| 隔离 | 共享内核 | 共享内核 | **gVisor/Kata 内核隔离** |
| 网络策略 | 需手动 | 需手动 | **默认严格安全策略** |
| 预热 | 无 | 无 | **WarmPool 预创建** |

---

## 5. Python SDK

```python
from k8s_agent_sandbox import SandboxClient
from k8s_agent_sandbox.models import SandboxLocalTunnelConnectionConfig

# 同步客户端（本地开发）
client = SandboxClient(
    connection_config=SandboxLocalTunnelConnectionConfig(server_port=3000)
)

sandbox = client.create_sandbox(template="python-sandbox-template", namespace="default")

# 在沙箱内执行命令
result = sandbox.commands.run("pip install numpy && python -c 'import numpy'")
print(result.stdout)

# 异步客户端（生产/集群内）
from k8s_agent_sandbox import AsyncSandboxClient
from k8s_agent_sandbox.models import SandboxDirectConnectionConfig

async with AsyncSandboxClient(
    connection_config=SandboxDirectConnectionConfig(
        api_url="http://sandbox-router-svc.default.svc.cluster.local:8080"
    )
) as client:
    sandbox = await client.create_sandbox(template="python-sandbox-template")
    result = await sandbox.commands.run("echo hello")
    await sandbox.terminate()
```

SDK 支持四种连接模式:
- `SandboxLocalTunnelConnectionConfig` — kubectl port-forward（开发）
- `SandboxGatewayConnectionConfig` — 通过网关路由（生产）
- `SandboxDirectConnectionConfig` — 直连路由 Service（集群内）
- `SandboxInClusterConnectionConfig` — 集群内 DNS（Agent-to-Agent）

---

## 6. 与 kagent 的关系

### 6.1 互补而非竞争

| 维度 | Agent Sandbox | kagent |
|------|--------------|--------|
| **抽象层级** | 基础设施层（Pod + 存储 + 隔离） | 应用层（Agent + LLM + 工具 + MCP） |
| **核心 CRD** | Sandbox (单例 Pod) | Agent (LLM + 工具 + 部署) |
| **解决什么** | "怎么安全地跑一个 Agent 进程" | "怎么定义一个 Agent 的行为" |
| **LLM 集成** | 无（不关心） | 多 Provider 模型配置 |
| **工具/MCP** | 无（不关心） | MCP + A2A + 技能系统 |
| **安全模型** | gVisor/Kata 内核隔离 | 网络白名单 |
| **生命周期** | 暂停/恢复/过期/TTL | 始终运行 |

### 6.2 集成路径

Roadmap 明确提到 **"Integration with kAgent"**。可能的集成方式:

1. **kagent 使用 Agent Sandbox 作为底层运行时**: Agent CRD 创建的 Pod → 改为创建 Sandbox，获得安全隔离 + 生命周期管理
2. **SandboxSpec 嵌入 Agent CRD**: Agent 的 `deployment` 部分引用 SandboxTemplate，而非直接定义 Pod
3. **WarmPool 加速 Agent 启动**: 预热 Python/Go 运行时环境，Agent 创建时直接领用

### 6.3 kagent 可以学到什么

| Agent Sandbox 特性 | kagent 现状 | 建议 |
|-------------------|------------|------|
| Scale to zero | Agent 始终运行 | 空闲 Agent 缩容到 0，节省资源 |
| gVisor/Kata 隔离 | Docker + network allowlist | 代码执行场景需要内核级隔离 |
| Secure-by-default | 需手动配置 | 默认拒绝不必要的网络/权限 |
| WarmPool 预热 | 无 | 冷启动慢时可预热 Agent 运行时 |
| TTL 自动清理 | 无 | 临时 Agent 用完自动回收 |
| NetworkPolicy | 无 | 默认严格网络策略 |

---

## 7. Roadmap (2026)

**核心优先级**:
- 文档大修 + 网站刷新
- PyPI 发布 SDK
- SDK 扩展（read/write/run_code 原生方法）
- 严格的 1:1 Sandbox-Pod 映射
- 计算机使用/浏览器使用场景 + 基础镜像

**高级特性**:
- API 与运行时解耦（自定义运行时不破坏 API）
- Go Client SDK
- PVC-based Scale-down/Resume
- Multi-Sandbox per Pod
- Startup Actions（启动时自动暂停）
- 自动删除 bursty 沙箱（RL 训练场景）
- OTel/Tracing 可观测性
- Falco + gVisor 安全日志
- QEMU / Firecracker / 其他隔离技术
- OpenEnv 支持

**框架集成**:
- CrewAI / Ray RLlib 集成
- **kAgent 集成**（明确列入 roadmap）
- 其他 Sandbox 方案集成

---

## 8. 技术栈

| 组件 | 技术 |
|------|------|
| Controller | Go + controller-runtime + kubebuilder |
| CRD API | v1beta1 (agents.x-k8s.io) |
| 隔离运行时 | gVisor / Kata Containers |
| Python SDK | k8s-agent-sandbox (pip) |
| 网络 | Headless Service + FQDN |
| 存储 | PVC template + 跨重启持久化 |
| 安全 | NetworkPolicy + SA token auto-mount=false |

---

## 关联

- [[kagent]] — kagent 项目实体页（应用层 Agent 框架，互补关系）
- [[kagent-crd-limitations]] — kagent CRD 能力边界分析（可对比 Sandbox CRD 的设计思路）
- [[kubernetes-agent-platforms]] — K8s Agent 平台竞品对比
- [[a2a-protocol]] — A2A 协议（Agent 间通信，Sandbox 提供稳定身份支持）
- [[orloj]] — Orloj 多 Agent 平台（同样关注 Agent 基础设施化）

## 最新动态（截至 2026-06-28）

> [!note] GKE Agent Sandbox GA，K8s 正式成为 agent 执行标准平台
> 2026-03 Kubernetes 官方博客专题介绍 Agent Sandbox，**GKE Agent Sandbox 已 GA**。Google 开源博客 2025-11 宣布它为 SIG Apps 正式子项目，目标是"标准化 K8s 作为 agent 执行平台"。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| SIG Apps 状态 | 子项目 | **正式子项目**（2025-11 Google 官宣）|
| 云落地 | 实验性 | **GKE Agent Sandbox GA** |
| 官方背书 | 社区 | **K8s 官方博客专题（2026-03-20）** |

### 2026 关键节点
- **2026-03-20 官方博客**：《Running Agents on Kubernetes with Agent Sandbox》系统介绍 Sandbox CRD
- **GKE GA**：Google Cloud 博客宣布 GKE Agent Sandbox 一般可用，提供安全可扩展的 agent 工作负载底座
- **Pre-Warming Pool**：社区讨论预热池特性，消除安全容器冷启动问题（gVisor/Kata）

### 战略意义
Agent Sandbox 让 K8s 正式进入"agent 执行平台"赛道。它与 [[openshell]]（NVIDIA NemoClaw，治理层）、[[kagent]]（CNCF，编排层）形成 K8s agent 基础设施的三层栈：
- **隔离层**：Agent Sandbox（gVisor/Kata 沙箱）
- **治理层**：OpenShell（策略/审计）
- **编排层**：kagent（声明式 agent CRD）

### 生态信号
- Reddit r/kubernetes 社区讨论预热池特性，关注度上升
- Northflank/Medium 等出现部署教程，落地案例增加

### 仍待观察
- 与 [[openshell]] 的竞合（都在做 agent 隔离）
- 非 GKE 的本地/自托管 K8s 支持
