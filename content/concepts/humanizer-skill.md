---
title: Humanizer Skill
created: 2026-05-16
updated: 2026-05-16
type: concept
tags: [ai-coding, prompt-engineering, agent, de-ai]
sources: [https://github.com/blader/humanizer]
confidence: high
---

# Humanizer Skill

> [[index|← Index]] | [[wechat-ai-writer-pipeline|→ 写作管线]]

## 概要

[blader/humanizer](https://github.com/blader/humanizer) ⭐19.1k — Claude Code / OpenCode 的纯 Markdown Skill，识别并消除文本中的 AI 生成痕迹。基于维基百科 [Wikipedia:Signs of AI writing](https://en.wikipedia.org/wiki/Wikipedia:Signs_of_AI_writing)。

**核心洞察：** "LLMs use statistical algorithms to guess what should come next. The result tends toward the most statistically likely result that applies to the widest variety of cases."

## 6 步流程

1. **识别** AI 模式
2. **改写** 问题段落
3. **保留含义** — 不改变核心信息
4. **保持语调** — 匹配目标语气
5. **注入灵魂** — 不只是删除坏模式，要主动注入人类特征
6. **反AI自检** — 问自己"这段哪里还像AI写的？"，再改一轮

## 29 种 AI 写作模式

### 内容模式（6个）

| # | 模式 | 典型词 | 问题 |
|---|------|--------|------|
| 1 | 夸大意义/遗产感 | stands as, testament, pivotal, evolving landscape | 无意义地拔高事物重要性 |
| 2 | 夸大知名度 | independent coverage, active social media | 列举来源但不给具体内容 |
| 3 | -ing 虚假深度 | highlighting, underscoring, symbolizing | 现在分词短语假装有分析 |
| 4 | 推广/广告腔 | boasts, vibrant, nestled, breathtaking | 无法保持中性语调 |
| 5 | 模糊归因/黄鼠狼词 | Industry reports, Experts argue | 引用模糊权威不指名 |
| 6 | 套路化"挑战与展望" | Despite challenges, Future Outlook | 每篇结尾都有的公式化段落 |

### 语言/语法模式（7个）

| # | 模式 | 典型词 |
|---|------|--------|
| 7 | AI 高频词 | actually, additionally, crucial, delve, landscape, tapestry, underscore |
| 8 | 回避 is/are | 用 serves as / stands as / boasts 替代简单系动词 |
| 9 | 负面平行 | Not only… but… / It's not just X, it's Y |
| 10 | 三段式滥用 | 强行把观点凑成三个 |
| 11 | 同义词循环 | protagonist → main character → central figure → hero（重复惩罚导致） |
| 12 | 虚假范围 | from X to Y 构造无意义的范围 |
| 13 | 被动语态 | 隐藏主语，省略行为人 |

### 风格模式（6个）

| # | 模式 |
|---|------|
| 14 | 破折号过多 — 模仿"有力"的销售式写作 |
| 15 | 过度加粗 **keyword** |
| 16 | 列表+粗体标题（`- **Title:** Description`） |
| 17 | 标题大写（Title Case In Headings） |
| 18 | emoji 装饰 🚀💡✅ |
| 19 | 弯引号（"…" 而非 "..."） |

### 交流模式（3个）

| # | 模式 | 典型词 |
|---|------|--------|
| 20 | AI 客套话 | I hope this helps!, Let me know, Here is a... |
| 21 | 知识截止免责 | as of [date], While details are limited... |
| 22 | 谄媚语气 | Great question!, You're absolutely right! |

### 填充/避险模式（7个）

| # | 模式 |
|---|------|
| 23 | 废话短语（In order to → To; Due to the fact that → Because） |
| 24 | 过度避险（could potentially possibly be argued that） |
| 25 | 空洞积极结尾（The future looks bright, Exciting times lie ahead） |
| 26 | 连字符词对（cross-functional, data-driven, end-to-end） |
| 27 | 伪权威修辞（The real question is, At its core, Fundamentally） |
| 28 | 路标式开场（Let's dive in, Here's what you need to know） |
| 29 | 碎片化标题（标题后跟一句废话作为"热身"） |

## "注入灵魂"原则

避免 AI 模式只是半份工作。没有灵魂的文字同样容易被识别。

**无灵魂写作特征：**
- 每句话长度和结构相同
- 没有观点，只有中性报道
- 不承认不确定性或矛盾感受
- 不使用第一人称
- 没有幽默、棱角、个性
- 读起来像维基百科或新闻稿

**如何注入灵魂：**
- **有观点** — 不要中性报道，要反应
- **变化节奏** — 短句、长句混搭
- **承认复杂** — 人有矛盾感受
- **用"我"** — 第一人称不丢人
- **允许一点乱** — 完美结构 = 算法
- **具体描述感受** — 不是"this is concerning"而是"there's something unsettling about agents churning away at 3am"

## Voice Calibration（语调校准）

如果提供了写作样本：
1. 分析样本的句子长度、用词水平、段首习惯、标点用法
2. 在改写中匹配样本语调，而非套用模板
3. 无样本时回退到默认行为

## 与 wechat-ai-writer 的整合

已将 29 模式整合进写作管线的三个 prompt 文件：
- `critic.md` — 真人感维度拆分为 10 个细粒度检测点
- `editor.md` — 去AI味专项检查从 5 步扩展为完整覆盖
- `writer.md` — 补充黑名单词表 + 新增写作约束

## 相关页面

- [[wechat-ai-writer-pipeline]] — 公众号 AI 写作管线
- [[oscar-research-methodology]] — OSCAR 调研五步法
