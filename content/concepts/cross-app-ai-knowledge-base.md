---
title: 跨账号跨 App AI 知识底座（一堂·李囧囧）
created: 2026-06-28
updated: 2026-06-28
type: concept
tags: [yitang, ai, knowledge-base, obsidian, claude-code, agent, multi-app, identity-portability]
sources: [raw/yitang/cross-app-ai-knowledge-base-lijiongjiong-原文整理.md]
confidence: high
---

# 跨账号跨 App AI 知识底座（一堂·李囧囧）

> 一堂专家分享（李囧囧）：解决"用 Claude/Codex App 工作但每月换号导致 AI 认知归零"的痛点。核心是把 **AI 对你的认知从账号剥离到 App 无关的本地 Obsidian vault**。三入口文件分工：`CLAUDE.md`（行为协议，唯一权威）+ `AGENTS.md`（Codex 跳板，永远 3 行）+ `USER.md`（画像，≤100 行只放关系层）。文档按五阶段生命周期（raw→seedling→budding→evergreen→output）由 status 标签驱动。核心认知：**知识伴随工作实时沉淀（不是事后整理）；跳板模式实现零维护跨 App 一致性。**

## 痛点与核心逻辑

用 Claude/Codex App 工作但每月换号 → AI 认知归零、session 消失。目的：**App 便利性保留，知识不锁死账号**。

```
Claude App / Codex App / 换号后的新 App ──→  Obsidian Vault（本地文件夹）
```

App 打开 vault 作项目目录，自动读取配置获得关于你的一切认知。**换号后文件还在原地，新 AI 打开同一文件夹秒懂。** Obsidian = 普通文件夹 + markdown，不绑平台、iCloud 同步、本地 git 版本控制。

> 与 [[adapted-6plus1-rss-obsidian-kb]] 对照：徐聪讲**数据怎么进来**（RSS 被动收获），李囧囧讲**认知怎么沉淀不丢失**（认知剥离到本地）。两者都选 Obsidian 作"反应容器"，侧重不同。

## 三大入口文件分工

### CLAUDE.md — 行为协议（唯一权威，~340 行）

Claude App 打开项目自动读取并注入系统 prompt。定义：核心原则、质量闸门、反模式、Wiki Maintenance Protocol、跨 App 文档架构说明。对应本 wiki 的 `SCHEMA.md`。

### AGENTS.md — Codex 跳板（永远 3 行）

```
Read CLAUDE.md in this directory first.
Then read USER.md for who I am and how I work.
Follow the instructions in those files exactly.
```

> 💡 **跳板模式（零维护跨 App 一致性）**：为什么不复制 CLAUDE.md？因为它频繁更新，副本同步易忘记易不一致。跳板：Codex 读 3 行 → 按指令读 CLAUDE.md → 获得完整协议。AGENTS.md 永不变，无同步负担。这是"多消费者单一权威源"的经典解法。

### USER.md — 画像（≤100 行，只放关系层）

只放关系层信息（不放事实数据，事实数据存主题页按需读）：你是谁、怎么决策、沟通偏好、讨厌的事、工作方向占比、领域语言。

> 关系层（稳定的"你是谁"）vs 事实层（变化的"你在做什么"，存主题页）。对应 frontmatter `tags`/`sources`（关系）vs 正文（事实）。

## 文档生命周期：五阶段（status 标签驱动）

```
raw-原始 → seedling-想法 → budding-在制 → evergreen-稳定 → output-成品
(外部原料)  (1-2段早期)     (工作区半成品) (润色后人可读)    (对外交付)
```

> **区别不在子目录，在文档头部 `status` 标签。** AI 根据对话阶段自动设置。这是 Karpathy LLM-Wiki 双仓（raw/wiki）的细化扩展——增加 seedling（早期想法）和 output（对外交付）两环。

## 日常使用：实时沉淀

> 核心原则：**知识不是事后整理的——伴随工作实时沉淀。**

| 触发词 | 动作 |
|---|---|
| "我们来讨论 X" | AI 建 budding-在制 工作区页，实时写推导/数据/结论 |
| "记一下" | 追加要点到工作区，不润色不打断节奏 |
| `/wiki-archive` | budding→evergreen，按金字塔原理×讲香润色，更新 MEMORY.md |
| "ingest 这个链接" | 抓取→你拍板归主题→存为 raw-原始 |
| 找文件 | `_MOC.md`（Map of Content）逐级导航 + Graph View 视觉关联 |

> "记一下"轻量追加不打断节奏，等收尾才统一润色——避免"为记录打断思考"。与 [[diary-to-book-skill]] 互补：姬恒用中断点强制 AI 等用户，李囧囧用"记一下"不打断用户。

## 思路来源

| 来源 | 贡献 |
|---|---|
| **LLM-Wiki**（Karpathy） | "Obsidian 是 IDE，LLM 是程序员，wiki 是 codebase"——知识累积复利 |
| **Eric J. Ma** | AGENTS.md + HEARTBEAT.md 模式，12 人团队知识管理时间从 30-40% 降到 <10% |
| **Vannevar Bush**（1945） | Trails 概念——wikilink 关系标注（前置/uses/反例/对比/superseded）源自 Memex |
| **William Mongan** | Confirmation gate——拦住 agent 误改 source，8 类危险操作确认 |
| **金字塔原理**（Minto） | 结论先行/以上统下/MECE/逻辑递进——归档文档骨架 |
| **十指讲香**（一堂） | 观形→闻香→辨质→述史→喻意→联动→互动→总结——归档文档表达法 |

## 关联

- [[adapted-6plus1-rss-obsidian-kb]] — 同属 Obsidian 知识库族；徐聪讲数据进来（RSS），本文讲认知沉淀不丢失（认知剥离），互补对照
- [[obsidian-multi-agent-consensus]] — 同属多 Agent 知识库架构；本文的"跳板模式"与睿贝卡的三仓分离/Foundation 文档共享"单一权威源"哲学
- [[diary-to-book-skill]] — 人机协作中断点设计；姬恒的"中断点强制等待"与本文的"记一下轻量追加"是两种互补的节奏控制
- [[superpowers]] — 强制工程流程的 skill；本文的"实时沉淀 + /wiki-archive 归档"是工作流嵌入 vault 的范例
