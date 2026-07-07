---
title: OpenGeni
created: 2026-07-02
updated: 2026-07-02
type: entity
tags: [product, project, platform, saas, b2b, ai, active, mvp]
sources:
  - https://github.com/Cloudgeni-ai/opengeni
  - https://opengeni.ai
  - https://github.com/Cloudgeni-ai/opengeni/blob/main/docs/architecture.md
  - https://github.com/Cloudgeni-ai/infrastructure-agents-guide
confidence: high
---

# OpenGeni

> OpenGeni 是 **Cloudgeni-ai** 出品的**自托管式"托管 Agent 服务"（self-hostable managed agent service）**——官方定位 "The open agent runtime. Embed it. Self-host it. Own it."。它跑 **OpenAI Agents SDK** 的 Agent，但真正拥有的是 Agent **周围**的生产级基础设施：会话生命周期、可重放事件历史、人在环审批、长时目标、沙箱、多租户、计量计费。技术上它是一个 **Bun monorepo**（Hono API + Temporal 编排 + OpenAI Agents SDK worker + Postgres/pgvector + NATS 实时总线 + MinIO/S3/Azure/GCS 对象存储），并附带一个独立的 **Rust 工作空间**（Connected Machine agent + 流中继）。一句话：**给 OpenAI Agents SDK 套了一层 Temporal + Postgres + NATS 的持久化、可观测、多租户运行时**，且把"在你自己的机器上跑 Agent"做成了与云沙箱**完全对等的一等公民计算目标**。

---

## 一句话定位

> **durable + recoverable + streamable + multi-tenant + sandbox-agnostic** 的 Agent 执行运行时，可自托管。

它是 **substrate（基底），不是 Agent 本身**。你带目标和 workspace 来，OpenGeni 给你 session API、exactly-once 实时流、可恢复的长跑 run、双计算模型、多租户安全边界、定时任务和计量计费。

与刚研究的 [[polos]] 同属"AI Agent 持久化执行运行时"赛道，但 OpenGeni **工程成熟度和架构完备度明显更高**——它直接复用生产级 [[temporal]] 做编排，而不是像 Polos 那样自研 Rust orchestrator；并把"Agent 跑在你自己机器上"做成了核心差异化卖点。

---

## 解决的核心痛点

针对**运维/产品团队**，想跑长时、有副作用（side-effectful）的 Agent——基础设施工作、改代码、跨天自治任务——但不想自己造持久化、恢复、流式、多租户、沙箱这套管道。

1. **Agent 跑着跑着挂了**——OpenGeni 让 run 存活于 worker 死亡和供应商抖动，**按设计无运行时长上限**
2. **实时观测与重放**——SSE 锚定每会话单调 `sequence`，支持重连/重放/补缺（gap backfill）
3. **危险操作要审批**——人在环（HITL）审批是一等公民
4. **多租户隔离**——workspace 为访问边界，Postgres **行级安全（RLS）**强制
5. **数据主权**——自带模型/密钥/推理路由；甚至可把 Agent 跑在**你自己的机器**上，不向它投递任何 OpenGeni 凭证
6. **要能当库嵌入产品，也能跨 AWS/Azure/GCP 当企业服务部署**

---

## 整体架构

"公共客户端只跟 Hono API 说话，其余全是内部机械。"

