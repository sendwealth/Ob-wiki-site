---
title: Kagent Agent Harness 概念解析
created: 2026-05-26
updated: 2026-05-27
type: concept
tags: [ai, kubernetes, kagent, sandbox]
sources:
  - ~/Projects/kagent/go/api/v1alpha2/agentharness_types.go
  - ~/Projects/kagent/go/core/internal/controller/agentharness_controller.go
  - ~/Projects/kagent/go/core/pkg/sandboxbackend/openshell/agentharness_openshell_client.go
confidence: high
---

# Kagent Agent Harness 概念解析

> AgentHarness 是 kagent 中与 Agent CRD 平行但目的完全不同的资源类型。Agent 提供智能（LLM + 工具），AgentHarness 提供环境（远程执行沙箱）。它通过外部后端（OpenClaw/NemoClaw）创建可 SSH/exec 的 VM 环境，但不在 K8s 集群内运行任何工作负载。

---

## 1. 三种 Agent 资源对比

kagent 有三种 CRD 都叫 "Agent"，但解决不同问题：

| 维度 | **Agent** | **AgentHarness** | **SandboxAgent** |
|------|-----------|-----------------|-----------------|
| CRD | `kagent.dev/v1alpha2.Agent` | `kagent.dev/v1alpha2.AgentHarness` | `kagent.dev/v1alpha2.SandboxAgent` |
| 短名 | `ag` | `ahr` | — |
| **核心定位** | AI Agent（有大脑） | 远程执行环境（无大脑） | 隔离沙箱中的 AI Agent |
| **Agent 运行时** | 内置（Python/Go ADK） | 无 | 内置（复用 AgentSpec） |
| **LLM 集成** | 有（多 Provider） | 无（可选 ModelConfig 仅用于网关配置） | 有 |
| **工作负载位置** | K8s 集群内 Deployment | 外部后端 VM | agent-sandbox Sandbox CR |
| **访问方式** | HTTP/A2A 协议 | exec / SSH | K8s Service |
| **底层实现** | controller 创建 Pod | OpenShell gRPC → 外部 VM | agent-sandbox controller |
| **适用场景** | 生产 AI Agent | 人工操作的远程环境、开发沙箱 | 安全隔离的 AI Agent |

```
一句话总结:
  Agent        = "有 AI 大脑的 Worker"
  AgentHarness = "可 SSH 的空壳 VM"
  SandboxAgent = "跑在沙箱里的 Agent"
```

---

## 2. AgentHarness 详细设计

### 2.1 CRD Spec 结构

```yaml
apiVersion: kagent.dev/v1alpha2
kind: AgentHarness
metadata:
  name: my-dev-env
spec:
  # 后端选择（必填）
  backend: openclaw            # openclaw | nemoclaw

  # 人类可读描述
  description: "Development environment for team X"

  # 容器镜像（空则用后端默认）
  image: ubuntu:22.04

  # 环境变量
  env:
  - name: MY_VAR
    value: "hello"

  # 网络控制
  network:
    allowedDomains:
    - "*.github.com"
    - "pypi.org"

  # LLM 网关配置（不是让 harness 有 AI 能力，
  # 而是在 VM 内配置 OpenClaw gateway，让 VM 内的工具能调用 LLM）
  modelConfigRef: default-model-config

  # 消息集成（Telegram/Slack）
  channels:
  - name: my-bot
    type: telegram
    telegram:
      tokenSecret:
        name: telegram-bot-token
        key: token
```

### 2.2 Spec 字段详解

| 字段 | 类型 | 说明 |
|------|------|------|
| `backend` | enum: openclaw/nemoclaw | 控制平面选择（必填） |
| `description` | string | UI 显示用 |
| `image` | string | VM 中运行的容器镜像 |
| `env` | []corev1.EnvVar | 注入 VM 的环境变量 |
| `network` | AgentHarnessNetwork | 出站域名白名单 |
| `modelConfigRef` | string | 引用 ModelConfig → 写入 VM 内 `~/.openclaw/openclaw.json` |
| `channels` | []AgentHarnessChannel | Telegram/Slack 集成（互斥验证） |

