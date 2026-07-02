---
title: gstack — Garry Tan 的 AI 软件工厂
created: 2026-05-11
updated: 2026-06-28
type: entity
tags: [ai-coding, agent, llm, product, project]
sources: [raw/gstack-readme.md, raw/gstack-architecture.md, raw/gstack-skills.md]
confidence: high
---

# gstack

> Garry Tan (YC CEO) 的开源 AI 软件工厂，将 Claude Code 变为 18 人虚拟工程团队

*Local path: ~/clawd/gstack/ | Version: 0.9.9.0*

## Overview

gstack 是 Y Combinator CEO [Garry Tan](https://x.com/garrytan) 的开源软件工厂。他在 60 天内用 gstack 写了超过 60 万行生产代码（35% 是测试），日产 1-2 万行可用代码。

**核心理念**: 18 个专业角色 + 7 个安全工具，全部以斜杠命令呈现。按冲刺流程排列：Think → Plan → Build → Review → Test → Ship → Reflect。

一个完整特性冲刺约 30 分钟，可并行 10-15 个特性分支。

**GitHub**: https://github.com/garrytan/gstack
**License**: MIT

## Key facts

- 日产 1-2 万行生产代码，60 天写了 60 万行 (→ [[heuristic-learning]] 学习范式)
- 18 个专业技能按冲刺流程排列
- 持久化浏览器架构，~100ms/命令响应（Bun + Chromium daemon）
- 支持 Claude Code、Codex、Gemini CLI、Cursor 等多 Agent
- 完整测试体系：静态验证 + E2E + LLM-as-judge
- Greptile 集成：自动 PR 审查分类

## 技能全览

### 思考与规划
| 技能 | 角色 | 核心能力 |
|------|------|----------|
| `/office-hours` | YC 合伙人 | 6 个强制问题重构产品定义，Startup/Builder 双模式 |
| `/plan-ceo-review` | CEO/创始人 | 找到请求中的 10 星产品，4 种范围模式 |
| `/plan-eng-review` | 工程经理 | 架构、数据流、ASCII 图表、边界条件、测试矩阵 |
| `/plan-design-review` | 高级设计师 | 7 轮设计审计，0-10 打分，AI Slop 检测 |

### 设计
| 技能 | 角色 | 核心能力 |
|------|------|----------|
| `/design-consultation` | 设计搭档 | 从零构建完整设计系统，竞品分析，交互式预览 |
| `/design-review` | 会编码的设计师 | 80 项视觉审计 + 修复循环，AI Slop 评分 |

### 审查与测试
| 技能 | 角色 | 核心能力 |
|------|------|----------|
| `/review` | Staff 工程师 | 找 CI 漏掉的 bug，自动修复，完整性缺口检测 |
| `/investigate` | 调试专家 | 根因分析铁律：不调查不修复，3 次失败停手 |
| `/qa` | QA 主管 | 真实浏览器测试，Diff 感知，自动回归测试 |
| `/codex` | 第二意见 | OpenAI Codex 独立审查，对抗模式，交叉分析 |

### 发布与监控
| 技能 | 角色 | 核心能力 |
|------|------|----------|
| `/ship` | 发布工程师 | 同步、测试、覆盖率审计、PR |
| `/land-and-deploy` | 发布工程师 | 合并 PR → CI → 部署 → 生产验证 |
| `/canary` | SRE | 部署后监控 |
| `/benchmark` | 性能工程师 | Core Web Vitals 对比 |
| `/document-release` | 技术写手 | 交叉对比 diff 更新所有文档 |
| `/retro` | 工程经理 | 团队感知周报，每人指标 + 成长建议 |

### 浏览器与安全
| 技能 | 角色 |
|------|------|
| `/browse` | 持久化 Chromium，真实点击/截图 |
| `/setup-browser-cookies` | 从 Chrome/Arc/Brave/Edge 导入 Cookie |
| `/careful` | 危险命令预警 |
| `/freeze` | 编辑锁定到单一目录 |
| `/guard` | careful + freeze 组合 |
| `/unfreeze` | 解除锁定 |
| `/gstack-upgrade` | 自更新 |

## 技术架构

### 浏览器系统
- **Bun + Chromium daemon** — 编译二进制 ~58MB，无 node_modules
- **Ref 系统** — `@e1`/`@c1` 引用元素，基于 ARIA tree + Playwright Locator
- **安全模型** — localhost only + Bearer token + Cookie Keychain 解密
- **日志** — 三个 50K 环形缓冲区，异步刷盘

### 构建系统
- SKILL.md 模板系统：从源码自动生成文档
- 测试三层：静态验证(免费) → E2E(~$3.85) → LLM-as-judge(~$0.15)
- 可观测性：heartbeat + partial 结果 + 非致命原则

## 最新动态（截至 2026-06-28）

> [!note] 爆发式增长：从"个人 skill 包"到现象级项目
> 2026-03 发布后，gstack 在 11 天冲到 39K stars，6 周达 85K，目前约 **66–89.7K stars**（不同来源口径差异）。Garry Tan 自称 60 天写了 60 万行代码（HN 上有争议）。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| 定位 | 18 人虚拟工程团队 | **23 opinionated roles**（CEO/Designer/Eng Manager/Release Manager/Doc Engineer 等）|
| 版本 | v0.9.9.0 | **v1.26.3.0**（2026-05-04）|
| 新增能力 | — | `/sync-gbrain` skill、native code-surface orchestrator |
| Star | 18K 区间 | **66K–89.7K** |

### 生态整合
- 与 [[gbrain]] 双向打通：gstack v1.26.3.0 内置 `/sync-gbrain`，编码前先查 brain 记忆
- 成为 Garry Tan "AI 软件工厂"三件套（gstack + [[gbrain]] + [[graphify]]）的核心编排层
- 被多份 2026 评测作为"solo founder 用 AI 当全栈团队"的标杆案例

### 仍待观察
- "60 万行代码"的产出质量争议（HN 社区质疑含模板/生成代码）
- 强 opinionated 设计对非 Tan 风格团队可能水土不服

## Counter-arguments & data gaps

- iframe 支持缺失（最受请求的功能）
- 仅 macOS Cookie 解密
- 无 WebSocket 流式传输
- 依赖 Claude Code 生态，其他 Agent 支持可能不完整

See also: [[heuristic-learning]], [[context-mode]]
