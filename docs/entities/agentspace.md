---
title: AgentSpace
created: 2026-07-21
updated: 2026-07-21
type: entity
tags: [project, ai, platform, agent, b2b, active, typescript, governance, marketplace]
sources:
  - ~/Projects/AgentSpace 源码
  - https://github.com/AgentSpace-Hub/AgentSpace
confidence: high
---

# AgentSpace

> 开源的 agent-native 协作 workspace —— 让人类团队和「数字员工」在同一个组织上下文里干活。把散落在个人终端里的 Agent 变成有身份、有 owner、有技能、有审批边界的组织资产，并用一层 AgentRouter 把 8 种 agent CLI（Claude Code / Codex / Antigravity / OpenCode / OpenClaw / Hermes / Gemini / NanoBot）归一成统一执行契约。TypeScript monorepo + PostgreSQL，Apache-2.0。

---

## 核心价值主张

| 维度 | 说明 |
|------|------|
| **Agent 是员工，不是工具** | 数字员工有 identity / role / owner / instructions / skills / knowledge，可在组织内招募、共享、转移、审计 |
| **同一 Agent，最合适 runtime** | Agent 身份与上下文跨任务稳定，AgentRouter 按任务路由到不同 harness，换 harness 不丢技能与知识 |
| **共享 workspace 上下文** | 频道、inbox、文档、任务看板、runtime 产物都挂在 workspace 上，人类与 Agent 同一操作面 |
| **治理优先** | 权限/审批/审计/预算是一个 control plane，敏感动作进 human approval gate（TabTabTab 风格快循环） |
| **产物持久化** | 工作产出是 tasks / files / docs / runtime outputs / approvals / durable history，不只是聊天记录 |
| **双部署同源** | 托管版 hire-an-agent.online 与自托管版跑同一份代码，**无功能差异** |

定位对标：[[orloj]]（"Agents are infrastructure" 全栈平台，最接近的架构表亲）、[[polos]]（"给 Agent 用的 Temporal" 持久化运行时）、[[temporal]]（持久化执行平台，task queue 的精神原型）、[[multica]]（AI 原生任务管理）。

---

## 整体架构

```
                    ┌─────────────────────────────────┐
                    │            人类成员               │
                    │  (owner / admin / member)        │
                    └──────┬──────────────────┬────────┘
                           │                  │
                  ┌────────▼────────┐ ┌───────▼────────┐
                  │  apps/web        │ │  apps/cli       │
                  │  Next.js 16 +    │ │  agent-space    │
                  │  React 19        │ │  (node --strip- │
                  │  (Server Actions)│ │   types)        │
                  └────────┬────────┘ └───────┬────────┘
                           │                   │
                           └────────┬──────────┘
                                    │
                    ┌───────────────▼───────────────┐
                    │  @agent-space/services        │ ← 业务逻辑层
                    │  tasks · approvals · channels  │
                    │  documents · knowledge · skills│
                    │  budgets · schedules · audit   │
                    └──────┬───────────────┬────────┘
                           │               │
             ┌─────────────▼──┐      ┌─────▼──────────────┐
             │ @agent-space/db │      │ @agent-space/domain │ ← 纯类型/契约
             │ PostgreSQL 16    │      │ runtime-agnostic    │
             │ schema v23, ~60表│      │ (无 node:crypto)    │
             └─────────────────┘      └─────────────────────┘
                           │
              ┌────────────▼──────────────┐
              │  task queue / approvals    │
              │  (postgres 持久化)          │
              └────────────┬──────────────┘
                           │ 下发任务
              ┌────────────▼──────────────┐
              │  agent-space-daemon        │ ← 远端执行进程
              │  (register + heartbeat)    │   可装在任何 host
              └────────────┬──────────────┘
                           │
                ┌──────────▼──────────────┐
                │  provider-runtime        │
                └──────────┬──────────────┘
                  ┌────────┴────────┐
                  │                  │
          ┌───────▼──────┐  ┌────────▼─────────┐
          │  AgentRouter  │  │ legacy provider   │
          │  (归一契约)    │  │ runtime           │
          └───────┬───────┘  └────────┬─────────┘
                  │                  │
   ┌──────┬──────┼──────┬──────┬────┴───┐
   ▼      ▼      ▼      ▼      ▼        ▼
Claude  Codex  Antigr OpenCode OpenClaw NanoBot
 Code    CLI   avity                Hermes   (Gemini)
```

