---
title: DeepSeek Harness — 一切皆插件的开源 Agent Harness
created: 2026-08-14
updated: 2026-08-14
type: entity
tags: [project, ai, platform, open-source, active]
sources: [~/Projects/deepseek-harness, https://github.com/deepseek-ai/deepseek-harness]
confidence: high
---

# DeepSeek Harness

> DeepSeek AI 开源的 agent harness（`dsh`），核心架构是**一切皆插件**：模型适配器、工具注册表、会话日志、agent loop 本身都是可替换的 Cordis 插件，没有需要打补丁的特权核心。当前处于 developer preview（v0.1.0-rc.5，MIT），Node.js 运行时 + 可选 Web UI / headless 模式。

---

## 核心价值主张

| 维度 | 说明 |
|---|---|
| 定位 | 面向编码/任务的通用 agent 运行时 harness：Web GUI、headless CLI、Python SDK 三种形态 |
| 架构哲学 | 一切皆插件（Everything is a Plugin）——通过 vendored [Cordis](https://github.com/cordiverse/cordis) 插件框架实现，无特权核心 |
| 扩展方式 | 插件挂载 + `cordis.yml` 声明式组合（profile/bundle 分层 patch），用户层可覆盖任意配置行 |
| 模型面 | 按 capability seam 暴露工具（~30 个模型可见工具），事件驱动 loop 而非硬编码流程 |
| 数据面 | 追加式事件日志（SessionEvent）作为唯一事实源，"模型可见即已记录"运行时不变式 |
| 开源策略 | MIT、dev preview 快速迭代（明示 breaking change）、暂不收外部 PR、通过 Discussions/dsh-plugin 生态协作 |
| 独特卖点 | capability seam 三角色设计（Service Definition / Provider / Consumer），换一个 Provider 即换整个产品行为 |

## 整体架构

```
                 ┌──────────────────────────────────────────────┐
                 │  dsh CLI (apps/cli) — profile 启动器          │
                 │  dsh web  /  dsh --profile headless "task"    │
                 └───────────────────┬──────────────────────────┘
                                     │ boots profile（bundle 分层 patch）
                 ┌───────────────────▼──────────────────────────┐
                 │  Profile 组合：base → web-app│headless         │
                 │  → profile cordis.patch.yml → 用户 --patch    │
                 └───────────────────┬──────────────────────────┘
                                     │ Cordis Loader 挂载插件树
                 ┌───────────────────▼──────────────────────────┐
                 │  ctx（Cordis Context = 服务仓库）              │
                 │  ctx.sessions  ctx.systemPrompt  ctx.tools    │
                 │  ctx.agents    ctx.agentLoop     ctx.llm      │
                 │  ctx.shell / fs / subprocess / sandbox / ...  │
                 └──────────┬───────────────────┬───────────────┘
                            │                   │
        ┌───────────────────▼─────┐   ┌─────────▼───────────────┐
        │  Agent Loop（turn/step） │   │  Capability Seams       │
        │  agent/* turn/* step/*  │   │  fs/shell/terminal/lsp/  │
        │  tools/* llm/* 事件瀑布  │   │  skill/web/subagent/    │
        └───────────────────┬─────┘   │  workflow/jobs/e2b(POC)  │
                            │         └─────────────────────────┘
                 ┌──────────▼───────────────────────────────────┐
                 │  持久化：SessionEvent 日志（JSONL/SQLite）     │
                 │  SessionHeader 元数据 / flush 批处理 / 崩溃恢复 │
                 └──────────────────────────────────────────────┘
```

## 核心组件

| 组件 | 职责 | ctx key |
|---|---|---|
| `core/session` | 追加式 `SessionEvent` 日志 + 内存 store，唯一事实源 | `ctx.sessions` |
| `core/system-prompt` | prompt 分区 + 工具 schema 组装 | `ctx.systemPrompt` |
| `core/tools` | 作用域工具注册表 + 守卫执行流水线 | `ctx.tools` |
| `core/agent` | `Agent` 接口、活动注册表、initiator 作用域、`agent/*` 事件 | `ctx.agents` |
| `core/agent-loop` | 实现公共 `Agent` 契约的默认 driver | `ctx.agentLoop` |
| `core/scope` | 每 agent 作用域注册原语（无依赖库） | — |
| `llm/llm` | 消息/流词汇 + 适配器 seam | `ctx.llm` |
| `llm-deepseek` / `llm-pi-ai` | 双 LLM 适配器：直连 DeepSeek / 多供应商 pi-ai | 注册到 `ctx.llm` |

能力族（seam 三角色齐全）：`fs`（本地 + 沙箱 + 文件工具）、`shell`（bash/pwsh）、`terminal`（持久 PTY）、`subprocess`、`code-runtime`（Code Mode worker）、`sandbox`（bwrap/Landlock/Seatbelt/Windows ACL）、`lsp`、`skill`、`web`（search/fetch）、`subagent`、`workflow`（worker-thread 引擎）、`jobs`（后台任务 + job_* 工具）、`compaction`、`e2b`（POC）。

Web 双半：`packages/host`（webserver、apiproxy、API gateway 的 Host 端）+ `packages/client`（浏览器 shell、React、`ui-*` 插件、Connection RPC 载体）。

## 核心概念

- **Plugin** — 实现 Service 的对象（函数 + `inject`/`apply`，或 Service 子类），注册到共享 Context；一切注册都是可逆 effect（卸载即回滚）。
- **Context** — 服务仓库；服务声明稳定 `ctx.<key>`，插件按 key 发现服务而非 import 具体实现；`inject` 表达依赖，隐式决定加载顺序。
- **Capability seam** — 可替换能力的三角色：Service Definition（抽象服务/注册表）+ Service Provider + Consumer（通常是模型工具）。换 Provider 即换产品：fs/subprocess Provider 指向远端沙箱，Bash/PTY/LSP 随之迁移。
- **SessionEvent 日志** — 追加式事件流，`deriveMessages()` 从日志投影模型历史；fork/resume/转写/遥测/持久化全部派生自同一流。"模型可见 ⟺ 已记录"。
- **Profile / Bundle** — profile 是有名组合（$DSH_HOME/profiles/<name>），bundle 是 Cordis 配置行 + 代码的分发格式；分层 patch 覆盖（整行替换，无深合并）。
- **Turn / Step** — turn 是输入排水周期（可含 0..n 个 step），step 是一次模型请求 + 其触发的工具执行。
- **Agent scope** — 每 agent 作用域注册（`agent.ctx`）：作用域工具/提示分区以"最具体者胜"遮蔽全局同名项；setup 窗口在发布前组装 agent 的世界。

## 数据流（一次 turn）

```
turn/start
  claim 下一 step 输入 + 一条排队消息
  组装 prompt 分区 + 工具 schemas
  → agent/pre-step（可改写/拒绝，waterfall）
  step/start
  追加 entered messages 为 user/message（持久事件）
  从日志 deriveMessages() 派生模型历史
  agent/request → llm/stream → assistant/chunk* → assistant/message
  tool/call → tools/pre-execute → tools/execute → tools/post-execute → tool/result*
  step/end（工具要求再来一次 / 新输入到达 → 下一 step）
  → agent/turn-stopping（serial，可终止 turn）
turn/end
```

输入经单一 inbox 到达 driver；`agent.inject()` 注入的上下文在 inbox 等待直到其他消息唤醒。`turn/*`、`step/*`、`user/message`、`assistant/*`、`tool/*` 是持久 session 事件，其余是三个域的活动扩展点。

## 持久化层 / 数据模型

- **SessionEvent 日志**：唯一事实源；`SESSION_FORMAT_VERSION = 0`，后端拒绝读不懂的版本（无迁移，pre-release 姿态）。
- **SessionHeader**：随日志旁路的元数据（version/id/createdAt/cwd/parentSession/seedLength/origin/delegationDepth/agentPreset），不进事件流、不进模型上下文。
- **后端**：`session-persistence-jsonl`（每会话独立转写文件）与 `session-persistence-sqlite`（共享库，`SCHEMA_VERSION` 单调递增）。
- **flush checkpoint**：`session/event` 同步通知 + 每会话控制器批量窗口；`session/flush` 作为下一 turn 前的排序/错误观察点。
- **崩溃恢复**：冷会话遇到无 `turn/end` 的孤儿 turn 不截断，追加合成 `turn/end { reason: interrupted }` 保持平衡。
- **派生层**：projection（缓存）、telemetry（OTel）、title 生成、session-query（SQLite FTS + 血缘）。

## 项目结构

```
deepseek-harness/
  apps/            cli（dsh 启动器）、web（前端构建）
  packages/        219 个 workspace 包，@deepseek-ai/dsh-*
    core/          session · system-prompt · tools · agent · agent-loop · scope
    llm/           llm seam · llm-deepseek · llm-pi-ai · token-meter · llm-retry
    session/       persistence seam + JSONL/SQLite · projection · telemetry · titles
    host/ client/  Web GUI 双半：webserver/apiproxy + React shell/ui-* 插件
    api/           Typert RPC gateway（@Remote 装饰器 → 生成 Host/Client 契约）
    sdk/ acp/      JSON-RPC 协议+TS client · Agent Client Protocol 服务器
    bundle/        base · web-app · headless（profile patch 层）
    boot/ preset/  app 启动胶水 · 每会话预设组合
    interaction/   approval/权限/命令/ask-user 工具
    hooks/         Claude Code / Codex hook 桥 + 线协议库
    extensions/    运行时自修改（cordis_* 工具，opt-in）
    examples/      agent-spine-demo 等演示 bundle
  vendor/          vendored Cordis 全家（@deepseek-ai/cordis 4.0.0-rc.7 等 9 包）
  python/          deepseek-harness-sdk + 捆绑 runtime（stdio JSON-RPC）
  native/          node-addon-landlock-run（Linux 沙箱）
  website/         VitePress 文档站投影
```

## 技术栈

| 类别 | 技术 |
|---|---|
| 语言/运行时 | TypeScript 6（strict，ESM only）、Node ^22.19 \|\| >=24、pnpm 11.7 workspace |
| 插件框架 | vendored Cordis 4.0.0-rc.7（含 loader/include/hmr/schemastery/cosmokit，rescope 到 @deepseek-ai） |
| 构建 | tsc -b（host/client 双 face）+ tsdown 打包 + Vite 前端 |
| 测试 | Vitest 4（unit/coverage 100% 每文件/e2e/snapshot 无 key 回放/Web stress/perf） |
| 静态门禁 | oxlint、knip、publint、jscpd、lefthook、~30 个 verify-* 生成目录校验 |
| 持久化 | JSONL 转写、SQLite（会话）、OTel 遥测 |
| 沙箱 | bwrap（Linux）、Landlock（native addon）、Seatbelt（macOS）、Windows ACL restricted token |
| 协议 | JSON-RPC（SDK）、ACP、MCP、LSP、Typert RPC 网关、Claude Code/Codex hook 线协议 |
| 其他语言 | Python SDK（deepseek_harness）、ripgrep（打包 @vscode/ripgrep 供 glob/grep） |

## 构建与测试

```sh
pnpm install && pnpm run build      # tsc -b host/client + tsdown + web 前端
pnpm run test                      # vitest unit
pnpm run test:coverage             # CI 覆盖门禁：每文件 100%
pnpm run test:e2e                  # 真 API（无 DEEPSEEK_API_KEY 自动跳过）
pnpm run test:snapshot             # 无 key ACP/headless 回放
pnpm run typecheck && pnpm run lint
pnpm run hygiene                   # knip+publint+constraints+vendored links 等
pnpm dsh web                       # Web UI @ http://127.0.0.1:3080（源码模式）
pnpm dsh --profile headless "task" # 一次性 headless 跑任务
```

## 设计权衡

1. **一切皆插件 vs 组合复杂度**：没有特权核心、所有组件可配置替换（含 agent-loop 本身）；代价是引导顺序靠服务依赖隐式表达，需要 `--dump-config` 工具审视组合树。
2. **Vendored Cordis 源码 vs npm 依赖**：harness 完全拥有框架层（可审计/可 patch/可 pin），发布时随 harness 一起发布框架；代价是 18 项本地修改需在每次 sync 时重放。
3. **事件日志唯一事实源 vs 格式演进**："模型可见即已记录"不变式保证可回放/可 fork/可遥测；代价是 `SESSION_FORMAT_VERSION=0` 拒绝旧/新格式，无迁移路径（dev preview 明示接受）。
4. **Capability seam 三角色 vs 设计成本**：换 Provider 全局生效（fs/shell 指向远端沙箱即整个执行世界迁移）；每个新能力必须一次设计完三个角色。
5. **生成目录 + 双构建 face vs 构建顺序约束**：tool/config/persistence/module-graph 目录全部由脚本生成并 CI 保鲜，文档永不漂移；Typert 需严格按 Host→Client→Web 顺序构建。
6. **Dev preview 姿态**：无兼容承诺、后端拒旧格式、暂不收外部 PR（社区走 Discussions + dsh-plugin 生态）；换取迭代速度。
7. **双 LLM 适配器**：直连 DeepSeek 与多供应商 pi-ai 并行（twin adapters），路由在 seam 上按需选择。
8. **沙箱按平台实现**：bwrap/Landlock/Seatbelt/Windows ACL，`ctx.sandbox` 在执行前包裹 argv；Windows 上 shell 栈整体切换为 pwsh（同一 patch 文件平台表达式控制）。
9. **patch 整行替换**：profile 覆盖必须重述保留的字段，无深合并层——简单但重复。

## 模型可见工具集（~30）

`bash`/`pwsh`、`edit`/`read`/`write`/`read_image`、`glob`/`grep`、`str_replace_editor`、`terminal_*`（6 个）、`run_code`、`web_search`/`web_fetch`、`subagent`/`subagent_fork`、`interrupt_agent`/`list_agents`/`send_message`、`workflow`/`ralph`、`job_*`、`todo_write`、`skill`、`create_goal`/`get_goal`/`update_goal`、`schedule_*`、`lsp`、`ask_user_question`、`exit_plan_mode`、`session_event_read`/`session_search`/`session_trace` 等、opt-in `cordis_*`（运行时自修改）。

## 生态系统

| 面 | 内容 |
|---|---|
| 形态 | `dsh web`（浏览器 GUI）、`dsh --profile headless "task"`（一次性）、Python SDK（stdio JSON-RPC 驱动子进程） |
| Bundles | `dsh-base`（模型/工具/持久化/策略/设置/凭据/遥测）→ `dsh-web-app` 或 `dsh-headless` |
| 互操作 | ACP 服务器（自动化）、JSON-RPC SDK（进程外）、MCP、LSP、Claude Code/Codex hook 桥 |
| 社区 | GitHub Discussions、Discord、`dsh-plugin` topic（插件发现） |
| 周边 | 官方插件生态尚在起步；examples/agent-spine-demo 是装配示范 |

## 相关链接

- [GitHub: deepseek-ai/deepseek-harness](https://github.com/deepseek-ai/deepseek-harness)
- [Cordis 框架](https://github.com/cordiverse/cordis) / [设计论文《A Programming Paradigm for Spatiotemporal Composability》](https://github.com/cordiverse/paper)
- [发布报道（gigazine）](https://gigazine.net/news/20260814-deepseek-harness-v0-1/)
- [发布解读（NYU rits）](http://rits.shanghai.nyu.edu/ai/deepseek-harness-cordis-everything-is-a-plugin/)

## 相关

- [[kagent-agent-harness]] — Kagent 的 AgentHarness 概念对照（另一个 harness 定位）
- [[acp-protocol]] — dsh 实现了 ACP 服务器，ACP 是编辑器↔Agent 标准协议
- [[loop-engineering]] — dsh 的 turn/step 事件驱动 loop 是 loop 工程的具体实现
- [[ai-agent-ecosystem]] — 放入 AI agent 生态全景
- [[claude-code-execution-security]] — dsh 的 sandbox 纵深与 Claude Code 执行安全对照
- [[temporal-durability-stability]] — dsh 的事件日志持久化与 Temporal durable execution 对照
- [[deer-flow]] — 字节 Super Agent Harness，同为 harness 定位的对照物