```
┌──────────────────────────────────────────────────────────────────┐
│                      OpenGeni 架构                                │
└──────────────────────────────────────────────────────────────────┘

  公共客户端
 ┌────────┐ ┌─────────┐ ┌─────────┐ ┌──────────┐
 │ React  │ │External │ │Webhook  │ │Custom UI │   只发 HTTP/SSE
 │ Web    │ │Service  │ │Caller   │ │/ SDK     │ ◀──────────────▶
 └───┬────┘ └────┬────┘ └────┬────┘ └─────┬────┘
     └───────────┴───────────┴────────────┘
                       │  Hono API（公共契约）
                       ▼
 ┌─────────────────────────────────────────────────────────────┐
 │                  托管 Agent 服务（自托管部署）              │
 │                                                             │
 │  ┌──────────┐   ┌──────────────────────────────────────┐   │
 │  │ Temporal │   │  Postgres ← 持久真相源                │   │
 │  │ 编排+信号│   │  sessions/events/history_items/run   │   │
 │  │          │   │  + pgvector（文档语义检索）           │   │
 │  └────┬─────┘   └──────────────────────────────────────┘   │
 │       │ 活动分发         ▲ 写持久，再 best-effort 发 NATS  │
 │       ▼                  │                                  │
 │  ┌──────────┐       ┌────┴─────────┐                       │
 │  │ Worker   │◀─────▶│  NATS Core   │  实时扇出总线         │
 │  │ OpenAI   │  发布  │ （只广播，   │  （Missed 事件按      │
 │  │ Agents   │       │   不持久）   │   sequence 回补）     │
 │  │ SDK 载具 │       └──────────────┘                       │
 │  └──┬───┬──┘                                              │
 │     │   │   ┌─────────────────┐                           │
 │     │   └──▶│ NATS 控制面     │◀── . 拨出 . ──┐            │
 │     │       │ (machine RPC)  │              │            │
 │     │       └─────────────────┘              ▼            │
 │     │                              ┌──────────────────┐    │
 │     │                              │ Connected Machine│    │
 │     │       ┌─────────────────┐    │ （你登记的机器） │    │
 │     └──────▶│  Stream Relay   │◀── . 拨出 . ──┘    │
 │             │  pty/desktop帧  │   (Rust: opengeni-relay)   │
 │             └─────────────────┘                            │
 │                                                             │
 │  ┌──────────────────────────────┐                           │
 │  │ Managed Sandbox              │                           │
 │  │ Docker / Modal / 本地 / 云 / none │                      │
 │  └──────────────────────────────┘                           │
 └─────────────────────────────────────────────────────────────┘
```

**七大内部组件：**

| 组件 | 技术 | 角色 |
|------|------|------|
| **API** | Hono（Bun） | 公共契约：验请求、建会话、收消息/控制事件、吐持久历史、流实时事件 |
| **DB** | Postgres + Drizzle + pgvector | 持久真相源：sessions/events/history_items/run state，文档语义检索 |
| **Temporal** | Temporal | 编排与信号（follow-up/approval/interrupt），**token 流与工具输出绝不进 workflow history** |
| **Worker** | OpenAI Agents SDK | 真正跑 Agent 的载具（harness） |
| **NATS Core** | NATS | 仅实时扇出总线（"Postgres 记忆，NATS 广播"） |
| **Control** | NATS 控制面 | Connected Machine 的 exec/RPC 通道 |
| **Relay** | Rust（`opengeni-relay`） | 无状态流中继，转发 pty/desktop 帧 |

---

## 核心设计不变式（Load-bearing invariants）

这是 OpenGeni 最有价值的设计沉淀——架构文档显式列出**承载正确性的硬规则**，违反它们往往是微妙的安全/正确性 bug，而非编译错误。这种"把不变式当一等公民"的工程文化值得学习（与 [[temporal]] 文档风格一脉相承）。

### 3.1 Postgres 是持久真相源，NATS 只做实时扇出

- **写持久，再 best-effort 发 NATS**——`appendAndPublishEvents` 先写 DB（真相源）再尽力发 NATS；**绝不无前置持久追加就发；绝不颠倒顺序**
- **NATS 抖动绝不杀在途 turn**——消费者从持久 log 协调错过的实时事件
- **缺事件按 `sequence` 从 Postgres 回补**——SSE 流重放持久事件、订阅实时、遇 sequence 缺口**从 DB 回补并按 sequence 去重**；流核心"宁可抛错也不带缺口交付"
- **读绝不搭总线**——文件/终端读走客户端→API→盒子进程内；只有副作用通知（`fs.changed`/`git.changed`）才追加+发布