> 来源：README.md 的 mermaid `flowchart TD`。AgentRouter 只做归一，**不接管业务队列**；queue / runtime-output / workspace skills / Web UI 仍在 daemon 外层。

---

## 核心服务与模块（monorepo 5 包 + 2 app）

| 包 / app | 职责 | 关键文件 |
|---|---|---|
| `apps/web` | Next.js 16 workspace 前端 + Server Actions API（`/api/daemon/*`, `/api/workspaces/*`, `/api/integrations/*`）。25 个 feature 模块（agents/approvals/automations/calendar/inbox/knowledge/market/org-chart/performance/tables/task-board/…） | `apps/web/app/w/[slug]/*` |
| `apps/cli` | `agent-space` CLI：doctor / workspace / im / channel / task / daemon / integrations 子命令，JSON 输出。含 `openagent-persona-sign`（ed25519 签名层） | `apps/cli/src/index.ts` |
| `@agent-space/domain` | **纯类型 + 契约**，runtime-agnostic（无 `node:crypto`/`Buffer`）。`AgentSpaceState`、`ActiveEmployee`、`AgentTemplate`、`DaemonProvider`、`ApprovalRequest`、`OpenAgentPersona` | `packages/domain/src/workspace.ts` 等 |
| `@agent-space/db` | PostgreSQL 访问层，schema v23，`CREATE TABLE IF NOT EXISTS` 声明式 + `database-schema-lock` 防漂移；SQLite→PG 迁移 CLI | `packages/db/src/postgres-schema.ts` |
| `@agent-space/services` | 业务服务层：~40 个领域服务目录（approvals/budgets/schedules/automations/knowledge-proposals/permissions/policies/…）。集成 Lark SDK + fflate | `packages/services/src/` |
| `agent-space-daemon` | **远端执行进程**，npm 打包成 `.tgz` 可全局安装。含 `agent-router` 子包（harness 归一）、`provider-runtime`、`remote-daemon`、`runtime-output`、`task-context`、`skill-imports` | `packages/daemon/src/` |
| `@agent-space/sandbox` | 沙箱抽象 `interface Sandbox`（readFile/writeFile/exec/snapshot/stop/destroy）。两实现：`local-sandbox` + `cube-sandbox`（实验中的 Cube scaffold） | `packages/sandbox/src/` |

---

## AgentRouter —— provider harness 归一层

定位：**不替代 workspace、不接管业务队列**，只负责启动不同 agent CLI 并把 events / results / sessions / diagnostics 归一成统一契约。

| Provider | 执行路径 | 归一的 diagnostics |
|---|---|---|
| Claude Code | AgentRouter | stream-json events、session fallback、tool approval bridge |
| Codex CLI | AgentRouter | JSON events、session fallback、runtime tool capability diagnostics |
| Antigravity CLI | AgentRouter | `agy -p` prompt-mode、conversation 复用、timeout/nonzero/empty |
| OpenCode | AgentRouter | JSON events、session propagation、PATH capability injection |
| OpenClaw | AgentRouter | health/preflight、auth/profile/model/tool/protocol diagnostics、missing session fallback |
| Hermes Agent | AgentRouter | 文本输出、executable 兼容检查、timeout/empty-response |
| Gemini CLI | legacy provider-runtime | 旧 one-shot fallback（用户仍可访问 Gemini CLI 时） |
| NanoBot | legacy provider-runtime | one-shot CLI |

独立 smoke：

```bash
agent-router harnesses          # 列出已装 harness
agent-router detect            # 探测本机可用 provider
agent-router run --harness claude --cwd /workspace/project "summarize this repo"
agent-router run --harness codex --cwd /workspace/project --model gpt-5.1 "fix tests"
agent-router run --harness openclaw --cwd /workspace/project --mode medium "review this diff"
agent-router run --harness claude --json-events "write a plan"   # JSONL: normalized events + {type:"result"}
```

