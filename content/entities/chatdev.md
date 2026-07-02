---
title: ChatDev (DevAll)
created: 2026-06-01
updated: 2026-06-01
type: entity
tags: [ai, platform, product, project, active, marketplace]
sources:
  - ~/Projects/ChatDev (source code)
  - https://github.com/OpenBMB/ChatDev
  - https://arxiv.org/abs/2307.07924
confidence: high
---

# ChatDev (DevAll)

> 从"虚拟软件公司"演进为零代码多 Agent 编排平台。YAML 驱动图工作流引擎 + FastAPI 后端 + Vue 3 Web Console，45+ 预置工作流覆盖数据分析/3D 生成/深度研究/游戏开发等场景。清华 OpenBMB 团队，2023 年学术起源，Apache-2.0。

---

## 定位与演进

| 阶段 | 代号 | 定位 | 核心差异 |
|------|------|------|----------|
| v1.0 | ChatDev | **Virtual Software Company** — 角色扮演多 Agent 自动软件开发 | CEO/CTO/Programmer 等角色 seminar 协作，自动化设计→编码→测试→文档 |
| v2.0 | DevAll | **Zero-Code Multi-Agent Platform** — "Developing Everything" | YAML 配置驱动、零代码构建任意多 Agent 系统（不限于软件开发） |

> v1.0 是 v2.0 的范式基础和经典示例（`ChatDev_v1.yaml`）。v2.0 大幅泛化了编排能力。

## 核心架构

```
┌─────────────────────────────────────────────────────┐
│                    Vue 3 Web Console                 │
│         (Launch / Design / Schema / Logs)            │
├─────────────────────────────────────────────────────┤
│                  FastAPI Backend                     │
│  server/app.py → bootstrap → config_schema_router   │
│              ↓ WebSocket (实时进度)                   │
├─────────────────────────────────────────────────────┤
│               Graph Workflow Engine                  │
│  workflow/graph.py (GraphExecutor)                   │
│  ├─ GraphContext (图拓扑 + 配置)                      │
│  ├─ TopologyBuilder (DAG 构建)                       │
│  ├─ CycleManager (循环/环检测)                        │
│  ├─ GraphManager (节点管理)                           │
│  └─ Runtime (DagExecutionStrategy |                  │
│              CycleExecutionStrategy |                 │
│              MajorityVoteStrategy)                    │
├─────────────────────────────────────────────────────┤
│              Node Executor Layer                     │
│  runtime/node/executor/factory.py                    │
│  ├─ agent_executor    — LLM Agent (核心)             │
│  ├─ python_executor   — 代码执行                     │
│  ├─ literal_executor  — 静态值                       │
│  ├─ subgraph_executor — 子图嵌套                     │
│  ├─ human_executor    — 人在环                       │
│  ├─ loop_counter/timer — 循环控制                    │
│  └─ passthrough       — 透传                         │
├─────────────────────────────────────────────────────┤
│              Agent Capabilities                      │
│  runtime/node/agent/                                 │
│  ├─ memory/   — MemoryBase → MemoryFactory           │
│  │            (Simple / File / Mem0 / FAISS)         │
│  ├─ thinking/ — ThinkingManager (扩展推理)            │
│  ├─ providers/— LLM Provider (OpenAI / Google Genai) │
│  ├─ tool/     — MCP Tool + Function Calling           │
│  └─ skills/   — Agent 技能包                         │
├─────────────────────────────────────────────────────┤
│              Edge Layer                              │
│  runtime/edge/                                       │
│  ├─ conditions/  — 边条件工厂 (路由决策)              │
│  └─ processors/  — 边处理器 (消息变换)               │
├─────────────────────────────────────────────────────┤
│              Entity / Config Layer                   │
│  entity/                                             │
│  ├─ configs/ (Node, EdgeLink, AgentConfig...)        │
│  ├─ graph_config.py — GraphConfig 加载               │
│  └─ messages.py    — Message + MessageRole           │
└─────────────────────────────────────────────────────┘
```

## 数据流（单次工作流执行）

```
1. 用户输入 (CLI/Web) → run.py / runtime/sdk.py
2. YAML 加载 → check/check.py 校验 → GraphConfig
3. GraphContext 构建 → TopologyBuilder 解析节点/边
4. RuntimeBuilder 注入 → RuntimeContext (tools/functions/memory/logger)
5. GraphExecutor.execute_graph()
   ├─ DagExecutionStrategy: 拓扑排序 → 逐节点执行
   ├─ CycleExecutionStrategy: 环检测 → 迭代执行
   └─ MajorityVoteStrategy: 多路投票 → 结果归约
6. 每个节点 → NodeExecutorFactory 分发到具体 Executor
7. Agent 节点 → LLM Provider 调用 → Tool 执行 → Memory 读写
8. 边条件评估 → 路由到下一节点
9. 最终消息 → graph_context.final_message()
10. 结果归档 → WareHouse/{session}/
```

## 技术栈

