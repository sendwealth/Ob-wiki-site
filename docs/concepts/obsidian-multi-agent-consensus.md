---
title: Obsidian多Agent共识中台工作法
created: 2026-06-21
updated: 2026-06-21
type: concept
tags: [yitang, ai, multi-agent, obsidian, agent-collaboration, knowledge-management, claude-code, codex]
sources: [raw/yitang/obsidian-multi-agent-rebecca-原文整理.md]
confidence: high
---

# Obsidian 多 Agent 共识中台工作法

> 一堂专家分享（睿贝卡Rebecca）：用 Obsidian 作为"共识中台"解决 Codex + Claude Code 多 Agent 协作时的认知不同步、历史稿污染、人格漂移问题。核心主张：**多 Agent 协作的瓶颈不在工具能力，而在共识**。

## 核心命题

> [!summary] 三层痛点，一个解法
> 人的 vibe coding 失控 + AI 自身失忆/幻觉/人格漂移 + 多 Agent 共识漂移——三层痛点最后都被同一套**外部记忆 + 显式规则**解掉。不要靠 Agent 的记忆力维持共识，要靠文档约束 Agent。

## 三层痛点诊断

| 层 | 痛点 | 根因 |
|---|---|---|
| **人的层** | vibe coding 越写越乱、方向漂移 | 缺少"我是谁、项目是什么"的锚点 |
| **AI 层** | 失忆、幻觉、同一问题两个答案、人格漂移 | 上下文压缩、无持久状态、模型升级 |
| **多 Agent 层** | Codex 认知 ≠ Claude Code 代码、旧稿当现行 | 无共享记忆、无 source of truth |

### 五条排查清单（90% 问题不在模型）

1. 这次会话里先让它读项目背景了吗？
2. 项目建在 Project 容器里，还是裸聊？
3. 这条原则只在你脑子里，还是写进文件了？
4. 你在用上周的对话上下文假设它还记得？
5. 模型换了吗？换后有没有重新让它读 Foundation？

## 三仓分离架构

| 仓库 | 职责 | 工具 |
|---|---|---|
| **项目主仓** | 代码、配置，Git 版本控制 | GitHub private repo |
| **运行仓** | 本地高频读写，跑代码 | 本地目录 |
| **Obsidian 仓** | 共识、知识、同步 | iCloud 同步 |

> 运行在运行仓，定义在项目仓，理解、沉淀与复用在 Obsidian。

### Obsidian vs Agent 原生 Project

| | Obsidian | Agent Project |
|---|---|---|
| 角色 | **source of truth** | **cache** |
| 时效 | 长期、结构化、可追溯 | 按工具就近、按会话就绪 |
| 版本 | 可版本控制、可对比改动 | 无法跨工具同步 |

工作流：Obsidian 写定 → 同步到 Agent Project → 每次会话第一句"先读 Foundation"

## 编号约定 + 固定动线

```
01-Projects/Invert-Bot/
├── 00-Foundation/              ← 底座认知，所有 Agent 必读
├── 10-Product-OS/              ← 产品/算法/卡片
├── 20-GTM-OS/                  ← 定位/增长/转化
├── 30-Compliance/              ← 合规边界
├── 40-Runtime-Map/             ← 三仓关系、备份、Git 策略
├── 90-MOC-Invert-OS.md         ← 项目总纲（项目地图）
└── 98-Historical-Document-Register.md  ← 历史文档登记
```

Agent 固定动线：`99-System 总纲 → 90-MOC → 00-Foundation → 按任务进 10-40`

## 三份核心文档

### 1. Foundation 文档（宪法）

只回答最底层、最稳定的问题：是什么 / 不是什么 / 为谁做 / 核心价值 / 模块关系。

> 不写战术、不写本周计划、不写临时 prompt。隐含规则：理解冲突时以这里为准。

### 2. MOC（Map of Content，地图）

告诉 Agent：项目有哪些大块、哪份是入口、进入某类任务走哪条线。本质是把"项目结构"变成可机读的索引。

### 3. Historical Register（历史档案登记）

防止"AI 拿旧稿当现行规则"。每份历史文档写明：日期、当时目的、当前状态、现在优先参考哪份。

