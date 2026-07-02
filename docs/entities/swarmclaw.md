---
title: SwarmClaw
created: 2026-05-25
updated: 2026-06-28
type: entity
tags: [product, saas, platform, ai, agent-runtime, multi-agent, open-source, nextjs, electron, mcp, openclaw]
sources: [~/Projects/swarmclaw/]
confidence: high
---

# SwarmClaw

> 开源自托管 AI Agent 运行时与多 Agent 编排框架。23+ LLM 提供商、12+ 聊天连接器、MCP 工具、扩展系统、自主任务（Mission）、心跳调度、Agent 委派与蜂群协作。定位为 Claude Code 和 LangChain 的自托管替代方案。

---

## 基本信息

| 项目 | 详情 |
|------|------|
| 版本 | v1.9.35 |
| 许可证 | MIT |
| npm 包 | `@swarmclawai/swarmclaw` |
| GitHub | github.com/swarmclawai/swarmclaw |
| 网站 | swarmclaw.ai |
| 代码规模 | ~1637 TS/TSX 文件，~312K 行 |
| 运行时要求 | Node.js ≥ 22.6 |

## 技术栈

```
┌─────────────────────────────────────────────────────┐
│                    Electron 桌面端                    │
│              (macOS / Windows / Linux)               │
├─────────────────────────────────────────────────────┤
│              Next.js 15 (standalone)                 │
│            Turbopack dev / port 3456                 │
├──────────────┬──────────────┬───────────────────────┤
│  React 前端   │  Zustand 状态  │   Tailwind CSS       │
│  App Router   │  setIfChanged │   shadcn/ui          │
├──────────────┴──────────────┴───────────────────────┤
│                   服务端核心层                        │
│  ┌─────────┐ ┌──────────┐ ┌───────────┐            │
│  │ Session │ │ Provider │ │ Connector │            │
│  │  Run    │ │ Registry │ │  Manager  │            │
│  │ Manager │ │ 23+ LLM  │ │ 12+ 渠道  │            │
│  └────┬────┘ └────┬─────┘ └─────┬─────┘            │
│       │           │             │                    │
│  ┌────▼───────────▼─────────────▼─────┐             │
│  │        Agent Main Loop             │             │
│  │  (Delegation / Swarm / Subagent)   │             │
│  └───────────────┬────────────────────┘             │
│                  │                                   │
│  ┌───────────────▼────────────────────┐             │
│  │  Extensions · MCP · Skills · Memory│             │
│  └───────────────────────────────────┘             │
├─────────────────────────────────────────────────────┤
│          better-sqlite3 (本地存储)                    │
│          Load-Modify-Save 集合模式                    │
└─────────────────────────────────────────────────────┘
```

## 核心架构模式

### 1. Chat 执行管线 (`enqueueSessionRun`)

所有聊天请求的唯一入口，经四层处理后执行：

1. **去重（Dedup）** — 相同 `dedupeKey` 的重复请求直接丢弃
2. **收集模式合并（Coalescing）** — 1500ms 窗口内的快速连续消息合并为单次调用
3. **心跳抢占（Preemption）** — 用户聊天中止正在运行的心跳轮次
4. **执行锁（Lock）** — 每个 session 同时只运行一个 turn，其余排队

### 2. Provider 注册表

23+ LLM 提供商统一注册在 `PROVIDERS` 映射中。绝大多数提供商（Google、DeepSeek、Groq、Together、Mistral、xAI、Fireworks、Nebius、DeepInfra 等）是 OpenAI 兼容的薄封装——仅修补 `apiEndpoint` 后委托给 `streamOpenAiChat`。非兼容提供商有独立流处理器：Anthropic、Ollama、OpenClaw Gateway。

此外还支持 CLI 类 Agent 工具集成：Claude CLI、Codex CLI、Gemini CLI、Copilot CLI、Cursor、Droid、Qwen Code、Goose 等共 10+ 个。

### 3. Connector 连接器体系

12+ 外部聊天渠道双向连接：

| 连接器 | 类型 |
|--------|------|
| Discord | 即时通讯/社区 |
| Slack | 企业协作 |
| Telegram | 即时通讯 |
| WhatsApp (Baileys) | 即时通讯 |
| Signal | 加密通讯 |
| Matrix | 去中心化通讯 |
| Microsoft Teams | 企业协作 |
| Google Chat | 企业协作 |
| Email (SMTP/IMAP) | 异步通讯 |
| BlueBubbles (iMessage) | 苹果生态 |
| OpenClaw Gateway | Agent 协议网关 |
| SwarmDock | Agent 任务分发 |

连接器管理器（`manager.ts`）统一处理入站/出站、重连、配对、策略、语音转写。

### 4. Agent 编排

```
Org Chart（组织图）
  └─ Agent（顶层）
       ├─ 委派（Delegation）→ 创建子任务，分配给其他 Agent
       ├─ 蜂群（Swarm）→ 多 Agent 协作完成目标
       └─ 子代理（Subagent）→ 同会话内嵌套调用
```