### 3.2 Temporal 编排；token 流绝不进 workflow 历史

- Temporal 只跑长时会话 workflow 和信号——**仅编排**。token 流与工具输出**绝不进 workflow history**
- 会话 workflow **内存里不持 goal 状态**——只通过 activity 读写 `session_goals`，循环天然 replay-safe

### 3.3 Agent turn 跑成**不可重试 activity**——修幂等，别瞎重试

- 每个 turn 是一个 `maximumAttempts: 1` 的 activity——**无自动 activity 重试**（模型/沙箱/GitHub/云调用都有副作用）
- **不要给整个 agent turn 加自动 Temporal 重试**，除非每个模型/工具/沙箱边界都已幂等
- 恢复是**显式**的：优雅关停检查点+重新入队（状态 `preempted`）；非优雅死亡用**类型化**心跳/schedule-to-start 超时检测，经 `requeueTurnAfterWorkerDeath` 重派，**每 turn 重派上限 3**
- worker 死亡检测**必须用类型化 SDK 失败类**（`instanceof ActivityFailure`），绝不用消息字符串匹配

### 3.4 按设计无运行时长上限——用症状而非计数/时钟约束

- run 合理跨天。**运行时长用症状约束**（无进展检测、预算耗尽），从不用计数或时钟
- **不要"求稳"而加/降**模型调用/续轮/activity 超时上限——修病理本身
- 可恢复条件**让会话 idle**（保留上下文）而非失败；失败会话可被新 `user.message` 复活（`failed → queued` 重启 workflow，`signalWithStart`），只有 `cancelled` 是终态

### 3.5 三种内存存储，三种职责

| 存储 | 职责 | 规则 |
|------|------|------|
| `session_history_items` | **喂模型的对话真相**（默认读路径） | 未脱敏、replay-ready；压缩**取代不删除**（`active=false`），摘要插在分数位置 `boundary - 0.5` |
| `agent_run_states` | **仅审批恢复**——暂停待审时序列化的 SDK `RunState` blob | 绝不当对话记忆 |
| `session_events` | **脱敏的人类/审计时间线**——驱动重放/SSE/UI | 脱敏且有损，**绝不喂回模型**，每会话单调 `sequence` |

（沙箱恢复状态又是独立存储：`sandbox_session_envelopes`）

### 3.6 Workspace 是访问边界 + 三种访问模式

- **workspace 是访问边界，不是资源 id**——每个 workspace 路由必须先 `requireAccessGrant()` 再碰数据；跨 workspace 返回 `null → 404`
- **所有 workspace 表强制 RLS**——以非超级用户 `opengeni_app` 角色连接，**必须**在 RLS 上下文包装器内读写
- **三种产品访问模式**：`local`（自举）、`configured`（委派 HMAC/bearer）、`managed`（better-auth + Stripe）
- **两个不同 auth 头**：部署共享键用 `x-opengeni-access-key`；产品 API 键/委派 token 用 `Authorization: Bearer`——别混
- **权限粒度不可塌缩**：`stream:view` 严格宽于 `sessions:read`（像素平面未脱敏），`files:write ≠ files:read`，`terminal:attach ≠ sessions:read`

### 3.7 contracts 包是 wire 类型的真相源

- `packages/contracts/src/index.ts` 是**所有**跨边界枚举/zod schema/每后端能力表/端口常量/HMAC token 信封的唯一真相源
- SDK 手工镜像这些类型（零运行时依赖），有**契约对等测试**钉住；`SandboxBackend` 成员**只许末尾追加**且跨 contracts/sdk/deployment 三处一致

---

## 双计算模型（核心差异化）

OpenGeni 最独特的卖点：**两种计算目标完全对等，都是一等公民 PRIMARY**。

