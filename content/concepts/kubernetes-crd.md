---
title: Kubernetes CRD (Custom Resource Definition)
created: 2026-05-26
updated: 2026-05-26
type: concept
tags: [ai, kubernetes, infrastructure, platform]
sources:
  - https://kubernetes.io/docs/concepts/extend-kubernetes/api-extension/custom-resources/
  - https://kubernetes.io/docs/tasks/extend-kubernetes/custom-resources/custom-resource-definitions/
  - https://book.kubebuilder.io/cronjob-tutorial/gvks
confidence: high
---

# Kubernetes CRD (Custom Resource Definition)

> CRD 是 Kubernetes 的核心扩展机制，允许用户在不修改 K8s 源码的情况下定义新的 API 资源类型。CRD + Controller = Operator Pattern，是声明式 API 的基石。kagent 的 Agent CRD、Agent Sandbox 的 Sandbox CRD 都是基于这个机制构建的。

---

## 1. 核心概念

### 1.1 什么是 CRD

**Custom Resource Definition (CRD)** 是 K8s 内置的 API 资源，用于声明式地定义新的自定义资源类型。

```
CRD (定义)  →  CR (实例)  →  Controller (协调)
```

- **CRD**: 告诉 API Server "有一种新的资源叫 XXX，它的 schema 是这样的"
- **Custom Resource (CR)**: 用户按照 CRD 定义的 schema 创建的具体实例
- **Controller**: Watch CR 变化，协调实际状态趋向期望状态

### 1.2 Resource vs Custom Resource

| 概念 | 说明 | 例子 |
|------|------|------|
| **Resource** | K8s 内置 API 端点 | Pods, Deployments, Services |
| **Custom Resource** | 用户扩展的 API 端点 | Agents (kagent), Sandboxes (agent-sandbox), CronTabs |

自定义资源创建后，用户可以像操作内置资源一样用 `kubectl` 管理。

### 1.3 Group / Version / Kind / Resource (GVK/GVR)

```
GVK = Group + Version + Kind
GVR = Group + Version + Resource (小写复数)

例: kagent Agent CRD
  Group:   kagent.dev
  Version: v1alpha2
  Kind:    Agent
  Resource: agents

REST API: /apis/kagent.dev/v1alpha2/namespaces/{ns}/agents/{name}
```

- **Group**: API 组（域名形式），如 `apps`, `batch`, `kagent.dev`
- **Version**: API 版本，如 `v1`, `v1alpha1`, `v1beta1`
- **Kind**: 类型名（CamelCase），如 `Deployment`, `Agent`
- **Resource**: REST 路径名（小写复数），如 `deployments`, `agents`

---

## 2. CRD 定义结构

### 2.1 完整示例

```yaml
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  # name = <plural>.<group>
  name: crontabs.stable.example.com
spec:
  # REST API 路径: /apis/<group>/<version>
  group: stable.example.com

  # 作用域: Namespaced（命名空间级）或 Cluster（集群级）
  scope: Namespaced

  # 资源名称定义
  names:
    plural: crontabs           # REST 路径
    singular: crontab          # CLI 别名
    kind: CronTab              # YAML 中使用
    shortNames: [ct]           # kubectl get ct

  # 多版本支持
  versions:
    - name: v1
      served: true             # 是否通过 API 暴露
      storage: true            # etcd 存储版本（只能有一个）
      schema:
        openAPIV3Schema:       # OpenAPI v3 验证
          type: object
          properties:
            spec:
              type: object
              properties:
                cronSpec:
                  type: string
                  pattern: "^\\S+$"
                image:
                  type: string
                replicas:
                  type: integer
                  minimum: 1
                  maximum: 10
      additionalPrinterColumns:   # kubectl get 显示列
        - name: Spec
          type: string
          jsonPath: .spec.cronSpec
        - name: Replicas
          type: integer
          jsonPath: .spec.replicas
        - name: Age
          type: date
          jsonPath: .metadata.creationTimestamp
      selectableFields:           # 字段选择器 (v1.32+)
        - jsonPath: .spec.image
      subresources:
        status: {}                 # 启用 /status 子资源
        scale:                     # 启用 /scale 子资源
          specReplicasPath: .spec.replicas
          statusReplicasPath: .status.replicas
```

### 2.2 CRD Spec 关键字段

| 字段 | 说明 |
|------|------|
| `spec.group` | API 组名（DNS 子域名格式） |
| `spec.scope` | `Namespaced` 或 `Cluster` |
| `spec.names` | plural/singular/kind/shortNames |
| `spec.versions[]` | 版本列表（可多版本共存） |
| `spec.versions[].served` | 是否对外暴露 |
| `spec.versions[].storage` | etcd 存储版本（唯一） |
| `spec.versions[].schema` | OpenAPI v3 验证 schema |
| `spec.versions[].subresources` | status / scale 子资源 |
| `spec.versions[].additionalPrinterColumns` | kubectl 显示列 |
| `spec.versions[].selectableFields` | 字段选择器 (v1.32+) |

