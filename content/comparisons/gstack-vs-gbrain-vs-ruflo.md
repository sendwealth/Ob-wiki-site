---
title: Garry Tan AI 工具三件套对比
created: 2026-05-13
updated: 2026-05-13
type: comparison
tags: [ai-coding, agent, comparison, openclaw, claude-code]
sources: [raw/gstack/readme.md, raw/ruflo/readme.md, raw/gbrain/readme.md]
confidence: high
---

# gstack vs ruflo vs gbrain

> Garry Tan 两件 + rUv 一件，三个 Claude Code 增强平台的定位对比

## Overview

| 维度 | gstack | gbrain | ruflo |
|------|--------|--------|-------|
| **作者** | Garry Tan (YC CEO) | Garry Tan (YC CEO) | rUv (ruv.io) |
| ⭐ Stars | ~5K | 15.3K | 48.9K |
| **定位** | AI 软件工厂（工作流） | Agent 记忆系统（知识库） | 多 Agent 编排基础设施 |
| **一句话** | 18 人虚拟工程团队 | Agent 的大脑 | Agent 的神经系统 |
| **License** | MIT | MIT | MIT |

## 定位关系

```
                    ┌─────────────────────────────────┐
                    │         ruflo（编排层）           │
                    │  多 Agent 协调、Federation、自学习  │
                    └──────────┬──────────────────────┘
                               │
              ┌────────────────┼────────────────┐
              ▼                ▼                ▼
    ┌─────────────────┐ ┌──────────────┐ ┌──────────────┐
    │  gstack（编码）  │ │ gbrain（记忆）│ │  其他 Agent  │
    │ ship/review/QA  │ │ 摄入/丰富/查询│ │              │
    └─────────────────┘ └──────────────┘ └──────────────┘
              │                │
              └──── 互补 ──────┘
         gstack 编码前查 gbrain
         gbrain 运营用 gstack 技能
```

**gstack + gbrain = Garry Tan 的完整方案**：编码（gstack）+ 记忆（gbrain），有桥接层

## 功能对比

| 能力 | gstack | gbrain | ruflo |
|------|--------|--------|-------|
| **产品思维** | ✅ `/office-hours` | ❌ | ❌ |
| **工程规划** | ✅ `/plan-eng-review` | ❌ | `/ruflo-goals` |
| **设计系统** | ✅ `/design-consultation` | ❌ | ❌ |
| **代码审查** | ✅ `/review` + `/codex` | ❌ | `ruflo-jujutsu` |
| **QA 测试** | ✅ `/qa` 浏览器测试 | ❌ | `ruflo-testgen` |
| **发布部署** | ✅ `/ship` → `/land-and-deploy` | ❌ | ❌ |
| **知识图谱** | ❌ | ✅ 自布线 | `ruflo-knowledge-graph` |
| **持久记忆** | ❌ | ✅ PGLite + pgvector | ✅ HNSW AgentDB |
| **自学习** | ❌ | ✅ 梦境循环 | ✅ SONA |
| **后台任务** | ❌ | ✅ Minions | ✅ 12 Workers |
| **Agent 编排** | ❌ | ✅ sub-agent + DAG | ✅ Swarm + Federation |
| **多 LLM** | Claude + Codex | 14 种 Embedding | 5 提供商 |
| **语音** | ❌ | ✅ Twilio 语音 | ❌ |
| **Web UI** | ❌ | ❌ | ✅ flo.ruv.io |
| **联邦协作** | ❌ | ❌ | ✅ 零信任 Federation |

## 技术栈对比

| | gstack | gbrain | ruflo |
|---|--------|--------|-------|
| **运行时** | Bun + Chromium | Bun + PGLite/Postgres | TypeScript + Rust WASM |
| **存储** | 文件系统 | Postgres + pgvector | AgentDB + HNSW |
| **浏览器** | 持久化 Chromium daemon | 无 | Playwright 插件 |
| **MCP 工具** | 无 | 30+ | 300+ |
| **CLI 命令** | 无 | 49 | 49 |
| **插件** | 无 | 34 技能 | 32 插件 |

## 使用场景选择

**gstack 独用**: 一个人高效编码，结构化冲刺流程
**gbrain 独用**: 构建 Agent 长期记忆，知识管理，人物/公司追踪
**gstack + gbrain**: Garry Tan 推荐组合 — 编码 + 记忆，互相增强
**ruflo 独用**: 多 Agent 基础设施，跨团队协作，大规模 Agent 编排
**三者组合**: ruflo 编排 + gstack 编码 + gbrain 记忆 = 最强配置

## 学习价值

- **gstack** → 学工作流设计、冲刺流程、角色分工 (→ [[gstack-sprint-flow]])
- **gbrain** → 学知识建模、图谱构建、混合搜索、实体丰富
- **ruflo** → 学多 Agent 架构、Federation、自学习模式

See also: [[gstack]], [[gbrain]], [[ruflo]], [[gstack-sprint-flow]], [[gstack-browser-architecture]]