### A. Managed Sandbox（托管沙箱）
OpenGeni 供给并拆除的新鲜云盒子。后端可切：**Docker / Modal / 本地 / 云供应商 / none**。
- 会话级注入短期、run 级 GitHub App token
- 仓库可 clone 进沙箱

### B. Connected Machine（连接机/自带机）⭐
你登记的、自己的机器（笔记本、构建服务器、GPU 盒子）。**machine-targeted turn 直接在你的硬件上跑**——**不创建云盒、不计费、不向它投递任何 OpenGeni 凭证**。

| 维度 | Managed Sandbox | **Connected Machine** |
|------|----------------|----------------------|
| 运行位置 | OpenGeni 供给的云盒 | **你的机器，直接跑** |
| git 认证 | 注入短期 GitHub App token | **用机器自己的 git 凭证**（token mint 被跳过） |
| 文件 | clone 选定仓库 | **不 clone，机器已有自己的文件系统** |
| 工作目录 | 无需选 | **每会话指定工作文件夹**（机器根或子目录，作为 agent 的 cwd 基） |
| 网络 | 云盒需可达 | **agent 向外拨**（dial-out），机器无需任何入站暴露 |
| 计费 | 按云盒 | **该 turn 不创建云盒、不计费** |

**Enroll 流程**（连接一台机器）：
1. workspace **Machines** 面板点 "Enroll a machine"，打印一行 install 命令在你机器上跑（拉取 agent 二进制并启动）
2. 审批机器，两条路：
   - **Device flow（同意）**：agent 打印短码 + 验证链接，你打开点 "Grant" 批准该具体机器（大声、显式同意，记录批准人）
   - **零点击 enroll token**：预先 mint 短期 token，agent 无头兑换（token 即授权，无需逐机点击）——适合脚本/批量登记
3. 机器出现在面板，显示状态/OS/架构/是否提供屏幕；可随时撤销；**屏幕控制是独立的、审批时单独 opt-in**

**运维开关**（默认**关闭**）：`OPENGENI_SANDBOX_SELFHOSTED_ENABLED=true` 才激活；关闭时所有 enroll/machine 路由返回 `404`，surface 对该部署不存在。

### Connected Machine 的 Rust agent（独立 Cargo 工作空间）

这是整个项目里技术含量最高的部分——一个**独立 Rust 工作空间**（不在 bun monorepo 内，`agent/target/` 被 gitignore）：

| Crate | 职责 |
|-------|------|
| `opengeni-agent-proto` | 生成的 wire 协议类型（Rust 侧，由 proto codegen） |
| `opengeni-agent` | 二进制：`run`/`enroll`/`service`/`update`/`uninstall`；拨号、RPC 分发、监督 |
| `opengeni-agent-platform` | 每 OS 的 `Platform` + `service` 渲染器（systemd/launchd/SCM） |
| `opengeni-agent-stream` | Relay 边流传输 + pty/framebuffer 泵 |
| `opengeni-agent-update` | 自更新：签名 manifest 发现、minisign+sha256 验证、原子替换、回滚 |
| `opengeni-relay` | 无状态流中继边镜像 |

**wire 协议单真相源**：proto3 定义在 `proto/opengeni_agent.proto`，**一次定义、双栈 codegen**——Rust 侧 `prost`+`protox`（纯 Rust protobuf 编译器，**无需 protoc 二进制**，cargo 构建完全 hermetic，含 NixOS），TS 侧 `ts-proto` 生成 `@opengeni/agent-proto`。`agent/scripts/codegen.sh` 一条命令重生双栈。**控制面（TS）与 agent（Rust）永不漂移**。