> Gemini / NanoBot 暂留旧路径，后续可继续收口到它们的 gateway/serve API。Hermes 第一版无原生 JSON event stream，AgentRouter 把 stdout 归一为最终 `outputText` 并通过统一 diagnostic contract 返回非零退出 / 超时 / 空响应。

---

## Permission Control Plane（治理面）

围绕 **resources × actors × grant sources × execution capabilities × external delegation** 组织。所有权限可「按资源树」或「按 actor」检视、撤销、审计、诊断漂移。

| 面 | 能力 |
|---|---|
| Workspace 成员 | owner/admin/member 角色、邀请链接、join code、邀请历史 |
| Channel 访问 | 加入、频道邀请、访问请求、读写断言；DM 隐私 scoped 到参与者与相关 agent owner |
| Agent 管理 | owner、instructions、channel 可用性、skills、knowledge、runtime 绑定 |
| Runtime grants | 用户级 grant、runtime 共享、bind/unbind、provider 健康度 |
| Daemon 安全 | API token create/revoke、远端 daemon 注册、runtime display name |
| Documents | owner/editor/viewer、agent access、permission request、版本回滚 |
| Google Workspace | OAuth 凭据 owner、agent-scoped delegation、外部文档请求 |
| Approvals | runtime tool approval、knowledge proposal approval、document permission |
| Diagnostics | missing grants、revoked credentials、orphaned grants、unavailable providers |

跨 workspace 访问会被显式拒绝并记 audit event（`workspace.cross_workspace_access_denied`）。

---

## 核心概念

- **Digital Employee（数字员工）** —— `workspace_employee` 表里的一等实体：name/role/remark_name/origin/summary/traits_json/fit/status/instructions/**owner_user_id**/channel_member_access。把"私人 Agent"变成"组织员工"。
- **AgentTemplate** —— 预设角色（`finance-analyst` / `product-manager` / `product-designer`），每个带 skillRecommendations（required/recommended/optional）和 searchTerms，用于 Skill Hub 匹配。
- **AgentSpaceState** —— workspace 级聚合状态（approvals / tasks / channels / …），services 层 `ensureWorkspaceStateSync(workspaceId)` 读写。
- **ActiveEmployee** —— 已解析完 skills/knowledge/runtime 绑定、可执行的活动员工对象；`employeeToPersona()` 把它映射成 OpenAgent persona-card。
- **Runtime grant** —— 用户对 `agent_runtime` 的使用授权；daemon 注册时自动给 token 创建者 grant。
- **Approval gate** —— 高影响动作（tool use / document access / external send / budget-sensitive）路由进人类审批；支持 `runtime_tool` 类型并做 pending 去重。
- **Budget 三层 + daemon 超支拦截** —— 预算管控在 daemon 执行前拦截超支任务。
- **OpenAgent persona-card** —— 跨组织转移 Agent 身份的互操作件（见下「开源亮点」）。

---

## 数据流：一次 founder team 执行

```
1. 人类在 workspace channel 丢一个请求（无 ticket 系统）
2. coordinator agent 拆解 → 切分/定 scope/派给 specialist agents
3. agents 收集上下文：documents + knowledge pages + Google Workspace 文件 + 历史 runtime outputs
4. 高风险动作前 flag → tool use / doc access / external send / budget 动作进 human approval gate
5. 人类 approve/reject（一次决策，全可见，无需 micromanage）
6. agents 完成工作 → 结果写回 tasks / docs / attachments / runtime outputs，全程 audit
```

底层 daemon 侧执行流：

```
task queue (postgres) → daemon poll → provider-runtime 组 AgentRouterRunRequest
  → AgentRouter spawn harness CLI（claude -p --stream-json / codex exec / agy -p / …）
  → normalize JSONL events → runtime-output manifest + diagnostics
  → 写回 services（task_execution_event / task_message / token_usage / budget 扣减）
  → 敏感动作经 tool approval bridge 回到 Web 审批 UI
```

---

## 持久化层 / 数据模型

PostgreSQL 16，schema 版本 `23`，约 60 张表，由 `database-schema-lock` 测试锁住预期 schema。核心表族：