- **Agent 主循环** (`main-agent-loop.ts`) — 消息处理、工具调用、内部 token 过滤、状态管理
- **委派系统** (`delegation-jobs.ts`) — 跨 Agent 任务分发与结果收集
- **蜂群协作** (`agent-swarm-registration.ts`, `subagent-swarm.ts`) — 多 Agent 并行/串行协作
- **守护者机制** (`guardian.ts`) — 安全检查点

### 5. Mission（自主目标驱动运行）

Mission 封装一个 session 赋予其目标、预算和里程碑日志：

- **预算强制**：USD / Token / Turn / 挂钟时间四维上限，`enqueueSessionRun` 每次入队检查
- **调度器**：`runMissionScheduler()` 每分钟在心跳管线顶部运行，独立于活跃时间窗口
- **报表**：按 `reportSchedule` 定期生成进度报告
- **状态机**：`running` → `paused` → `completed` / `budget_exhausted`

### 6. 终端工具边界

三类工具会强制退出 Agent 循环，后续逻辑不会执行：

- `memory_write` — 记忆持久化后退出
- `durable_wait` — 阻塞等待外部输入时退出（如审批门）
- `context_compaction` — 上下文压缩后退出以重新启动

## 关键设计决策

| 决策 | 原因 |
|------|------|
| `hmrSingleton` 替代模块级 `const` | Next.js HMR 重执行模块会丢失状态，挂载到 `globalThis` 存活 |
| `setIfChanged` 替代 raw `set()` | API 返回新对象引用触发级联渲染，JSON 指纹比对跳过未变更写入 |
| `saveCollection()` 防批量删除守卫 | 防止保存部分数据集时意外清空整个集合 |
| OpenAI 兼容封装模式 | 避免为每个提供商重写流处理器，一个 `streamOpenAiChat` 覆盖 90% |
| `enqueueSessionRun` 单入口 | 统一去重/合并/抢占/锁逻辑，所有调用者走同一路径 |
| Balanced-brace walker + Zod 替代 Regex | LLM 输出中的内部标记（如 JSON side-channel）用结构化解析，Regex 在嵌套 JSON/多行载荷上会断裂 |
| Extensions 替代 Plugins | 已全面迁移命名，类型/目录/API 统一为 extensions |

## 部署模式

| 模式 | 命令 | 说明 |
|------|------|------|
| 桌面端 | 下载安装包 | Electron 包裹 Next.js standalone server |
| CLI | `npx @swarmclawai/swarmclaw` | 全局安装后 `swarmclaw` 命令启动 |
| Docker | `docker-compose up` | 含 sandbox-browser 镜像 |
| Fly.io | `fly deploy` | `fly.toml` 配置 |
| Railway | railway.json | 一键部署 |
| Render | render.yaml | 一键部署 |

桌面端 Electron 以 `ELECTRON_RUN_AS_NODE=1` 启动 standalone server 子进程，数据目录 `SWARMCLAW_HOME` 指向 OS app-data。

## UI/UX 哲学

- **渐进式披露** — 高级选项折叠在 `AdvancedSettingsSection` 后
- **智能默认值** — `setup-defaults.ts` 单一事实来源；`randomSoul()` 提供个性建议
- **上下文帮助** — `HintTip` (?) tooltip 组件；连接器配置 `FIELD_HINTS`
- **不卡住用户** — API key 直链获取地址；错误状态说明原因和下一步

## 最新动态（截至 2026-06-28）

> [!note] 定位清晰化：OpenClaw 生态的自托管多 agent 运行时
> SwarmClaw 2026-06 被 Enterprise DNA 等目录收录，定位明确为 **"为 OpenClaw 生态设计的自托管 AI agent 运行时"**，而非通用竞品。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| 定位 | 自托管 agent 运行时 | **明确绑定 OpenClaw 生态**（不是通用竞品）|
| 曝光 | 新项目 | Enterprise DNA / TrendShift / Hermes Atlas 收录 |
| 模型支持 | 23+ LLM | Anthropic / Ollama / Google / DeepSeek 等 |

### 生态信号
- **OpenClaw 深度集成**：Mission planning、多模型供应商、agent memory、MCP tools、schedules、delegation 一应俱全
- 被定位为 [[ruflo]]（通用 meta-harness）的**OpenClaw 专用替代**，而非直接竞品
- YouTube/Hermes Atlas 等出现专项介绍，社区认知度上升

### 仍待观察
- 相对 [[ruflo]]（53K+ stars）的生态规模差距
- OpenClaw 生态本身的增长能否带动 SwarmClaw

## 关联项目与生态

- [[openhuman-architecture]] — 类似的 Agent 运行时架构（Rust 核心）
- [[multica]] — AI 原生任务管理，Agent 编排方向相关
- [[a2a-protocol]] — Agent 互操作协议，SwarmClaw OpenClaw Gateway 可能对接
- [[ruflo]] — 竞品：48.9K⭐ 多 Agent 编排平台
- [[acp-protocol]] — 编辑器-Agent 通信协议，CLI Agent 集成相关
