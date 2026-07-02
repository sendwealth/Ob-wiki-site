---
title: OpenShell
created: 2026-05-27
updated: 2026-06-28
type: entity
tags: [project, ai, platform, saas, b2b, active]
sources:
  - ~/Projects/OpenShell (源码研究)
  - https://github.com/NVIDIA/OpenShell
  - https://docs.nvidia.com/openshell/latest/
confidence: high
---

# OpenShell

> NVIDIA 开源的 AI Agent 安全沙箱运行时平台。为自主 AI Agent 提供策略强制、凭据隔离、网络边界和身份边界的沙箱化执行环境。Rust 实现，16 crate workspace，~166K LOC。

---

## 核心价值主张

| 维度 | 说明 |
|------|------|
| **安全沙箱** | 多层隔离：Landlock 文件系统 + seccomp + 网络命名空间 + 策略代理 + 进程身份 |
| **策略即代码** | YAML 声明式策略 + OPA (Rego) 动态评估 + Z3 SMT 证明器形式化验证 |
| **多运行时** | Docker / Podman / Kubernetes / libkrun microVM 四种计算后端 |
| **Agent-First** | 项目本身用 Agent 技能驱动开发（`.agents/skills/` 16 个技能），dogfooding |
| **GPU 支持** | 实验性 VFIO 直通 + CDI 设备分配，面向 AI 推理场景 |
| **可观测性** | OCSF v1.7.0 结构化安全日志，7 种事件类型 |

## 整体架构

```
┌─────────────────────── User Interfaces ───────────────────────┐
│  CLI (clap)    │    SDK (Python)    │    TUI (ratatui)        │
└───────────┬──────────────┬─────────────────┬──────────────────┘
            │         gRPC / HTTP            │
            └──────────────┬─────────────────┘
                           ▼
┌──────────────── Control Plane (Gateway) ──────────────────────┐
│                                                                │
│  ┌──────────┐ ┌──────────┐ ┌───────────┐ ┌────────────────┐  │
│  │ API Server│ │Persistence│ │  Policy   │ │Inference Config│  │
│  │ (tonic)  │ │(SQLite/Pg)│ │  Manager  │ │    Router      │  │
│  └──────────┘ └──────────┘ └───────────┘ └────────────────┘  │
│                                                                │
│  Driver Boundaries:                                            │
│  ┌─────────┐ ┌──────────┐ ┌──────────────┐ ┌──────────────┐  │
│  │ Compute │ │Credential│ │  CP Identity │ │Sandbox Ident.│  │
│  │ Driver  │ │  Driver  │ │   Driver     │ │   Driver     │  │
│  └────┬────┘ └──────────┘ └──────────────┘ └──────────────┘  │
│       │ gRPC/UDS                                                │
└───────┼────────────────────────────────────────────────────────┘
        ▼
┌─────── Infrastructure ───────────────────────────────────────┐
│  Docker │ Podman │ Kubernetes │ VM (libkrun)                  │
└───────┬───────────────────────────────────────────────────────┘
        ▼ provisions workload
┌─────── Sandbox Data Plane ───────────────────────────────────┐
│                                                                │
│  ┌────────────┐   spawn    ┌──────────────────────────────┐  │
│  │ Supervisor │───────────▶│  Restricted Agent Process    │  │
│  └─────┬──────┘            └──────────────┬───────────────┘  │
│        │                                  │ all egress        │
│   outbound to GW                          ▼                   │
│   (control, logs, relay)    ┌─────────────────────────────┐  │
│                              │     Policy Proxy (CONNECT)  │  │
│                              └──────┬──────────┬──────────┘  │
│                                     │OPA eval  │inference.local
│                              ┌──────▼──┐  ┌────▼──────────┐  │
│                              │External │  │Inference Router│  │
│                              │Services │  │  (backends)   │  │
│                              └─────────┘  └──────────────┘  │
└────────────────────────────────────────────────────────────────┘
```

## 核心组件

### Gateway (控制平面)

Gateway 是 OpenShell 的认证控制平面，职责：

- **API 服务**：gRPC + HTTP 接口，CLI/SDK/TUI 统一接入
- **持久化**：Protobuf 对象存储，SQLite（默认）/ Postgres 双后端
  - 统一 schema：`id / object_type / name / scope / version / status / payload`
  - SQLite 文件权限 0o600，保护 API 密钥和会话令牌
  - 乐观并发控制（CAS），`expected_resource_version` 防写入冲突
