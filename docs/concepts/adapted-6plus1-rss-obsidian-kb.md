---
title: ADAPTED 6+1 AI 知识库方法论（一堂·徐聪）
created: 2026-06-28
updated: 2026-06-28
type: concept
tags: [yitang, ai, knowledge-base, obsidian, rss, data-lifecycle, llm-wiki, methodology]
sources: [raw/yitang/adapted-6plus1-rss-obsidian-xucong-原文整理.md]
confidence: high
---

# ADAPTED 6+1 AI 知识库方法论（一堂·徐聪）

> 一堂专家分享（徐聪）：AI 时代数据有了 5 个新出口，数据管理需要全生命周期框架。用 **ADAPTED 6+1 模型**（预判-识别-收集-处理-使用-反馈+治理）贯穿数据从源头到价值落地全链路，落地工具是 **RSS（被动收获）+ Obsidian（仓库+处理）+ LLM Wiki（Karpathy 方案）**。两条核心认知：**①信息源质量是普通人学 AI 的 ROI 最高点；②log.md 不只是日志，是近期记忆+上下文压缩器+Lint 侦察地图+知识复利账本。**

## ADAPTED 6+1 模型

| 字母 | 阶段 | 核心问题 |
|---|---|---|
| **A**nticipate | 预判 | 数据将来服务哪个高频、高价值 AI 场景？频次够不够？独特性强不强？成本能不能接受？有无风险？ |
| **D**efine | 识别 | 这份材料让 AI 更懂事实？背景？风格？判断标准？还是什么不能做？ |
| **A**cquire | 收集 | 怎么阅读效率最高？如何在有限时间内获取更多数据？ |
| **P**rocess | 处理 | 给 AI 当上下文？进知识库？做评测题？当反馈样本？**处理深度由出口决定** |
| **T**ransform | 使用 | 这批数据最想让 AI 在哪个具体任务上稳定变好？ |
| **E**valuate | 反馈 | 结果评估，信息回流，形成反馈飞轮 |
| **D**iscipline | 治理 | 合规、权限、伦理、安全、长期治理 |

> 💡 预判的思维顺序：**我要让 AI 帮我干什么 → 需要什么材料 → 这些材料值不值得专门处理**（以终为始）。

## AI 时代数据新范式：3 不变 + 3 巨变

### 三不变

**① 深度不变（DIKW）**：数据→信息→知识→智慧 = 实事求是 + 解放思想的过程。注意 DIKW 之前还有**"第 0 步：数据源→数据"**，往往最耗时间（跨平台？质量？反爬？统一格式？）。知识→智慧的关键是**对抗惯性**——知识越多惯性越大，容易用老办法解新问题。

**② 流程不变（IPO）**：Input→Process→Output 始终成立。但 AI 时代绷紧"garbage in garbage out"——**不能只盯 OUTPUT 调提示词，要从源头优化 INPUT**。**信息源质量是普通人学 AI 的 ROI 最高点**：找领域最佳实践，躬身入局，PBL 自上而下快速入门。

**③ 目标不变（商业价值）**：收集/存储/处理/维护的代价能否被价值覆盖。中小团队最大成本是**人力成本**（标记/整理/维护/知识库搭建决定上限），要把时间尽量花在"信息→知识"而非"数据"层级。

### 三巨变

**① 出口巨变**（5 个新场景，是 AI 时代判断数据价值的新标准）：

| 出口 | 干什么 |
|---|---|
| AI 上下文 | 让模型更懂这次任务 |
| 知识库 / RAG | 让模型能检索你的私有材料 |
| 评测集 | 用来判断 AI 到底有没有变好 |
| 反馈库 | 记录 AI 的错答、人工修改、修改理由 |
| 工作流 / Agent | 让数据进入自动化执行链路 |

> 以前评估数据只问"准不准、全不全、格式好不好"；现在要追问：**这批数据最终让 AI 在哪个场景变好了？**

**② 形式巨变**：AI 时代新增 Prompt-Response 对话对、人工修改痕迹、失败案例、风格样例、过程记录（会议分歧/取舍理由）、多模态材料。能同时兼容传统 + AI 数据的工具只有飞书（多设备+协作）和 Obsidian（本地知识库）。

**③ 成本巨变**：转写/OCR/摘要/分类打标签/结构化/初筛清洗/标注萃取，以前很贵现在几乎免费。

## 落地：RSS + Obsidian + LLM Wiki

### A-Acquire 收集：主动获取 → 被动收获