### 2.3 Status 结构

```yaml
status:
  observedGeneration: 1
  backendRef:
    backend: openclaw
    id: "sandbox-abc123"           # 后端沙箱 ID
  connection:
    endpoint: "ssh://user@host:22"  # 连接端点
  conditions:
  - type: Accepted
    status: "True"
    reason: AgentHarnessAccepted
  - type: Ready
    status: "True"
    reason: SandboxRunning
```

---

## 3. Controller 协调流程

```
用户创建 AgentHarness CR
         │
         ▼
┌─────────────────────────┐
│ AgentHarnessController  │
│ (agentharness_controller│
│       .go)              │
└────────┬────────────────┘
         │
         │ 1. 添加 Finalizer
         │    "kagent.dev/agent-harness-backend-cleanup"
         │
         │ 2. 查找 Backend 实现
         │    Backends[spec.backend] → AsyncBackend 接口
         │
         ▼
┌─────────────────────────┐
│   AsyncBackend 接口      │
│  (sandboxbackend 包)     │
│                         │
│  EnsureAgentHarness()   │──── gRPC ────→ OpenShell 后端
│  GetStatus()            │                  (外部 VM)
│  DeleteAgentHarness()   │
│  OnAgentHarnessReady()  │  ←─── 创建/查询/删除沙箱
└────────┬────────────────┘
         │
         │ 3. 更新 Status
         │    backendRef.id = 沙箱 ID
         │    connection.endpoint = SSH 端点
         │    conditions: Accepted + Ready
         │
         │ 4. Post-Ready Bootstrap（仅一次）
         │    OnAgentHarnessReady() → 在 VM 内执行初始化
         │    如：写入 openclaw.json、启动 gateway
         │    标记 annotation: kagent.dev/agent-harness-bootstrap-generation
         │
         │ 5. 如果未 Ready → 10s 后重新排队
         │
         ▼
    Ready ✓
    用户可通过 SSH/exec 访问 VM
```

### 3.1 关键设计

- **异步后端**: `AsyncBackend` 接口抽象了 OpenClaw/NemoClaw，通过 gRPC 与外部控制平面通信
- **幂等创建**: `EnsureAgentHarness` 先查找已有沙箱，避免重复创建
- **Finalizer 保护**: 删除 CR 前先调用 `DeleteAgentHarness` 清理外部 VM
- **Generation 追踪**: 通过 `observedGeneration` 和 bootstrap annotation 确保只在 spec 变更时重新初始化
- **Post-Ready Hook**: VM 就绪后才执行一次性初始化（配置 LLM 网关、启动服务）

### 3.2 OpenShell 后端交互

```
AgentHarnessController
    │
    ▼
AgentHarnessOpenShellClient (openshell 包)
    │
    │  gRPC 调用:
    │  ├── CreateSandbox → 创建 VM
    │  ├── GetSandbox    → 查询状态 (phase → Ready condition)
    │  ├── DeleteSandbox → 删除 VM
    │  └── ExecSandbox   → 在 VM 内执行命令 (streaming)
    │
    ▼
OpenShell gRPC Server (openshellv1)
    │
    ▼
NemoClaw / OpenClaw 沙箱运行时
```

`ExecSandbox` 使用流式 gRPC，支持 stdin/stdout/stderr + exit code：

```go
// 在 VM 内执行命令
exitCode, stderr, err := client.ExecSandbox(ctx, sandboxID, 
    []string{"pip", "install", "numpy"}, 
    nil,   // stdin
    nil,   // env
    30,    // timeout seconds
)
```

---

## 4. OpenShell — 外部沙箱网关

### 4.1 什么是 OpenShell

**OpenShell 是 NVIDIA 的 AI Agent 安全沙箱运行时**，独立于 kagent 部署。它是一个 gRPC 网关服务，提供隔离的沙箱 VM 生命周期管理。

