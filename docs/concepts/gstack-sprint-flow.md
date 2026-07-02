---
title: gstack 冲刺流程
created: 2026-05-11
updated: 2026-05-11
type: concept
tags: [ai-coding, agent, workflow, process]
sources: [raw/gstack-skills.md]
confidence: high
---

# gstack Sprint Flow

> Think → Plan → Build → Review → Test → Ship → Reflect，每个技能输出是下一个的输入

## Overview

gstack 的核心不是工具集合，而是一个**流程**。每个技能按冲刺顺序排列，前一步输出直接喂给下一步。一个完整冲刺（一个特性）约 30 分钟。关键突破：可并行跑 10-15 个冲刺。

## Phase 1: Think — `/office-hours`

YC 风格产品重构。用户说"日历简报应用"，Agent 回答"你其实在做一个个人参谋 AI"。

**6 个强制问题**:
1. 需求真实性 — 你能说出一个具体需要这个产品的人吗？
2. 现状替代 — 他们现在怎么解决？为什么不够好？
3. 绝望具体性 — 给我真实场景，不是假设
4. 最窄楔子 — 最小可行的第一版是什么？
5. 观察与惊喜 — 什么会让用户说"wow"？
6. 未来适配 — 这会过时吗？

**两种模式**: Startup（追问式） / Builder（生成式）
**输出**: 设计文档 → `~/.gstack/projects/`

## Phase 2: Plan — `/plan-*`

**CEO Review** — 找 10 星产品，4 种范围模式（Expansion / Selective / Hold / Reduction）

**Eng Review** — 架构、数据流、ASCII 图表、边界条件、测试矩阵。图表是关键——LLM 画图时假设无处藏身。
**输出**: 测试计划 → 被 `/qa` 自动读取

**Design Review** — 7 轮审计：信息架构、交互状态、用户旅程、AI Slop 风险、设计系统、响应式、未决定项。每轮 0-10 打分。

## Phase 3: Build

你自己写代码。gstack 不代替思考，让你思考更清楚。

## Phase 4: Review — `/review` + `/codex`

**Review** — 找 CI 通过但生产会炸的 bug：N+1 查询、竞态条件、信任边界、缺失索引。
**Codex** — OpenAI 第二意见：Review / Challenge（对抗）/ Consult。交叉分析找盲区互补。

## Phase 5: Test — `/qa`

Diff-aware（只测受影响页面）/ Full / Quick / Regression 四种模式。每次修复自动生成回归测试。

## Phase 6: Ship — `/ship` + `/land-and-deploy`

`/ship`: 同步 → 测试 → 覆盖率审计 → PR。无测试框架自动引导。
`/land-and-deploy`: 合并 → CI → 部署 → 生产验证。自动检测平台，出问题提供回滚。

## Phase 7: Reflect — `/retro`

团队感知周报：commits、LOC、测试比例、PR 大小、编码时段、热点文件、发布连续天数。

## 流程衔接

```
office-hours → design doc
  → plan-ceo-review → 审查后的 design doc
  → plan-eng-review → 测试计划 + 架构文档
  → plan-design-review → 设计完整的 plan
  → [编码]
  → review → 发现 + 修复
  → qa → 测试 + 回归测试
  → ship → PR
  → land-and-deploy → 生产验证
  → canary → 持续监控
  → retro → 周复盘
```

## Review Readiness Dashboard

在 `/ship` 之前显示所有审查状态。Eng Review 是唯一必选门控（可跳过）。CEO 和 Design 是信息性的。

See also: [[gstack]], [[heuristic-learning]]