---

## 3. 验证机制

### 3.1 OpenAPI v3 Schema

CRD 使用 OpenAPI v3.0 定义字段验证规则:

```yaml
schema:
  openAPIV3Schema:
    type: object
    properties:
      spec:
        type: object
        required: ["image"]          # 必填字段
        properties:
          image:
            type: string
            minLength: 1
          replicas:
            type: integer
            minimum: 1
            maximum: 100
          type:
            type: string
            enum: ["Declarative", "BYO"]  # 枚举
          resources:
            type: object
            properties:
              cpu:
                type: string
                pattern: "^[0-9]+m?$"
              memory:
                type: string
                pattern: "^[0-9]+(Ki|Mi|Gi)$"
```

### 3.2 CEL 验证规则 (x-kubernetes-validations)

使用 Common Expression Language 进行跨字段验证:

```yaml
# kagent agent_types.go 中的例子
properties:
  type:
    type: string
    enum: ["Declarative", "BYO"]
x-kubernetes-validations:
  - rule: "self.type == 'Declarative' ? has(self.declarative) : true"
    message: "declarative must be specified if type is Declarative"
  - rule: "self.type == 'BYO' ? has(self.byo) : true"
    message: "byo must be specified if type is BYO"
```

### 3.3 Validation Ratcheting (v1.33 stable)

允许在**不改变无效部分**的情况下更新资源——已有的无效字段不会被新验证规则拒绝。这让 CRD 作者可以安全地添加新验证，而不必强制所有现有资源立即修复。

### 3.4 限制

以下 OpenAPI 特性在 CRD 中**不支持**:
- `definitions`, `dependencies`, `deprecated`, `discriminator`
- `uniqueItems: true`
- `additionalProperties: false`
- `$ref`（不能引用外部定义）

---

## 4. 高级特性

### 4.1 Finalizer（终结器）

阻止资源删除直到清理完成:

```yaml
metadata:
  finalizers:
    - kagent.dev/cleanup
```

Controller 在删除资源前先执行清理（如删除关联 Deployment、Service），清理完成后移除 finalizer，K8s 才真正删除资源。

### 4.2 Status 子资源

分离 spec（期望状态）和 status（观测状态），实现:
- 细粒度 RBAC（用户可写 spec，但只有 controller 可写 status）
- `kubectl get` 不显示 status（除非 `-o yaml`）
- Generation / ObservedGeneration 追踪

### 4.3 多版本与 Conversion Webhook

CRD 可以同时暴露多个 API 版本，通过 Conversion Webhook 在版本间转换:

```
客户端请求 v1  ←→  Conversion Webhook  ←→  etcd 存储 v1beta1
客户端请求 v2  ←→  Conversion Webhook  ←→  etcd 存储 v1beta1
```

kagent 的版本策略: v1alpha1 (legacy) → v1alpha2 (current)

### 4.4 AdditionalPrinterColumns

自定义 `kubectl get` 输出:

```yaml
additionalPrinterColumns:
  - name: Provider
    type: string
    jsonPath: .spec.provider
  - name: Model
    type: string
    jsonPath: .spec.model
  - name: Age
    type: date
    jsonPath: .metadata.creationTimestamp
```

输出:
```
NAME             PROVIDER   MODEL        AGE
my-model-config  OpenAI     gpt-4o       5d
```

### 4.5 Field Selectors (v1.32+)

```yaml
selectableFields:
  - jsonPath: .spec.color
  - jsonPath: .spec.size
```

允许 `kubectl get shirts --field-selector spec.color=red`

### 4.6 Scale 子资源

让 HPA 可以自动扩缩容自定义资源:

```yaml
subresources:
  scale:
    specReplicasPath: .spec.replicas
    statusReplicasPath: .status.replicas
```

---

## 5. CRD vs ConfigMap vs Aggregated API

### 5.1 何时用 CRD vs ConfigMap

**用 ConfigMap**: 简单配置，不需要结构化验证，不需要 controller
**用 CRD**: 需要结构化 schema、kubectl 原生支持、controller 协调、RBAC 控制

**具体判断** — 如果以下大多数成立，用 CRD:
- 需要 kubectl 原生支持（`kubectl get my-resource`）
- 需要 Watch + 自动化响应变化
- 需要 `.spec` / `.status` / `.metadata` 惯例
- 需要结构化验证（OpenAPI schema）
- 资源是受控资源的抽象或聚合

### 5.2 CRD vs Aggregated API Server