- **策略管理**：策略版本管理、热加载、网关级/sandbox 级作用域
- **凭据管理**：Provider 注册、凭据注入（环境变量/文件/动态轮换）
- **推理路由**：`inference.local` 虚拟端点，将模型请求路由到配置的后端
- **Supervisor Relay**：SSH/TCP 中继，multiplexed over supervisor session
- **PKI Bootstrap**：mTLS 证书、gateway-supervisor 双向认证

### Supervisor (沙箱数据平面)

每个沙箱内运行的本地安全边界：

- **启动流程**：启动 → 连接 Gateway → 认证 → 获取策略/配置 → 应用隔离 → 启动 Agent
- **隔离层**：Landlock 文件系统 + seccomp + 网络命名空间 + 策略代理 + 进程降权
- **热更新**：轮询 Gateway 配置版本，动态加载新策略；加载失败则保持 last-known-good
- **连接模式**：`openshell connect`（SSH/TCP 中继）、`openshell exec`（命令执行，流式输出）
- **日志推送**：OCSF 结构化事件 → Gateway

### Policy Engine (策略引擎)

多层策略强制：

| 层 | 机制 | 时机 |
|---|---|---|
| 文件系统 | Landlock LSM | 启动时（静态） |
| 进程 | 降权用户 + reduced capabilities | 启动时（静态） |
| Seccomp | 阻止 raw socket 等危险 syscall | 启动时（静态） |
| 网络命名空间 | 强制 egress 通过本地 CONNECT 代理 | 启动时（静态） |
| 网络策略 | OPA (Rego) 评估目标/端口/二进制身份/L7 规则 | 运行时（动态热加载） |
| 推理路由 | Gateway inference settings 配置 | 运行时（动态） |

**Prover (openshell-prover)**：Z3 SMT solver 驱动的策略形式化验证器，检查策略一致性和安全性。

### Compute Drivers (计算驱动)

| 运行时 | 适用场景 | 沙箱边界 |
|--------|---------|---------|
| Docker | 本地开发 | Container + nested sandbox namespace |
| Podman | Rootless / 单机 | Container + nested sandbox namespace |
| Kubernetes | 集群部署 (Helm) | Pod + nested sandbox namespace |
| VM (libkrun) | 实验性 microVM 隔离 | 独立 libkrun VM，overlay fs |

统一 `ComputeDriver` trait：`CreateSandbox / GetSandbox / DeleteSandbox / WatchSandboxes / ExecSandbox`

### OCSF Logging (openshell-ocsf)

OCSF v1.7.0 结构化安全事件：

| 事件类型 | Builder | 用途 |
|----------|---------|------|
| 网络活动 | `NetworkActivityBuilder` | TCP 连接、代理隧道、bypass 检测 |
| HTTP 活动 | `HttpActivityBuilder` | L7 请求策略决策 |
| SSH 活动 | `SshActivityBuilder` | 认证、通道操作 |
| 进程活动 | `ProcessActivityBuilder` | 入口点生命周期 |
| 安全发现 | `DetectionFindingBuilder` | Nonce 重放、bypass 检测 |
| 配置变更 | `ConfigStateChangeBuilder` | 策略加载、TLS 设置 |
| 应用生命周期 | `AppLifecycleBuilder` | 沙箱启动/就绪 |

输出格式：Shorthand（可读） + JSONL（机器解析，可外发）。

## 核心概念

| 概念 | 说明 |
|------|------|
| **Gateway** | 认证控制平面，拥有所有持久状态和策略版本 |
| **Supervisor** | 沙箱内本地安全边界，outbound 连接 Gateway |
| **Sandbox** | 一个隔离的 Agent 执行环境，有独立策略/凭据/身份 |
| **Policy** | YAML 声明式安全策略（网络/文件系统/进程/推理），OPA 评估 |
| **Provider** | 凭据提供者（Keychain / Secret Service / Vault / K8s Secrets） |
| **Inference Route** | `inference.local` 虚拟端点 → 模型后端映射 |
| **Relay** | Supervisor-Gateway 双向 SSH/TCP 通道 |

## 数据流：Sandbox 创建到运行