> [!warning] 高频坑
> 新 Agent 最先扫到的是根目录旧稿（文件名前缀 1.0-），而不是深层路径的 Foundation。Register 显式标注"历史讨论稿"+重定向到新文档。旧稿不删（保留演化），通过登记表重定向入口。

## 同一主题三份文档拆分法

| 文档 | 层级 | 谁读 |
|---|---|---|
| `30-xxx-Strategy` | Why / What | Codex 讨论战略 |
| `40-xxx-Setup-Checklist` | How / Sequence | Claude Code 实际执行 |
| `50-xxx-Gate-Draft` | Boundary / Gate | 人检查边界 |

物理隔离——Codex 不会跑去做 gitignore，Claude Code 不会被战略原则带跑重新讨论已经定了的事。

## V1 → V3 成熟度模型

| 阶段 | 内容 | 效果 |
|---|---|---|
| **V1** | 一份 Foundation + 一个 Agent Project | 超越 80% 用户 |
| **V2** | 编号目录 + MOC + 多文档 | 多领域规则有序 |
| **V3** | 三仓分离 + Git + Historical Register | 多工具/多人/长周期 |

> [!warning] 不要跳级
> 不要为了"看起来专业"直接跳到 V3。V1 跑通的人比 V3 半吊子的人产出高得多。阶梯划分的是"结构复杂度"，不是"用不用 Obsidian"——从 V1 起 Obsidian 就是必须的。

### 对齐回写（所有版本必做）

```
和 Agent 在对话中达成新共识
  → 30 秒判断：临时灵感还是稳定原则？
  → 稳定原则 → 立刻写回 Foundation
  → 下次新会话 Agent 读 Foundation 时自动继承
```

> AI 不会记得，下周的你也不会记得。不做对齐回写，每次好对话都"白聊"。

## 三条核心工程原则

1. **模型可替换**：不绑定模型人格。框架稳定，模型可换
2. **最小工具集优先**：优先保留数据连接、结构化分析、Python 计算、卡片生成、合规过滤
3. **缓存与记忆优先于长上下文堆叠**：Obsidian 就是"长期记忆"，不需要把所有历史塞进 prompt

## 5 条工作习惯

1. **先建 Foundation，再写任何 Prompt**——没有 Foundation 的 Agent 协作 = 没有宪法的国家
2. **给项目写 MOC，阅读顺序前置**——不要假设 Agent 会自己找文档
3. **历史稿单独登记**——对抗 AI 拿旧稿当现行规则
4. **三仓分离**——别让 Obsidian 干运行的活
5. **同一主题拆 Why/How/Gate 三份**——Agent 各取所需，思路不互相污染

## 三层保护（备份）

| 层 | 工具 | 作用 |
|---|---|---|
| 同步层 | iCloud + Google Drive | 跨设备一致 |
| 版本层 | Git + private GitHub | 版本控制 |
| 快照层 | 定期只读时间戳压缩包 | 最后防线 |

> 同步不是备份，版本控制也不是备份。

## 与 Hermes 工作流的对照

| 文章做法 | Hermes 对应 |
|---|---|
| Foundation 文档 | AGENTS.md / SOUL.md / MEMORY.md |
| MOC | index.md |
| Historical Register | log.md + session_search |
| 对齐回写 | memory tool |
| Agent Project cache | Hermes skills + config |
| 三仓分离 | ~/clawd/（共识）+ ~/Projects/（运行）+ GitHub（版本） |

> [!note] 关键启示
> 我们当前的 ~/clawd/ 结构已经天然实现了这篇文章的 V2 级别。要补的：①给核心项目（如 truthverifier）写一份显式 Foundation 文档（"是什么/不是什么"）；②给历史决策建 Register，避免新 Agent 拿旧设计当现行。

## 相关页面

- [[superpowers]] — AI 编码 Agent 行为塑造技能（约束 Agent 的另一层机制）
- [[claude-code-workflow]] — Claude Code 多 Agent 编排引擎
- [[openhuman-architecture]] — OpenHuman 知识图谱与记忆系统设计
- [[loop-engineering]] — 循环工程（状态机 + 反馈回路 + 可观测性）
- [[skill-self-evolution]] — Skill 自进化闭环（技能作为可复用共识）