| 特性 | CRD | Aggregated API |
|------|-----|---------------|
| 实现复杂度 | 低（声明 YAML） | 高（自建 API Server） |
| 验证 | OpenAPI v3 + CEL + Webhook | 任意验证 |
| 默认值 | OpenAPI default + Webhook | 任意默认 |
| 存储定制 | etcd 固定格式 | 自定义存储层 |
| 协议 | 标准 REST | 自定义协议 |
| 版本转换 | Conversion Webhook | 任意逻辑 |
| 适用场景 | 90% 的扩展需求 | 复杂/特殊需求 |

---

## 6. Operator Pattern

CRD + Controller = Operator。将领域知识编码为 K8s 扩展:

```
┌─────────────┐     Watch      ┌──────────────┐
│   API Server │ ─────────────→ │  Controller   │
│  (etcd + CR) │ ←──── Reconcile ── │  (自定义逻辑)  │
└─────────────┘                 └──────────────┘
       ↑                               │
       │ Create/Update/Delete           │
       │ K8s 原生资源                    ▼
       │                        ┌──────────────┐
       └────────────────────────│ Deployments  │
                                │ Services     │
                                │ ConfigMaps   │
                                │ Pods...      │
                                └──────────────┘
```

**Reconcile Loop**: Controller 不断比较期望状态（spec）和实际状态，通过创建/更新/删除 K8s 资源来消除差距。

### 实际项目中的 Operator

| 项目 | CRD 数量 | 说明 |
|------|---------|------|
| **kagent** | 8+ | Agent, ModelConfig, ToolServer, AgentHarness, SandboxAgent, Memory... |
| **Agent Sandbox** | 4 | Sandbox, SandboxTemplate, SandboxClaim, SandboxWarmPool |
| **Orloj** | 8 | AgentDefinition, AgentInstance, ToolRegistration, ApprovalPolicy... |
| **Cert Manager** | 4 | Certificate, Issuer, ClusterIssuer, CertificateRequest |
| **Argo Rollouts** | 2+ | Rollout, AnalysisTemplate, Experiment |

---

## 7. 开发工具链

### 7.1 Kubebuilder

最流行的 CRD + Controller 脚手架工具:

```bash
# 初始化项目
kubebuilder init --domain kagent.dev --repo github.com/kagent-dev/kagent

# 创建 API (CRD + Controller)
kubebuilder create api --group kagent --version v1alpha2 --kind Agent

# 生成 CRD YAML
make manifests

# 运行本地
make run
```

### 7.2 Controller Runtime

Kubebuilder 底层库，提供:
- Watch / Event 过滤
- Reconcile 接口
- Owner Reference（资源生命周期绑定）
- Event 记录（`kubectl describe` 中显示 Events）

### 7.3 代码生成

```bash
# DeepCopy 方法（Go 结构体深拷贝）
make generate

# CRD YAML（从 Go struct 标注生成）
make manifests

# 客户端代码（typed client/informer/lister）
make generate-go
```

### 7.4 Kubebuilder Markers (Go 注解)

```go
// +kubebuilder:object:root=true          // 生成 CRD 根类型
// +kubebuilder:subresource:status         // 启用 status 子资源
// +kubebuilder:printcolumn:name="Provider",type=string,JSONPath=".spec.provider"
// +kubebuilder:resource:categories=kagent,shortName=ag
// +kubebuilder:validation:Enum=OpenAI;Anthropic;Gemini
// +kubebuilder:default="python"
// +kubebuilder:validation:Minimum=1
// +kubebuilder:validation:Maximum=100
// +kubebuilder:optional
type AgentSpec struct {
    Type AgentType `json:"type"`
    // ...
}
```

---

## 8. CRD 设计最佳实践

### 8.1 API 设计

- **小 API**: 一个 CRD 做一件事，不要塞太多字段
- **分层**: 基础 CRD（如 Sandbox）+ 扩展 CRD（如 SandboxTemplate/SandboxClaim）
- **不可变 spec**: spec 一旦创建不应改变语义；需要改变时用新版本
- **status 反映真实**: status 由 controller 写入，反映实际观测状态

### 8.2 版本管理

- Alpha (v1alpha1): 可破坏性变更
- Beta (v1beta1): 尽量向后兼容
- Stable (v1): 严格向后兼容
- 同一时间只有一个 `storage: true` 版本

### 8.3 安全

- 默认最小权限（AutomountServiceAccountToken: false）
- RBAC 明确授权（不要用 cluster-admin）
- Finalizer 确保清理
- Webhook 验证输入边界

---

## 关联

- [[kagent]] — kagent 使用 8+ CRD 定义 Agent 生态系统
- [[kagent-crd-limitations]] — CRD 抽象能力的边界分析
- [[agent-sandbox]] — Agent Sandbox 的 4 个 CRD（Sandbox/Template/Claim/WarmPool）
- [[orloj]] — Orloj 的 8 CRD + 治理审批系统
- [[kubernetes-agent-platforms]] — 各 K8s Agent 平台的 CRD 设计对比