```
1. CLI/SDK → gRPC CreateSandbox → Gateway
2. Gateway → 分配 ID + JWT sandbox token → 选择 Compute Driver
3. Compute Driver → 调用 Docker/K8s/VM API 创建容器/VM
4. 容器/VM 内 → Supervisor 启动
5. Supervisor → outbound 连接 Gateway → mTLS 认证
6. Gateway → 下发策略 + 配置 + 凭据
7. Supervisor → 应用 Landlock + seccomp + 网络命名空间
8. Supervisor → 启动 Policy Proxy (OPA) + Inference Router
9. Supervisor → 以降权用户启动 Agent 子进程
10. Agent 所有 egress → Policy Proxy → OPA 评估 → 允许/拒绝
11. Agent 推理请求 → inference.local → Inference Router → 模型后端
```

## 持久化层

Protobuf 对象存储，统一 schema：

| 列 | 用途 |
|----|------|
| `id` | Gateway 生成的稳定 ID，主键 |
| `object_type` | 资源类型：sandbox / provider / ssh_session / inference_route / sandbox_policy / draft_policy_chunk |
| `name` | 人类可读标识符，type 内唯一 |
| `scope` | global / sandbox 级别 |
| `version` | 乐观锁版本号 |
| `status` | 工作流状态 |
| `labels` | JSON(B) 元数据标签 |
| `payload` | Protobuf 二进制序列 |

## 项目结构

```
OpenShell/
├── crates/                          # Rust workspace (16 crates)
│   ├── openshell-cli/               # CLI 二进制 (clap)
│   ├── openshell-server/            # Gateway 控制平面
│   │   ├── migrations/              # SQLite + Postgres 迁移
│   │   └── src/
│   │       ├── api/                 # gRPC/HTTP handlers
│   │       ├── persistence/         # 对象存储抽象
│   │       └── ...
│   ├── openshell-sandbox/           # Supervisor + Policy Proxy
│   │   ├── data/                    # 嵌入式资源
│   │   └── src/
│   │       ├── proxy/               # CONNECT 代理
│   │       ├── supervisor/          # 监管进程
│   │       └── ...
│   ├── openshell-policy/            # 策略解析 + OPA 引擎
│   ├── openshell-prover/            # Z3 SMT 策略验证器
│   ├── openshell-router/            # 隐私感知推理路由
│   ├── openshell-ocsf/              # OCSF v1.7.0 事件构建器
│   ├── openshell-core/              # 共享类型/配置/错误
│   ├── openshell-providers/         # 凭据提供者后端
│   ├── openshell-bootstrap/         # Gateway 注册元数据
│   ├── openshell-tui/               # ratatui 监控面板
│   ├── openshell-driver-docker/     # Docker 计算驱动
│   ├── openshell-driver-podman/     # Podman 计算驱动
│   ├── openshell-driver-kubernetes/ # Kubernetes 计算驱动
│   ├── openshell-driver-vm/         # libkrun microVM 驱动
│   └── openshell-vfio/              # VFIO GPU 直通
├── python/openshell/                # Python SDK + CLI 打包
├── proto/                           # Protobuf 定义 (22 .proto 文件)
├── deploy/                          # Docker / Helm / K8s / deb / rpm
├── docs/                            # Fern 文档站源码
├── fern/                            # Fern 站点配置/主题
├── architecture/                    # 架构文档 (5 篇)
├── rfc/                             # RFC 设计提案
├── .agents/skills/                  # Agent 技能 (16 个)
├── .github/workflows/               # CI (26 个 workflow)
└── tasks/                           # mise 任务定义
```

## 技术栈

| 类别 | 技术 |
|------|------|
| 语言 | Rust 2024 edition (MSRV 1.88), Python (SDK) |
| 异步运行时 | tokio |
| gRPC | tonic + prost |
| HTTP | axum |
| TLS | rustls (native roots) |
| CLI | clap |
| TUI | ratatui |
| 数据库 | SQLite (rusqlite) + Postgres (tokio-postgres) |
| 策略引擎 | OPA (Rego) + Z3 SMT solver |
| 容器编排 | Docker API / Podman REST / Kubernetes API / libkrun |
| 序列化 | protobuf (prost) + serde |
| 日志/追踪 | tracing + OCSF v1.7.0 |
| 指标 | prometheus (metrics) |
| 构建 | mise task runner, sccache |
| CI | GitHub Actions (26 workflows) |
| 文档 | Fern (mdx) |
| 包管理 | Helm chart, deb, rpm, PyPI, curl installer |
| 代码规模 | 262 Rust 文件, ~166K LOC |

## 构建与测试

