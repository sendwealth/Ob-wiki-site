---
title: Ruflo 与 gstack 对比
created: 2026-05-12
updated: 2026-05-12
type: comparison
tags: [ai-coding, agent, comparison, claude-code]
sources: [raw/ruflo/readme.md, raw/gstack/readme.md]
confidence: high
---

# Ruflo vs gstack

> 两个 Claude Code 增强平台的全面对比：基础设施 vs 工作流

## Overview

| 维度 | Ruflo | gstack |
|------|-------|--------|
| **作者** | rUv (ruv.io) | Garry Tan (YC CEO) |
| ⭐ Stars | 48,900+ | ~5,000+ |
| **定位** | 多 Agent 编排基础设施 | AI 软件工厂工作流 |
| **理念** | Agent 自动协调、自学习、联邦 | 结构化冲刺流程、角色分工 |
| **语言** | TypeScript + Rust WASM | TypeScript + Bun |
| **License** | MIT | MIT |

## 架构对比

| | Ruflo | gstack |
|---|-------|--------|
| **核心** | MCP Server + Router + 27 Hooks | SKILL.md + 编译二进制 + Chromium daemon |
| **Agent 数** | 100+ 专业 Agent | 18 个技能角色 |
| **记忆** | HNSW 向量 DB + SONA 自学习 | 文件系统 + 设计文档 |
| **浏览器** | Playwright 插件 | 持久化 Chromium daemon (~100ms) |
| **LLM** | 5 提供商（Claude/GPT/Gemini/Cohere/Ollama） | Claude Code 为主 + Codex |
| **联邦** | 零信任跨机器协作 | 无 |

## 功能对比

| 能力 | Ruflo | gstack |
|------|-------|--------|
| 产品思维 | ❌ | ✅ `/office-hours` YC 风格重构 |
| 工程规划 | `/ruflo-goals` GOAP A* | `/plan-eng-review` ASCII 图表 |
| 设计系统 | ❌ | ✅ `/design-consultation` 完整系统 |
| 代码审查 | `ruflo-jujutsu` diff 分析 | `/review` + `/codex` 双模型 |
| QA 测试 | `ruflo-testgen` + `ruflo-browser` | `/qa` 真实浏览器 + 回归 |
| 安全审计 | `ruflo-security-audit` + AIDefense | `/careful` + `/guard` 命令预警 |
| 发布部署 | ❌ | ✅ `/ship` + `/land-and-deploy` |
| 持久记忆 | ✅ HNSW + 跨会话 | ❌ 文档即记忆 |
| 自学习 | ✅ SONA + ReasoningBank | ❌ |
| 后台任务 | ✅ 12 个 Worker | ❌ |
| 复盘 | ❌ | ✅ `/retro` 团队周报 |
| Web UI | ✅ flo.ruv.io | ❌ |

## 使用场景

**选 Ruflo 当**:
- 需要多 Agent 自动协作和自学习
- 跨团队/跨机器 Agent 通信
- 需要多 LLM 提供商故障转移
- 构建大型 Agent 基础设施

**选 gstack 当**:
- 一个人高效产出（日产万行代码）
- 需要产品思维和设计系统
- 重视结构化冲刺流程（Think→Plan→Build→Review→Ship）
- 快速上手，30 分钟出第一个完整特性

## 互补性

两者不互斥，可以组合使用：
- gstack 的 `/office-hours` + `/plan-*` 做产品规划和架构设计
- Ruflo 的 Swarm + Federation 做多 Agent 执行和跨团队协作
- gstack 的 `/review` + `/qa` + `/ship` 做质量控制和发布

See also: [[ruflo]], [[gstack]]