| 层 | 技术 | 说明 |
|----|------|------|
| 后端 | Python 3.12, FastAPI 0.124 | Pydantic v2, uvicorn, WebSocket |
| 前端 | Vue 3, Vite | Web Console 可视化编辑/执行 |
| LLM | OpenAI SDK, Google Genai | 多 Provider 支持 |
| 向量 | FAISS (CPU), mem0ai | RAG + 长期记忆 |
| 工具 | MCP (Model Context Protocol) | 外部工具集成 |
| 配置 | YAML + JSON Schema | 零代码工作流定义 |
| 构建 | uv (Python), npm (Frontend) | Docker Compose 部署 |
| 许可 | Apache-2.0 | |

## 预置工作流（yaml_instance/）

| 类别 | 工作流 | 说明 |
|------|--------|------|
| **软件开发** | `ChatDev_v1.yaml` | 经典角色扮演自动开发（CEO→CTO→Programmer→...） |
| **数据分析** | `data_visualization_basic/enhanced_v2/v3.yaml` | CSV→可视化图表 |
| **3D 生成** | `blender_3d_builder_*.yaml`, `spring_3d.yaml` | Blender + 图片生成 3D 模型 |
| **深度研究** | `deep_research_v1.yaml` + subgraph | 多轮搜索→综合报告 |
| **游戏开发** | `GameDev_with_manager.yaml` | AI 生成完整游戏 |
| **通用推理** | `react.yaml`, `reflexion_product.yaml` | ReAct/Reflexion Agent 模式 |
| **多 Agent 协作** | `MACNet_v1.yaml`, `general_problem_solving_team.yaml` | 多 Agent 团队 |
| **Demos** | `demo_*.yaml` (20+) | 功能展示（MCP/记忆/循环/投票/子图/动态边...） |

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 零代码驱动 | YAML + JSON Schema | 降低用户门槛，可视化编辑 |
| 图执行引擎 | 自研 DAG Runtime | 支持环/循环/子图/投票，优于线性 Pipeline |
| 节点执行器 | Strategy Pattern | 7 种 Executor 可扩展，Agent/Python/Human 统一接口 |
| 边条件 | 工厂模式 | 可插拔条件评估 + 消息变换处理器 |
| 记忆系统 | 分层 (Global + Agent-level) | SimpleMemory / FileMemory / Mem0 / FAISS 多后端 |
| LLM 调用 | Provider 抽象 | OpenAI 兼容 + Google Genai，可扩展 |
| 工具系统 | MCP 原生 + Function Calling | 标准 MCP 协议 + 自定义 Python 函数 |
| 会话管理 | WareHouse 目录隔离 | 每次运行独立工作空间 + 附件存储 |

## 与同类项目对比

| 维度 | ChatDev (DevAll) | [[archon]] | [[agno]] | [[ruflo]] |
|------|-------------------|------------|----------|-----------|
| 核心定位 | 零代码多 Agent 平台 | AI 编码确定性编排 | 全栈 Agent SDK | 多 Agent 编排平台 |
| 配置方式 | YAML 图 | YAML DAG | Python code-first | 低代码 UI |
| 运行时 | Python 自研引擎 | Bun + TypeScript | Python 内置 | TypeScript |
| 前端 | Vue 3 Web Console | — | Agno OS (React) | Web UI |
| 学术背景 | ✅ arXiv 论文 | ❌ | ❌ | ❌ |
| MCP 支持 | ✅ 原生 | ✅ | ✅ | ✅ |
| 子图嵌套 | ✅ | ❌ | ✅ Workflow | ✅ |
| 循环/投票 | ✅ | ❌ | ✅ | ✅ |
| 开发语言 | Python | TypeScript | Python | TypeScript |

## 项目信息

| 项 | 值 |
|----|-----|
| GitHub | OpenBMB/ChatDev |
| 学术论文 | [Communicative Agents for Software Development (arXiv:2307.07924)](https://arxiv.org/abs/2307.07924) |
| SaaS 平台 | https://chatdev.modelbest.cn/ |
| 主要贡献者 | NA-Wen, zxrys, swugi, huatl98 |
| 团队 | 清华大学 OpenBMB |
| 初始发布 | 2023-06-30 |
| 公开发布 | 2023-08-28 |
| 2.0 重写 | ~2025 (DevAll) |
| 许可证 | Apache-2.0 |

## 设计权衡与局限

1. **YAML 锁定** — 零代码友好但复杂逻辑表达受限（无循环内条件分支的图灵完备表达）
2. **Python 3.12 独占** — `requires-python = ">=3.12,<3.13"` 严格锁定
3. **单进程执行** — 节点间无并行执行策略（与 [[archon]] 的 worktree 并行不同）
4. **记忆后端碎片** — 4 种记忆后端但无统一查询接口
5. **测试覆盖** — 测试目录存在但覆盖有限（5 个测试文件）
6. **前端紧耦合** — Vue 3 前端与后端 API 紧耦合，非独立 SDK 优先

---

**关联：** [[archon]] · [[claude-code-workflow]] · [[temporal]] · [[agno]] · [[ruflo]] · [[kagent]] · [[a2a-protocol]] · [[heuristic-learning]] · [[context-mode]] · [[codegraph]]