**分发 + 自更新**：一行 install 脚本（POSIX `sh` for Linux/macOS，`.ps1` for Windows），检测 os/arch→解析 GitHub Release 资产→**双重验证**（脚本体内 pin 的 minisign 公钥签名 + sha256）→装到 per-user 路径→打印 enroll 命令。`opengeni-agent update` 拉签名 channel manifest、验证 minisign+sha256+版本单调性、**原子自替换**（含 Windows rename-self-aside）、启动健康门失败则**回滚**到旧二进制。篡改工件永远被拒。

可与 [[openshell]]（NVIDIA 的 Landlock+seccomp+namespace+OPA 沙箱）、[[agent-sandbox]]（K8s SIG Sandbox CRD）对照——OpenGeni 的"自带机"路线完全不同，它不隔离，而是**让 Agent 直接合法地跑在你的真实环境里**，靠"不投递凭证 + dial-out + 显式审批"建立信任。

---

## Monorepo 结构

Bun workspaces（`apps/*` + `packages/*`）+ 独立 Rust workspace（`agent/`）。

```
opengeni/
├── apps/
│   ├── api/      @opengeni/api-router   Hono HTTP 面（createApp、路由、MCP HTTP 传输）
│   ├── worker/   @opengeni/worker-bundle Worker 入口（runOpenGeniWorker + un-bundle）
│   └── web/      opengeni-web            React + Vite 前端
├── packages/
│   ├── contracts/   @opengeni/contracts    共享 zod schema + wire 类型（真相源）
│   ├── db/          @opengeni/db           Drizzle schema、RLS 查询层、迁移、角色 provision
│   ├── core/        @opengeni/core         框架无关核心：domain/access/billing
│   ├── sdk/         @opengeni/sdk          类型化客户端、会话生命周期、SSE 流（零运行时依赖）
│   ├── events/      @opengeni/events       事件追加+发布
│   ├── config/      @opengeni/config       运行时配置解析/校验
│   ├── deployment/  @opengeni/deployment   部署契约（Helm/Terraform/preflight）
│   ├── react/       @opengeni/react        React hooks + 样式组件（直播、composer、机器面板）
│   └── agent-proto/ @opengeni/agent-proto  ts-proto 生成的 wire 类型
├── agent/           独立 Rust Cargo workspace（见上）
├── deploy/
│   ├── helm/opengeni/         Helm chart（API/web/worker/migrations/烟雾夹具）
│   └── terraform/{azure,aws,gcp}/  云参考 substrate
├── docs/            architecture.md / run-lifecycle.md / capabilities.md / packs.md ...
└── scripts/         dev-stack.sh / deployment-preflight.ts / codegen.sh ...
```

**客户端闭包（embeddable、server-free）**：`contracts → sdk → react`，可被嵌入任意产品。

---

## 关键能力

### 会话 API（Session-based）
创建/列出/取/重命名会话；发消息；控制事件（approve/interrupt）；读持久历史。**Sessions 是持久的**——刷新浏览器或之后打开会话 URL，从 Postgres 重放事件历史并重连实时事件。

### Exactly-once 实时流
SSE 锚定每会话单调 `sequence`，支持重连/重放/缺口回补（见不变式 3.1）。

### 持久、可恢复的 run
run 存活于 worker 死亡与供应商抖动，**按设计无运行时长上限**（见不变式 3.3、3.4）。

### 人在环审批
中断、批准、拒绝工具请求；long-running goals。

### 能力目录（Capability Catalog）
workspace 级统一目录，合并：内置 packs/APIs/MCP/捆绑技能 + `OPENGENI_MCP_SERVERS` 配置的 MCP + 本地目录项 + **官方 MCP Registry 发现的公共远程 MCP**。启用远程 MCP 先做 `initialize/list-tools` 探针，成功才存 `capability_installations`；失败返回 `422` 保持禁用——**故陈旧/宕机/纯 auth 端点永不破坏运行时 agent turn**。凭据头 AES-256-GCM 加密存储，API 永不回传值。