核心 RPC（定义在 `go/api/openshell/proto/openshell.proto`）：

| RPC | 用途 |
|-----|------|
| `CreateSandbox` / `GetSandbox` / `DeleteSandbox` | 沙箱生命周期 |
| `ExecSandbox` | 在沙箱内执行命令（streaming stdout/stderr/exit code） |
| `CreateSshSession` / `RevokeSshSession` | SSH 会话管理 |
| `ConnectSupervisor` | 持久双向流（沙箱↔网关协调） |
| `GetDraftPolicy` / `ApproveDraftChunk` | AI 驱动的安全策略推荐 |
| `Health` | 健康检查 |

### 4.2 两个后端变体

| 变体 | 说明 | 镜像 |
|------|------|------|
| **OpenClaw** | 基础沙箱后端 | 用户指定或默认 |
| **NemoClaw** | 增强治理（策略审批、安全审计） | 固定: `ghcr.io/kagent-dev/nemoclaw/sandbox-base:2026.5.4` |

两者共用同一个 OpenShell gRPC 网关，但 NemoClaw 在 VM 内运行额外的治理组件。

### 4.3 配置方式

Controller 启动参数（`--openshell-gateway-url` 为空则禁用 AgentHarness controller）：

```
--openshell-gateway-url=dns:///openshell.openshell.svc:443   # 必填
--openshell-token=xxx                                          # Bearer token
--openshell-token-file=/etc/openshell/token                    # 或从文件读取
--openshell-tls-ca-file=/etc/openshell/ca.pem                  # TLS CA
--openshell-insecure=false                                     # 仅本地开发
--openshell-dial-timeout=10s                                   # 连接超时
--openshell-call-timeout=30s                                   # RPC 超时
```

Helm values：
```yaml
controller:
  env:
    - name: OPENSHELL_GRPC_ADDR
      value: "openshell.my-namespace.svc.cluster.local:8080"
```

---

## 5. 使用 AgentHarness

### 5.1 UI 创建

1. 打开 kagent UI → **Agents** → **New Harness**
2. 目前只有一种类型：**NemoClaw (OpenClaw)**
3. 填写表单：Name / Namespace / Description / Model Config / OpenClaw 设置
4. 提交 → 创建 `AgentHarness` CR

### 5.2 YAML 创建

```yaml
apiVersion: kagent.dev/v1alpha2
kind: AgentHarness
metadata:
  name: my-dev-sandbox
spec:
  backend: openclaw
  description: "Dev sandbox with LLM gateway"
  image: ""                      # 空则用 NemoClaw 默认镜像
  env:
  - name: GITHUB_TOKEN
    valueFrom:
      secretKeyRef:
        name: my-secret
        key: api-key
  network:
    allowedDomains:
    - "api.openai.com"
    - "*.github.com"
  modelConfigRef: default-model-config
  channels:
  - name: my-bot
    type: telegram
    telegram:
      tokenSecret:
        name: telegram-bot-token
        key: token
```

### 5.3 查看状态

```bash
kubectl get agentharness
# NAME             BACKEND    READY   ID                AGE
# my-dev-sandbox   openclaw   True    sandbox-abc123    5m

kubectl get ahr -o yaml my-dev-sandbox   # 短名 ahr
```

### 5.4 SSH 访问

```
UI 点击 SSH → /openshell?sandbox=my-dev-sandbox
  │
  ▼ WebSocket 连接 /api/sandbox/ssh
  │
  ▼ HTTP handler (sandbox_ssh.go)
  ├── WebSocket upgrade
  ├── OpenShell CreateSshSession gRPC
  ├── HTTP CONNECT 隧道到 gateway
  └── SSH session over tunnel → 双向 PTY I/O
  │
  ▼ 浏览器中获得交互式 shell
```

### 5.5 完整生命周期