| 表族 | 代表表 |
|---|---|
| 组织/身份 | `workspace`, `users`, `auth_identity`, `session`, `workspace_membership`, `workspace_invitation` |
| 数字员工 | `workspace_employee`, `agent_fork_invitation`, `agent_fork_snapshot`, `employee_runtime_binding` |
| 任务/队列 | `workspace_task`, `agent_task_queue`, `agent_task_attempt`, `task_execution_event`, `task_message` |
| 运行时/daemon | `daemon_connection`, `daemon_api_token`, `agent_runtime`, `workspace_runtime_grant`, `runtime_app_operation` |
| AgentRouter | `agent_router_session`, `agent_router_provider_session`, `agent_router_event`, `agent_router_context_snapshot` |
| 治理/审批 | `document_agent_access`, `document_permission_request`, `agent_access_request`, `audit_log`, `budget` |
| 知识/技能 | `skill`, `skill_file`, `agent_skill`, `agent_knowledge_page`, `knowledge_proposal`, `runtime_app_skill_binding`, `skill_import_event` |
| 成本 | `model_pricing`, `token_usage`, `budget` |
| 外部集成 | `external_integration`, `external_user_binding`, `external_channel_binding`, `external_resource_binding`, `external_message_mapping`, `external_message_outbox`, `external_data_operation_run`, `external_integration_event`, `external_thread_binding` |
| Google Workspace | `google_oauth_credential`, `agent_google_workspace_delegation` |
| 其他 | `workspace_channel`, `channel_participant`, `workspace_notification`, `attachment`, `workspace_snapshot`, `runtime_app_catalog_item`, `runtime_installed_app`, `app_metadata` |

> `agent_fork_*` 两表是「Agent 转移/fork」的持久化基础，配合 `OpenAgentPersona` 做跨组织身份导出。

---

## 项目结构

```
AgentSpace/
├── apps/
│   ├── web/          Next.js 16 workspace（app/ + features/ + e2e/）
│   └── cli/          agent-space CLI（node --experimental-strip-types 直跑 .ts）
├── packages/
│   ├── domain/       纯类型/契约（runtime-agnostic，可被 web 与 daemon 共用）
│   ├── db/           PostgreSQL 访问 + schema 声明 + 迁移 CLI
│   ├── services/     ~40 个领域服务（approvals/budgets/schedules/automations/…）
│   ├── daemon/       agent-space-daemon + agent-router 子包（harness 归一）
│   └── sandbox/      Sandbox 接口 + local/cube 两实现
├── deploy/
│   ├── systemd/      agentspace.service / agentspace-daemon.service / agentspace-feishu-worker.service
│   ├── nginx/        agentspace.conf（反代 127.0.0.1:1455 + WebSocket upgrade）
│   ├── postgres/     docker-compose.yml（postgres:16）
│   └── feishu-worker/ docker-compose.yml + env.example
├── scripts/feishu/   飞书 smoke / db 测试
├── .github/workflows/deploy-production.yml
├── TODO/             按 PR 编号的需求文档（120-34 等，多数已 Done）
└── README.md / README_ZH.md / Target.md / CONTRIBUTING.md
```

---

## 技术栈

| 类别 | 技术 |
|---|---|
| 语言 | TypeScript 5.9（`--experimental-strip-types` 直跑源码，生产 daemon 用 esbuild bundle） |
| 前端 | Next.js 16、React 19、Server Actions（需稳定 `NEXT_SERVER_ACTIONS_ENCRYPTION_KEY`） |
| 后端 | Node.js 24（daemon ≥ 20.20）、npm 11 workspaces monorepo |
| 数据库 | PostgreSQL 16（schema v23，从 SQLite 迁移而来，带 schema-lock 测试） |
| 测试 | Vitest 3（`*.test.ts` 与源码同目录）、Playwright e2e（`apps/web/e2e`） |
| 构建 | esbuild（daemon `scripts/build.mjs`）、`tsc` 多 `tsconfig.types.json` 生成 `dist-types` 跨包类型 |
| 沙箱 | 自研 `Sandbox` 接口 + local + Cube（实验） |
| 集成 SDK | `@larksuiteoapi/node-sdk`（飞书）、fflate、pg |
| 部署 | systemd unit + nginx 反代 + docker-compose（postgres / feishu-worker） |
| CI | `deploy-production.yml`（单工作流） |