### Capability Packs（角色导向包）
角色导向 bundle，展开为既有运行时原语（MCP 工具选择 + 捆绑技能 + 连接器需求 + 文档知识 + 定时任务模板 + 元数据）。首个 pack：`marketing-social-daily-analysis`（社交账号 + 营销知识库 + 每日定时分析）。Pack 可声明 `sandboxImage`（digest-pinned 容器镜像）和 `skills`（inline SKILL.md + 文件），参与 pack-scoped 运行时组合。

### GitHub App 集成
推荐方式给 agent 范围化的仓库访问——UI 列已装仓库，worker 仅为会话选定仓库 mint 短期 installation token。通过 manifest 流程一键建 App。

### 文档上传 + 语义检索
上传/索引/重试 + pgvector 语义搜索。

### 定时、循环工作
cron 式定时任务，唤醒会话并无人值守跑一轮。

### 使用计量与权益
每模型调用用量计账，支持静态或托管（Stripe）计费。三种产品访问模式见不变式 3.6。

---

## 技术栈

| 层 | 选型 |
|----|------|
| 运行时 | **Bun**（workspace） |
| API | **Hono** |
| Web | **React + Vite** |
| 编排 | **Temporal**（直接复用，非自研） |
| 持久化 | **Postgres + Drizzle + pgvector**（强制 RLS） |
| 实时 | **NATS Core**（仅扇出） |
| 对象存储 | 本地 MinIO；生产 **Azure Blob / AWS S3 / GCS** |
| Agent SDK | **OpenAI Agents SDK** |
| 模型 | OpenAI / Azure OpenAI / Anthropic / Bedrock / 自托管（bring-your-own） |
| Connected Machine | **Rust**（独立 Cargo workspace） |
| 部署 | **Helm chart** + **Azure/AWS/GCP 参考 Terraform** + preflight/profile 命令 |

**关键集成选择：直接用 Temporal 做编排**——这是与 [[polos]]（自研 Rust orchestrator）的根本路线分歧。OpenGeni 借力成熟生产系统，把精力投在 Agent 特性层。

---

## 部署

- **`bun run dev`** 一键起全栈（装依赖、建 `.env`、起 Docker 基础设施、跑迁移、建本地沙箱镜像、起 API/worker/web）
- 手动分进程模式可分终端跑各长时进程
- 生产：**Helm chart**（API/web/worker/migrations + 一次性本地/烟雾夹具）+ **Azure/AWS/GCP 参考 Terraform substrate** + stack-wrapper plan 装官方上游 NATS/Temporal Helm chart
- `bun run deployment:profiles` / `preflight --profile <name>` / `stack --profile <name>` 部署预检
- 生产运维应用托管服务/既有端点/官方 chart for Postgres/Temporal/NATS/密钥/ingress-TLS/可观测；chart 内 PG/Temporal/NATS/MinIO 模板仅限本地/CI/烟雾

---

## 配套：Infrastructure Agents Guide