```bash
# 开发环境设置
mise run gateway          # 启动独立 Gateway
mise run sandbox          # 创建/重连开发沙箱

# 测试
mise run test             # 单元测试
mise run e2e              # 端到端测试
mise run ci               # 完整本地 CI (lint + 编译 + 测试)

# 提交前
mise run pre-commit       # lint + format + license headers

# 文档
mise run docs             # 本地验证 Fern 文档

# 安装
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
uv tool install -U openshell   # PyPI

# Kubernetes
helm install openshell oci://ghcr.io/nvidia/openshell/helm-chart
```

## 设计权衡

1. **Supervisor-initiated 连接**：Supervisor outbound 连 Gateway，而非 Gateway inbound 到 Sandbox。避免了 NAT/端口映射问题，但要求 Supervisor 能访问 Gateway。
2. **Protobuf 对象存储 vs ORM**：统一 schema + 二进制 payload 换取灵活性，代价是 SQL 层无法直接查询 payload 内字段。
3. **多层隔离 vs 单一沙箱**：Landlock + seccomp + namespace + proxy 叠加防御，任一层被绕过时其他层仍有效，但增加了启动复杂度。
4. **OPA 动态策略 vs 编译时策略**：网络策略可热加载，文件系统/进程策略需要重建沙箱。权衡了灵活性与安全性。
5. **Driver 抽象层**：四种计算后端共享 `ComputeDriver` trait，统一生命周期语义，但每个驱动的平台特性通过 opaque `platform_config` 透传。
6. **SQLite 默认 + Postgres 可选**：降低本地开发门槛（零外部依赖），生产环境可切换到 Postgres。
7. **Agent-First 开发流程**：16 个 Agent 技能驱动 issue triage、spike、build、PR 创建。项目本身就是 agent-driven 工作流的实践。

## 生态系统

| 组件 | 说明 |
|------|------|
| CLI (`openshell`) | 用户管理界面，多 Gateway 注册 |
| Python SDK | `pip install openshell`，绑定 gRPC API |
| TUI | ratatui 实时监控面板 |
| Helm Chart | Kubernetes 集群部署 |
| Docker/Podman | 本地单机部署 |
| Fern Docs | https://docs.nvidia.com/openshell/latest/ |
| Agent Skills | 16 个 `.agents/skills/` 技能 |

## 相关链接

- **GitHub**: https://github.com/NVIDIA/OpenShell
- **文档**: https://docs.nvidia.com/openshell/latest/
- **Roadmap**: https://github.com/orgs/NVIDIA/projects/233
- **License**: Apache-2.0 (NVIDIA CORPORATION)
- **安全报告**: psirt@nvidia.com（不通过 GitHub 报告）

## 最新动态（截至 2026-06-28）

> [!note] 从"沙箱运行时"升级为"NVIDIA Agentic AI 治理栈核心"
> OpenShell 在 GTC 2026 被**打包进 NemoClaw**（OpenShell 治理运行时 + Nemotron 开源模型），COMPUTEX 2026 发布 Ubuntu snap。NVIDIA 把它定位为 agentic AI 的"agent control plane"。

### 2026 关键发布

| 事件 | 内容 |
|------|------|
| **GTC 2026 — NemoClaw** | 开源栈（Apache 2.0）：OpenShell 治理运行时 + Nemotron 开源模型，解决 agentic AI 治理瓶颈 |
| **COMPUTEX 2026 — Ubuntu snap** | 与 Canonical 合作发布 verified OpenShell snap，简化 Ubuntu 部署 |

### 战略升级
- 定位从"AI agent 沙箱"升级为 **"agent control plane / 治理运行时"**
- NemoClaw 把 OpenShell（治理）+ Nemotron（模型）打包，提供端到端 governed agent 栈
- Futurum Group 评价其为"重画 agent control plane 的开放标准"

### 生态信号
- 与 Canonical/Ubuntu 深度合作，瞄准企业 Linux 部署
- 与 [[kagent]]（CNCF K8s agent 框架）形成"治理 + 编排"互补
- Reddit 社区讨论热烈，但 CES demo 有零星连接性问题反馈

### 仍待观察
- NemoClaw 栈的实际采用度（governance 叙事 vs 落地）
- 与 [[agent-sandbox]]（K8s SIG Apps）的竞合关系

---

关联 [[kagent]]（Kubernetes Agent 框架，使用 OpenShell AgentHarness）、[[agent-sandbox]]（K8s SIG Apps 沙箱基础设施，互补层）、[[a2a-protocol]]（Agent 间通信协议）、[[kubernetes-crd]]（CRD 设计模式）、[[agentic-rag]]（Agent 增强检索）、[[context-mode]]（开发工具）、[[temporal]]（分布式编排参考架构）