---

## 构建与测试

```bash
# 1. 装依赖（逐子包 install，no-audit no-fund）
npm run setup

# 2. 起 PG
cp .env.example .env
docker compose -f deploy/postgres/docker-compose.yml up -d
npm run db:pg:init          # 初始化 schema

# 3a. 跑 workspace（dev，监听 0.0.0.0:1455）
npm run dev:web

# 3b. 或用 CLI
npm run cli -- help
npm run cli -- doctor --json
npm run cli -- task list --json
npm run cli -- daemon status --json

# 4. 质量门（typecheck + lint + vitest）
npm run quality:web
npm run typecheck            # deps + web + cli + daemon 四段
npm run test:e2e:web         # Playwright

# 5. 打 daemon 远端包
npm run daemon:pack          # → agent-space-daemon-0.1.3.tgz
#   远端：npm i -g ./agent-space-daemon-0.1.3.tgz
#   agent-space-daemon start --foreground --server-url … --daemon-token adt_xxx …

# 6. PG 运维
npm run db:pg:status -- --json
npm run db:pg:migrate -- --dry-run --sqlite-path data/agent-space.sqlite --json
```

---

## 设计权衡

1. **AgentRouter 是归一层不是运行时** —— 不接管业务 queue、不替代 workspace，只把 8 种 CLI 的 events/sessions/diagnostics 归一。好处：业务逻辑稳定，换 harness 只换 adapter；代价：Gemini/NanoBot 等仍走 legacy provider-runtime，存在双路径技术债（README 明确标注「后续可继续收口」）。
2. **远端 daemon 解耦执行** —— Web 服务器不直接 spawn agent CLI，而是 daemon 注册 + 心跳 + 领任务。好处：runtime 机器与 Web 机器分离、可跨网络、可多机扩、CLI 凭据隔离在 daemon 用户下；代价：多一层 register/heartbeat 协议与 daemon token 治理。
3. **domain 包 runtime-agnostic** —— `@agent-space/domain` 禁用 `node:crypto`/`Buffer`，ed25519 签名放 `apps/cli` 的 Node 层。好处：类型/契约可同时被 web 与 daemon 复用、纯函数易测；代价：签名链路跨包，`employeeToPersona()` mapper 与 signer 分离。
4. **Postgres-only + schema-lock** —— 从 SQLite 迁到 PG，schema v23 用 `database-schema-lock.test.ts` 锁预期。好处：JSONB + FTS5 等高级查询、生产级并发；代价：无 SQLite 本地零依赖模式（迁移 CLI 仍保留 `migrate-from-sqlite`）。
5. **persona 默认隐私脱敏** —— `employeeToPersona()` 默认 REDACT operator instructions / resolved skills / owner identity，`includeSensitive: true` 才 opt-in。好处：persona-card 是可分享的身份件不是私配导出；代价：消费方需要显式开关才能拿全量。
6. **托管与自托管同源无功能差** —— 同一份代码，托管在 `hire-an-agent.online`。好处：自托管用户无功能阉割、开源可信度高；代价：商业模型靠托管便利性而非功能锁定。
7. **治理优先于更聪明的 chatbot** —— 明确 slogan「humans own direction and authorization, agents own coordination and execution」。好处：填补多数 agent 框架的 governance 空白；代价：审批/预算/权限层对个人单机用户偏重。

---

## 开源亮点