```
创建 CR
  │
  ├→ Controller 添加 Finalizer "kagent.dev/agent-harness-backend-cleanup"
  ├→ backend.EnsureAgentHarness() → gRPC CreateSandbox
  ├→ 轮询 GetStatus() (10s requeue)
  ├→ Ready 后: OnAgentHarnessReady()
  │     ├── 写入 ~/.openclaw/openclaw.json (LLM 网关配置)
  │     └── 启动 openclaw gateway
  ├→ 标记 annotation: kagent.dev/agent-harness-bootstrap-generation
  └→ Status: Ready=True

删除 CR
  │
  ├→ backend.DeleteAgentHarness() → gRPC DeleteSandbox
  ├→ 移除 Finalizer
  └→ CR 被清理
```

---

## 7. 与 Agent Sandbox 的关系

| 维度 | AgentHarness | [[agent-sandbox|Kubernetes Agent Sandbox]] |
|------|-------------|------------------------------------------|
| **开发者** | kagent 团队 | Kubernetes SIG Apps |
| **CRD** | `AgentHarness` (kagent.dev) | `Sandbox` (agents.x-k8s.io) |
| **后端** | 外部 VM（OpenClaw gRPC） | 集群内 Pod（gVisor/Kata） |
| **工作负载** | 不在集群内 | 集群内 Pod + PVC |
| **安全隔离** | 后端负责 | gVisor/Kata 内核隔离 |
| **生命周期** | 异步轮询（10s requeue） | 声明式（replicas 0/1） |
| **AI Agent 运行时** | 无 | 无（通过 SandboxAgent 有） |
| **预热池** | 无 | WarmPool CRD |

kagent 的 `SandboxAgent` CRD 实际上是将 Agent 的 AgentSpec 嵌入到 agent-sandbox 的 Sandbox 之上——即 **"SandboxAgent = Agent + 隔离沙箱"**。

---

## 8. 实际使用场景（示例）

### 8.1 开发环境

```yaml
# 创建一个可 SSH 的开发环境
apiVersion: kagent.dev/v1alpha2
kind: AgentHarness
metadata:
  name: dev-env-alice
spec:
  backend: openclaw
  image: python:3.12-dev
  env:
  - name: GITHUB_TOKEN
    valueFrom:
      secretKeyRef:
        name: github-token
        key: token
```

### 8.2 带消息集成的运维环境

```yaml
# 通过 Telegram 控制的运维沙箱
apiVersion: kagent.dev/v1alpha2
kind: AgentHarness
metadata:
  name: ops-oncall
spec:
  backend: nemoclaw
  description: "On-call operations environment"
  network:
    allowedDomains:
    - "api.internal.company.com"
  modelConfigRef: ops-llm-config
  channels:
  - name: ops-bot
    type: telegram
    telegram:
      tokenSecret:
        name: telegram-ops-bot
        key: token
```

---

## 9. 关键代码路径

| 文件 | 职责 |
|------|------|
| `go/api/v1alpha2/agentharness_types.go` | CRD 类型定义 |
| `go/api/v1alpha2/sandboxagent_types.go` | SandboxAgent 类型（嵌入 AgentSpec） |
| `go/core/internal/controller/agentharness_controller.go` | AgentHarness 协调循环 |
| `go/core/internal/controller/sandboxagent_controller.go` | SandboxAgent 协调循环 |
| `go/core/pkg/sandboxbackend/` | AsyncBackend 接口定义 |
| `go/core/pkg/sandboxbackend/openshell/` | OpenShell gRPC 客户端实现 |
| `go/core/internal/httpserver/handlers/sandbox_ssh.go` | SSH 代理 HTTP handler |

---

## 关联

- [[kagent]] — kagent 项目实体页
- [[kagent-crd-limitations]] — CRD 能力边界分析
- [[agent-sandbox]] — Kubernetes SIG Apps Agent Sandbox 项目（SandboxAgent 的底层）
- [[kubernetes-crd]] — CRD 技术参考
