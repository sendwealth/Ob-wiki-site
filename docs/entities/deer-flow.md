---
title: DeerFlow（字节跳动开源 Super Agent Harness）
created: 2026-07-12
updated: 2026-07-12
type: entity
tags: [ai-agent, multi-agent, langgraph, super-agent, sandbox, open-source, byte-dance]
sources: ["https://github.com/bytedance/deer-flow", "https://mp.weixin.qq.com/s/zzxzluJ5Jwop2Pp320Hi9w"]
confidence: high
---

# DeerFlow（字节跳动开源 Super Agent Harness）

> [!summary] 一句话
> DeerFlow 是字节跳动开源的 **Super Agent Harness（超级智能体运行时）**：基于 **LangGraph + LangChain** 重写，编排 **子代理（sub-agents）+ 长期记忆（memory）+ 沙箱（sandbox）**，用**可扩展技能（skills）** 驱动，让 Agent 拥有真实执行环境去干"研究 / 写代码 / 出报告 / 做网页 / 生成幻灯片"等小时级长任务。本地仓库已克隆于 `~/Projects/deer-flow`（2.0 分支）。

> [!note] 2.0 是彻底重写
> DeerFlow 从「Deep Research 框架」演进为「Super Agent Harness」。2.0 与 1.x **无共同代码**（1.x 在 `main-1.x` 分支维护）。2026-02-28 v2 发布后登顶 GitHub Trending #1。

## 系统架构（三层服务 + 统一入口）

```
                    Nginx (Port 2026)  ← 统一反向代理入口
   ┌──────────────────────┼───────────────────────┐
   │                      │                       │
   ▼                      ▼                       ▼
LangGraph Server     Gateway API            Frontend
 (Port 2024)         (Port 8001)            (Port 3000)
 Agent 运行时        FastAPI REST           Next.js + React
 - lead_agent        - Models API           - Chat UI
 - Thread 管理        - MCP 配置            - 产物展示
 - SSE 流式           - Skills 管理
 - Checkpoint         - 文件上传 / 清理
                      - 产物 / 建议
```

- 路由：`/api/langgraph/*` → LangGraph，`/api/*` → Gateway，其余 → Frontend。
- 共享配置：`config.yaml`（models/tools/sandbox/summarization）+ `extensions_config.json`（MCP servers / skills 状态）。

## 核心模块（基于真实代码 `backend/packages/harness/deerflow/`）

### 1. Agent 运行时（LangGraph Server）
- 入口：`deerflow.agents.lead_agent:make_lead_agent`（`langgraph.json` 声明）。
- `lead_agent` 是唯一**主控 Agent**，负责分解任务、按需 spawn 子代理、汇总。
- 状态：`ThreadState` 继承 LangGraph `AgentState`，扩展 `sandbox / artifacts / thread_data / title / todos / viewed_images`。

### 2. Middleware 链（8+ 道，在 Agent 核心前依次执行）
顺序：`ThreadData → Uploads → Sandbox → Summarization → Title → TodoList(plan_mode) → ViewImage → Clarification`，外加 `LoopDetection / Memory / SubagentLimit / TokenUsage / ToolErrorHandling`（见 `lead_agent/agent.py` 与 `agents/middlewares/`）。
- **Summarization**：会话内主动压缩已完成子任务、把中间结果卸载到文件系统，防止上下文爆窗。
- **SubagentLimit**：限制子代理并发/数量，防止失控。
- **LoopDetection**：检测死循环。

### 3. 子代理（Sub-Agents）
- Lead Agent 可**动态 spawn** 子代理，各自拥有**隔离上下文**（看不到主/其他子代理上下文），带限定工具与终止条件，**尽可能并行**执行，回传结构化结果后由 lead 合成。
- 内置子代理（`subagents/builtins/`）：`general_purpose`（通用）、`bash_agent`（执行 shell）。`subagents/` 下含 `registry / executor / config` 实现注册与执行。
- 这正是 DeerFlow 处理"分钟→小时"级任务的核心机制。

### 4. 沙箱与文件系统（Sandbox & File System）
- 抽象 `SandboxProvider`：`LocalSandboxProvider`（直连，开发用，主机 bash 默认禁用）、`AioSandboxProvider`（Docker 隔离容器，生产用）；K8s 通过 provisioner 服务跑 pod。
- 每个 thread 独立数据目录（路径隔离），虚拟路径映射：
  - `/mnt/user-data/workspace` ← 工作区
  - `/mnt/user-data/uploads` ← 上传文件
  - `/mnt/user-data/outputs` ← 最终产物
  - `/mnt/skills` ← 技能目录
- "不是带工具的聊天机器人，而是**有真实执行环境的 Agent**"。

### 5. 技能系统（Skills）
- 标准 Agent Skill = 一个 `SKILL.md`（Markdown 定义工作流 + 最佳实践 + 资源引用），含 frontmatter（`name / description / allowed-tools`）。
- 目录：`skills/public/`（内置：research、report-generation、slide-creation、web-page、image-generation、pdf-processing、frontend-design…）与 `skills/custom/`（用户装，gitignored）。
- **渐进式加载**：仅在任务需要时才注入对应技能到 system prompt，保持上下文精简。可装 `.skill` 归档、可替换/组合成复合工作流。

