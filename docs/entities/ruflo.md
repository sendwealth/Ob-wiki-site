---
title: Ruflo — Multi-Agent AI Orchestration Platform
created: 2026-05-12
updated: 2026-06-28
type: entity
tags: [ai-coding, agent, multi-agent, swarm, claude-code, mcp-server, llm]
sources: [raw/ruflo/readme.md]
confidence: high
---

# Ruflo

> 48.9K⭐ | 由 Claude Flow 更名而来，100+ Agent 编排平台，MIT License

*GitHub: https://github.com/ruvnet/ruflo | Author: rUv (ruv.io) | Runtime: TypeScript + Rust WASM*

## Overview

Ruflo 是一个多 Agent AI 编排平台，专为 Claude Code 设计。核心能力：将 Claude Code 从单上下文编码助手升级为**协调的 Agent 群体**——共享记忆、从结果中学习、跨机器通信、可审计。

由 [rUv](https://ruv.io) 创建，底层由 [Cognitum.One](https://cognitum.one) agentic 架构驱动，运行超充能的 Rust AI 引擎、embeddings、记忆和插件系统。

**数据**: 48,907 ⭐ | 5,425 forks | TypeScript | 2025-06-02 创建 | 每日更新

## Key facts

- 100+ 专业 Agent（编码、测试、安全、文档、架构）(→ [[gstack]] 对比：18 个技能）
- 300+ MCP tools + 49 CLI 命令 + 32 插件
- 自学习记忆：HNSW 向量搜索，150x-12,500x 加速
- Agent Federation：跨机器/跨组织的零信任协作
- Web UI Beta: [flo.ruv.io](https://flo.ruv.io/) — 多模型聊天 + MCP 工具调用
- Goal Planner: [goal.ruv.io](https://goal.ruv.io/) — GOAP A* 规划器
- 多 LLM 提供商：Claude, GPT, Gemini, Cohere, Ollama

## 架构

```
User → Claude Code / CLI
        ↓
  Orchestration Layer (MCP Server, Router, 27 Hooks)
        ↓
  Swarm Coordination (Queen, Topology, Consensus)
        ↓
  100+ Specialized Agents
        ↓
  Memory & Learning (AgentDB, HNSW, SONA, ReasoningBank)
        ↓
  LLM Providers (Claude, GPT, Gemini, Cohere, Ollama)
        ↑
  Learning Loop ←────────────────────────────┘
```

## 核心能力

### Swarm Coordination（群体协调）
- 分层、Mesh、自适应拓扑 + 共识（Raft, Byzantine, Gossip）
- Queen-led 层级架构
- 智能任务路由（89% 准确率）

### Self-Learning Memory（自学习记忆）
- SONA 神经模式 + ReasoningBank + 轨迹学习
- HNSW 索引 AgentDB，亚毫秒检索
- AES-256-GCM 静态加密（RFE1 格式）

### Agent Federation（Agent 联邦）
- 跨安装 Agent 协作，零信任安全
- mTLS + ed25519 身份验证
- 14 类 PII 检测管线，自动脱敏
- 行为信任评分（0.4×成功 + 0.2×在线 + 0.2×威胁 + 0.2×完整性）
- 合规内置：HIPAA, SOC2, GDPR 审计轨迹

### 12 Background Workers
- audit, optimize, testgaps 等自动触发后台任务

## 32 插件生态

### 核心编排
| 插件 | 功能 |
|------|------|
| ruflo-core | 基础：服务器、健康检查、插件发现 |
| ruflo-swarm | 多 Agent 团队协调 |
| ruflo-autopilot | Agent 自主循环运行 |
| ruflo-workflows | 可复用多步任务模板 |
| ruflo-federation | 跨机器安全协作 |

### 记忆与知识
| 插件 | 功能 |
|------|------|
| ruflo-agentdb | 快速向量数据库 |
| ruflo-rag-memory | 混合搜索 + 图跳跃 + 多样性排名 |
| ruflo-rvf | 跨会话记忆保存恢复 |
| ruflo-ruvector | GPU 加速搜索 + Graph RAG + 103 工具 |
| ruflo-knowledge-graph | 实体关系图构建遍历 |

### 智能与学习
| 插件 | 功能 |
|------|------|
| ruflo-intelligence | 从成功中学习 |
| ruflo-daa | 动态 Agent 行为和认知模式 |
| ruflo-ruvllm | 本地 LLM（Ollama）+ 智能路由 |
| ruflo-goals | 目标分解 + 进度跟踪 |

### 代码质量
| 插件 | 功能 |
|------|------|
| ruflo-testgen | 自动生成缺失测试 |
| ruflo-browser | Playwright 浏览器自动化 |
| ruflo-jujutsu | Git diff 分析 + 风险评分 |
| ruflo-docs | 自动文档生成维护 |

### 安全合规
| 插件 | 功能 |
|------|------|
| ruflo-security-audit | 漏洞和 CVE 扫描 |
| ruflo-aidefense | Prompt 注入防御、PII 检测 |

## Claude Code 对比

| 能力 | Claude Code 独用 | + Ruflo |
|------|------------------|---------|
| Agent 协作 | 隔离，无共享上下文 | Swarm + 共享记忆 + 共识 |
| 协调 | 手动编排 | Queen-led 层级（Raft, Byzantine） |
| 记忆 | 仅会话内 | HNSW 向量记忆，亚毫秒检索 |
| 学习 | 静态行为 | SONA 自学习 + 模式匹配 |
| 任务路由 | 人工决定 | 智能路由（89% 准确率） |
| 后台任务 | 无 | 12 个自动触发 Worker |
| LLM | 仅 Anthropic | 5 提供商 + 故障转移 |
| 安全 | 标准 | CVE 加固 + AIDefense |

## 最新动态（截至 2026-06-28）

> [!note] 从"Claude Flow"正式更名 Ruflo，定位 enterprise meta-harness
> Ruflo v3.5.0（2026-02）是稳定里程碑，正式从 "Claude Flow" 更名。Star 数从原调研的 48.9K 涨到 **53K–62K**（不同来源口径），累计 **1,488+ releases**，保持几天一个 alpha 的节奏。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| Star | 48.9K | **53K–62K** |
| 版本 | 持续迭代 | **v3.5.0 稳定版**（2026-02）|
| 定位 | 多 Agent 编排平台 | **"leading agent meta-harness for Claude"**（enterprise 叙事）|
| Release 总数 | 每日更新 | **1,488+** |

### v3.5.0 核心特性
- **SPARC methodology** — 结构化 agent 协作方法论（企业级流程）
- **Hive-mind swarms** — 蜂群式多 agent 协作，深化原 Queen-led 层级
- **Adaptive memory + self-learning** — 记忆与学习闭环产品化
- **Consensus modes** — 多 agent 决策共识机制
- **Multi-provider + background workers** — 多 LLM 故障转移 + 后台任务持续运行

### 生态信号
- 被多份 2026 enterprise AI 指南列为"Claude Code 多 agent 编排首选"
- 与 [[gstack]] 的差异化更清晰：**Ruflo = 基础设施/meta-harness，gstack = 工作流/方法论**
- 社区讨论（#1666）聚焦"是否值得用"，反映从尝鲜进入务实评估阶段

### 仍待观察
- Federation（#1669）成熟度
- 300+ 工具的维护负担与质量一致性

## Counter-arguments & data gaps

- **复杂度高** — 300+ 工具、49 命令、32 插件，学习曲线陡峭
- **过度工程风险** — 对小项目可能过重
- **依赖 Claude Code 生态** — 核心价值绑定 Anthropic
- **Federation 尚未完全成熟** — issue #1669 标注为开发中
- **与 gstack 的定位差异** — Ruflo 偏基础设施/平台，gstack 偏工作流/方法论

See also: [[gstack]], [[heuristic-learning]], [[agentic-rag]]