姊妹仓库 [Cloudgeni-ai/infrastructure-agents-guide](https://github.com/Cloudgeni-ai/infrastructure-agents-guide)——13 章**基础设施 Agent 设计/构建/运维指南**：架构、沙箱、凭证、变更控制、Terraform/Checkov 技能、GitHub App 访问、云凭证。OpenGeni 与之配对使用。

---

## 与相邻方案的定位关系

OpenGeni 处在"**Agent 持久化运行时**"赛道，但工程取向鲜明：

### vs [[polos]]（最直接竞品，同周调研）

| 维度 | Polos | **OpenGeni** |
|------|-------|-------------|
| 编排核心 | **自研 Rust orchestrator** + Postgres | **直接复用 Temporal** + Postgres |
| Agent SDK | 自有 SDK（Py/TS） | **OpenAI Agents SDK**（借力主流） |
| 编程模型 | 普通代码，反 DAG | Session API + OpenAI Agents SDK |
| 实时流 | OTel trace | **SSE + NATS，exactly-once，sequence 锚定** |
| 沙箱 | Docker/E2B/VM（应用级） | Docker/Modal/本地/云/none **+ Connected Machine** |
| 自带机 | ❌ | ⭐ **一等公民 PRIMARY**（Rust agent，dial-out，不投凭证） |
| 多租户 | 未提 | ⭐ **workspace + 强制 RLS + 三访问模式** |
| 计费 | 未提 | ⭐ **Stripe 计费 + 用量计量** |
| 能力目录 | 内置 sandboxTools | ⭐ **packs + MCP Registry 发现 + 加密凭据头** |
| 成熟度 | 早期（README 为主） | **高度成熟**（架构文档/部署产物/CI/安全边界齐全） |
| 哲学 | "No DAGs，普通代码" | "substrate，非 Agent；embed 或 deploy" |

**核心差异**：Polos 强调"无 DAG 的简洁编程模型 + 自研内核"，OpenGeni 强调"**借力 Temporal/OpenAI SDK 等成熟件 + 把 Agent 跑到你自己的机器上 + 企业级多租户/计费**"。OpenGeni 工程完备度明显高一档。

### vs [[temporal]]
OpenGeni **是 Temporal 的重度消费方**——用 Temporal 做 workflow+signal 编排，但把 token 流挡在 history 之外，turn 跑成不可重试 activity（见不变式 3.2/3.3）。是"在 Temporal 之上造 Agent 专用层"的范本，可对照 [[temporal-durability-stability]]、[[temporal-highlights]]。

### vs [[langfuse]] / [[langchain]] / [[crew-ai]]
这些是 Agent 编排/可观测框架，**不提供运行时基础设施**。OpenGeni 是运行时基底，可承载这些框架产出的 Agent（经 OpenAI Agents SDK 桥接）。

### vs [[dagster]]/[[prefect]]/[[apache-airflow]]/[[argo-workflows]]
数据/批工作流引擎，针对 ETL/批处理，不针对 LLM Agent 的实时交互/沙箱/HITL。详见 [[ai-workflow-landscape]]。

### vs [[dify]]/[[n8n]]/[[langflow]]
低代码可视化流，面向非开发者；OpenGeni 是 **code-first + API-first**，面向运维/产品团队构建 agentic 产品。

### vs [[openshell]]/[[agent-sandbox]]
系统级沙箱路线（强隔离）；OpenGeni 的 Connected Machine 是**反路线**——不隔离，让 Agent 合法直接跑在真实环境，靠"不投递凭证 + dial-out + 显式审批"建信任。Managed Sandbox 则是应用级，与之部分重叠。

---

## 设计取舍（基于架构文档的归纳）

| 决策 | 选择 | 理由 |
|------|------|------|
| 编排 | **直接用 Temporal** | 借力成熟生产系统，不重复造轮子；把精力投 Agent 层 |
| 持久真相源 | **Postgres + 强制 RLS** | 事务一致 + 多租户行级隔离；NATS 只扇出 |
| turn 重试 | **不可重试 activity + 显式恢复 + 重派上限 3** | 副作用不可盲目重试；显式比自动安全 |
| 运行时长 | **按设计无上限，用症状约束** | infra Agent 合理跨天；计数/时钟上限是假安全 |
| 记忆 | **三存储三职责** | 防止把脱敏事件喂回模型、防止用 run state 当记忆 |
| 自带机 | **一等公民，dial-out，不投凭证** | 数据主权卖点；信任靠架构而非隔离 |
| wire 协议 | **proto 一次定义、双栈 codegen** | TS 控制面与 Rust agent 永不漂移 |
| 自更新 | **minisign + sha256 双验 + 原子替换 + 回滚** | 远程机器上的 agent 必须可安全自治更新 |
| SDK | **零运行时依赖 + 契约对等测试** | 可嵌入任意产品，类型永不漂移 |
| 能力探针 | **启用前 initialize 探针，失败返回 422** | 陈旧 MCP 永不破坏运行时 turn |

---

## 适用场景

✅ **适合：**
- 跑长时、有副作用的基础设施 Agent（写 IaC、修合规发现、检测 drift、review PR）
- 想**让 Agent 在自己机器/构建服务器/GPU 盒上**直接跑（数据主权）
- 产品团队想把 Agent **嵌入自家产品**（embed SDK），或跨组织部署
- 需要多租户 + 计费的企业级 Agent 平台
- 需要 HITL 审批 + 可重放审计的合规场景

⚠️ **可能不适合：**
- 单轮问答、无副作用的轻量 Agent（基础设施过重）
- 需要极强系统级隔离的高安全场景（Connected Machine 不隔离；Managed Sandbox 是应用级）
- 已重度投入非 OpenAI Agents SDK 的团队（虽可桥接，但原生体验在 OpenAI SDK）

---

## 项目状态

- **v0.1**，Apache-2.0，早期但基线齐全（license/贡献指南/安全上报/行为准则/issue+PR 模板/CI typecheck+单测）
- 托管试用：[app.opengeni.ai](https://app.opengeni.ai)
- 早期安全边界已明确（三种访问模式、RLS、write-only secret env、沙箱准备策略审查提醒）

---

## 相关

- [[polos]] — 同周调研的最直接竞品；对照编排核心（自研 vs Temporal）、自带机、多租户、成熟度
- [[temporal]] — OpenGeni 的编排基石；OpenGeni 是"Temporal 之上造 Agent 层"的范本
- [[temporal-durability-stability]] / [[temporal-highlights]] — Temporal 持久化原理，OpenGeni turn-as-non-retryable-activity 直接套用
- [[openshell]] — 系统级 Agent 沙箱对照（OpenGeni Managed Sandbox 是应用级，Connected Machine 是反路线）
- [[agent-sandbox]] — K8s SIG Sandbox CRD，另一种沙箱路线对照
- [[langfuse]] — LLM 可观测，与 OpenGeni 的 SSE/事件流/审计时间线对照
- [[ai-workflow-landscape]] / [[ai-workflow-deep-comparison]] — AI 工作流生态全景
- [[langchain]] / [[crew-ai]] — Agent 编排框架，可被 OpenGeni 这类运行时承载
- [[dagster]] / [[prefect]] / [[apache-airflow]] / [[argo-workflows]] — 通用工作流引擎对照

---

## 参考来源

- [Cloudgeni-ai/opengeni — GitHub](https://github.com/Cloudgeni-ai/opengeni)
- [OpenGeni 官网](https://opengeni.ai)
- [architecture.md — 架构参考（不变式地图）](https://github.com/Cloudgeni-ai/opengeni/blob/main/docs/architecture.md)
- [capabilities.md — 能力目录](https://github.com/Cloudgeni-ai/opengeni/blob/main/docs/capabilities.md)
- [packs.md — 能力包](https://github.com/Cloudgeni-ai/opengeni/blob/main/docs/packs.md)
- [agent/README.md — Connected Machine Rust agent](https://github.com/Cloudgeni-ai/opengeni/blob/main/agent/README.md)
- [infrastructure-agents-guide — 姊妹指南仓库](https://github.com/Cloudgeni-ai/infrastructure-agents-guide)
- [app.opengeni.ai — 托管试用](https://app.opengeni.ai)

---

> **置信度说明**：定位、架构（Hono/Temporal/OpenAI Agents SDK/Postgres+NATS/MinIO）、七大不变式、双计算模型、Rust agent crate 结构、monorepo 布局、技术栈、部署产物均直接来自官方 README + architecture.md + agent/README.md，**置信度高**。Star/License/issue 数因 GitHub API 限流未核验，但从 README 明确标注 Apache-2.0、官网标注 v0.1。设计取舍为基于架构文档的合理归纳。