### 6. 工具系统（Tools）
三类来源经 `get_available_tools()` 聚合：
- 内置（`tools/`）：`present_file / ask_clarification / view_image` 等；
- 配置项（`config.yaml`）：`web_search / web_fetch / bash / read_file / write_file / str_replace / ls`；
- MCP（`extensions_config.json`）：github、filesystem、postgres、brave-search、puppeteer…

### 7. 模型工厂（Model Factory）
- `models/factory.py`：`config.yaml` 声明模型 → `create_chat_model()` → `resolve_class()`（反射）→ LangChain 实例。
- 支持 OpenAI / Anthropic / DeepSeek / 任意 OpenAI 兼容 API；可标 `supports_thinking / supports_vision`。
- 官方推荐 Doubao-Seed-2.0-Code、DeepSeek v3.2、Kimi 2.5。

### 8. 长期记忆（Long-Term Memory）
- 跨会话持久化**用户画像 / 偏好 / 沉淀知识**（本地存储、用户可控），越用越懂你。
- `MemoryMiddleware` 在运行时注入；写入时**去重**避免无限累积。
- 配合 `ThreadState` 工作记忆 + Summarization 上下文压缩，构成"三层"记忆体验（注意：并非微信文所言的"知识图谱"，见下）。

### 9. IM 渠道（Channels）
- 无需公网 IP，自启动：`Telegram`（Bot API）/ `Slack`（Socket Mode）/ `Feishu·Lark`（WebSocket）/ `WeCom`（WebSocket）。
- 聊天命令：`/new /status /models /memory /help`。

### 10. 可观测与嵌入式
- Tracing：内置 **LangSmith** + **Langfuse**（可同时上报）。
- `DeerFlowClient` 嵌入式 Python 库：进程内直接调用，与 HTTP Gateway 同 schema（CI 用 `TestGatewayConformance` 校验）。

## 技术栈
- 后端：Python 3.12 + **LangGraph / LangChain**（`langgraph dev` 跑运行时）+ FastAPI（Gateway）+ uv 管理。
- 前端：Next.js 22+（React/TSX），pnpm。
- 沙箱：Docker / Kubernetes（provisioner）。
- 配置：YAML + JSON，热更新（后端按需重读 `config.yaml`，MCP 用 mtime 失效缓存）。
- 安全：默认仅监听 `127.0.0.1`；建议生产环境加 IP 白名单 / 认证网关 / 网络隔离（因具备系统命令执行能力）。

## ⚠️ 与微信文章（虾说AI实验室）描述的对照（关键纠偏）

微信文把 deer-flow 包装成"长时域 SuperAgent 框架"并列出"六大模块 + 74K Star"，**方向对、细节有夸大/错位**，对比真实代码：

| 维度 | 微信文章描述 | 真实代码（DeerFlow 2.0） |
|---|---|---|
| 定位 | "长时域 SuperAgent 框架" | 准确："super agent harness"，确为 SuperAgent 形态 ✅ |
| Star 数 | "74K+ Star，Fork 10K+" | **未核实的营销数字**；真实亮点是 2026-02-28 登顶 GitHub Trending #1 ⚠️ |
| 编排核心 | 自研"SuperAgent 编排层 / DAG" | 实为 **LangGraph** 编排（非自研 DAG 引擎）⚠️ |
| 消息网关 | "事件驱动通信层，支持同步/异步、广播、订阅" | 实为 **Gateway REST API + IM 渠道**，并非 pub/sub 消息总线 ⚠️ |
| 三层记忆 | "短期+长期**知识图谱**+工作记忆" | 长期记忆是**持久化档案/偏好/知识（本地存储）**，**无知识图谱**；靠 Summarization 压缩上下文 ⚠️ |
| 沙箱 | "Docker/K8s 容器化" | 准确：Local + Aio(Docker) + K8s provisioner ✅ |
| 技能市场 | "可插拔技能系统" | 准确：`SKILL.md` 渐进加载，可扩展/替换 ✅ |
| 子代理 | "研究/编码/创作代理并行" | 准确：lead 动态 spawn 子代理（general_purpose / bash_agent），隔离上下文并行 ✅ |

> [!tip] 学习收获
> 文章作为"概念科普"可用，但**做架构判断必须回到源码**。DeerFlow 真正的工程内核是 **LangGraph 编排 + Middleware 链 + 沙箱隔离 + 技能渐进加载**，而非它渲染的"自研调度 + 知识图谱 + 消息总线"。这与 [[superagent]] 概念里的"编排层/沙箱/记忆/子代理"主干一致，但实现层要打折扣。

## Wikilinks
- [[superagent]]
- [[a2a-protocol]]
- [[multica-loop-agent]]
- [[agentic-rag]]
- [[openshell]]