- **Apache-2.0 + 完全自托管 + 无功能差** —— 托管与自托管同源，不像很多 agent 平台把治理/调度锁在 SaaS。
- **AgentRouter：跨 8 harness 的统一执行契约** —— 把 Claude Code / Codex / Antigravity / OpenCode / OpenClaw / Hermes 的 events / sessions / outputs / diagnostics 统一归一，`--json-events` 输出 JSONL + 终态 `{type:"result"}`。是少有的「provider harness normalization layer」开源实现。
- **结构化 provider diagnostics** —— 统一错误码族 `provider.cli_missing` / `provider.profile_missing` / `provider.auth_invalid` / `provider.model_unavailable` / `provider.session_invalid` / `provider.tool_missing` / `provider.tool_unauthorized` / `provider.tool_permission_denied` / `provider.protocol_parse_failed`，runtime online ≠ provider usable，preflight 快速失败。
- **Digital Employee 一等公民** —— `workspace_employee` 表 + `owner_user_id` + skills/knowledge/runtime 绑定，Agent 身份跨任务跨 runtime 稳定，可在组织内 fork/transfer（`agent_fork_*` 表）。
- **OpenAgent persona-card 互操作** —— `openagent-persona.ts` 把 ActiveEmployee 映射到 [OpenAgent](https://github.com/5dive-ai/openagent) persona-card（face/voice/provenance），CLI 层加 ed25519 签名 + `did:key` 派生，默认脱敏。这是 Agent 跨组织身份互操作的开源尝试。
- **治理四件套全内置** —— 权限 control plane + TabTabTab 风格审批循环 + 三层预算 + 全量 audit_log，多数 agent 框架缺这部分。
- **IM 集成但治理不外泄** —— 飞书集成（2026-07-02 合并 main，bind-channel/bind-user/bind-resource）+ Slack 插件（测试分支），把 AgentSpace agent 接到 IM 对话但治理留在 AgentSpace。
- **远端 daemon 可打包分发** —— `npm run daemon:pack` 产 `.tgz`，`npm i -g` 装、systemd 起服务，runtime 机器可远离 Web 机器。
- **TODO-as-design-log** —— `TODO/` 下按 PR 编号存需求文档（`12-channel-documents.md`、`21-approvals.md`、`27-automation-workflows.md`、`33-budget-control.md` 等，多数已 Done），是少见的把设计决策 PR 化留痕的开源项目。
- **新闻线活跃** —— 2026-06-21 v1.0 首发 → 06-22 AgentRouter 支持 5 harness → 06-24 OpenCode 收口 → 07-02 飞书合并 → 07-09 Slack 测试分支 → 07-13 Antigravity CLI 接入。

---

## 生态系统

| 周边件 | 角色 |
|---|---|
| OpenAgent (5dive-ai) | persona-card 身份规范，AgentSpace 导出对齐 |
| 飞书 / Lark SDK | IM 渠道集成（已合并） |
| Slack 插件 | IM 渠道集成（测试分支） |
| Google Workspace | OAuth 凭据 + agent-scoped delegation |
| Cube scaffold | 实验中沙箱实现 |
| 8 个 agent CLI | Claude Code / Codex / Antigravity(`agy`) / OpenCode / OpenClaw / Hermes / Gemini / NanoBot |

---

## 相关链接

- 仓库：`~/Projects/AgentSpace`（本机）/ https://github.com/AgentSpace-Hub/AgentSpace
- 托管版：https://hire-an-agent.online
- daemon 包文档：`packages/daemon/README.md`（provider 说明 / OpenClaw health / Hermes / Cube scaffold / troubleshooting）
- 飞书 smoke：`scripts/feishu/README.md`
- 设计需求档：`TODO/README.md`（PR 编号 → 需求文档索引）

---

## 相关 Wiki 页

- [[orloj]] —— "Agents are infrastructure" 全栈平台，最接近的架构表亲（声明式 + 治理 + 多 Agent + GitOps）
- [[temporal]] —— 持久化执行平台，AgentSpace task queue 的精神原型
- [[polos]] —— "给 Agent 用的 Temporal" 持久化运行时，durable log + HITL 审批 + 沙箱
- [[kagent]] —— Kubernetes 原生 Agent 框架（CRD 声明 + 多运行时 + MCP/A2A）
- [[multica]] —— AI 原生任务管理（Go + Next.js monorepo 表亲）
- [[deer-flow]] —— 字节跳动开源 Super Agent Harness（lead_agent 编排 + IM 渠道）
- [[zed-agent-architecture]] —— Zed Agent 8 crate 分层 + ACP/MCP 双协议
- [[agent-sandbox]] —— K8s SIG Apps Sandbox CRD，与 `@agent-space/sandbox` 的隔离思路对照
- [[ecc]] / [[superpowers]] —— 跨 harness Agent skill 生态，与 AgentSpace skill-imports/runtime-app-skill-binding 对照