核心思考：用**最少时间触及最多优质数据源**，由"主动获取"进化到"被动收获"。

| 方式 | 优势 | 劣势 |
|---|---|---|
| 每天更新的优质信息源（AIHOT 等） | 无脑收集、信息源上限高 | 无法定制、需额外存储 |
| Openclaw Skills 心跳定时获取 | 一定程度上可定制 | 反爬、依赖 Skills（维护成本高） |
| **RSS 定时刷新**（ROI 最高） | **定制化最高、可搭配仓库** | 学习成本较高、仍受反爬影响 |

工具栈：RSS 生成（RSSHub 最通用/weweRSS 公众号专用/Mp2RSS 公众号+X）、RSS 阅读器（FreshRSS/FeedMe）、浏览器插件（Obsidian Web Clipper/Bilibili Obsidian Clipper）、基础设施（WSL + Docker）。

### P-Process 处理：LLM Wiki（Karpathy 方案）

参考 Karpathy 的 LLM Wiki——先让 LLM 把书读完做笔记，有疑问翻笔记而非原书。

**双仓结构**（与 [[obsidian-multi-agent-consensus]] 三仓分离同源）：
- `raw/` — 原始素材（curated collection，事实来源，**LLM 只读不写**）
- `wiki/` — LLM 生成知识库（概念定义/实体页面/交叉引用/矛盾标注，含 `index.md`）
- `CLAUDE.md` — 知识库规则文件（schema）

**积累机制**：LLM 回答后把答案存回 `wiki/` 成新页面 → **知识库越来越厚，AI 越来越聪明**（但 Token 和维护成本递增）。

**三级加工深度**（由出口决定）：
- L1 粗加工：转写/卡片/转存/OCR
- L2 精加工：结构化（表格/标签）/向量化（Smart Connections 按主题拆分）
- L3 注灵魂：标注（正/反案例）/萃取（多源内容→指南/方法论/模型）

**检索流程（Ingest-Query-Lint）**：Ingest（新素材进 raw/，更新 wiki/+index）→ Query（查 index.md 定位，综合给答案）→ Lint（检查过时内容/孤儿页面/缺失交叉引用）。

> 💡 与本 Ob-wiki 的对应：`raw/`=原始素材、`concepts/`=wiki 页面、`SCHEMA.md`=CLAUDE.md、`index.md`=目录、`log.md`=时间索引。**本 wiki 自身就是 LLM Wiki 的实现。**

### T-Transform 使用：PARA + 卡片笔记法 + LLM Wiki

**PARA**（以行动为导向）：知识按"能帮做成什么"组织而非"是什么"。P(项目/有截止)→A(领域/无终点)→R(资源/暂无行动)→A(归档)逐级沉淀。
**卡片笔记法**三原则：原子化/关联优先/用自己的话写。
**三层组合**：PARA 层（导航）+ 卡片层（内容，原子化，可 RAG 检索 + 双向链接）+ LLM Wiki 层（检索）。

### E-Evaluate 反馈：log.md 的四重作用

全文最精妙的设计，也解释了 Ob-wiki 为什么坚持维护 log：

1. **LLM 的"近期记忆"** — INGEST 时读 log 避免重复，QUERY 时扫一眼了解最近变化
2. **"上下文窗口的压缩器"** — **index.md 是空间索引（东西在哪），log.md 是时间索引（发生了什么）**，两者结合用极少 Token 快速定位
3. **Lint 的"侦察地图"** — 逆向追踪概念何时、从哪份原始资料引入；反馈链 `log 暴露异常 → Lint 发现缺口 → 触发新 INGEST → log 记录`
4. **"知识复利"的账本**（Karpathy 核心概念 compounding）— 每条记录是"利息结算"；回顾 log 看知识库在成长还是堆积、哪些是核心节点、哪些是死知识

## 关联

- [[obsidian-multi-agent-consensus]] — 同属 Obsidian 知识库架构；本文的"raw/wiki 双仓 + CLAUDE.md schema + Lint"与睿贝卡的三仓分离/Foundation 文档/Historical Register 同源
- [[diary-to-book-skill]] — 同属"把日常数据变成知识资产"的闭环；本文的"5 个出口"对应姬恒的 L1-L5 数据转化引擎
- [[kecheng-to-ai-tool]] — 把方法论沉淀成可复用 AI 工具；本文的 ADAPTED 模型本身就是一个可操作框架
- [[content-growth-loop]] — 内容增长闭环；本文的 log.md 四重作用 + Ingest-Query-Lint 是"圆周运动/反馈飞轮"的具体实现
