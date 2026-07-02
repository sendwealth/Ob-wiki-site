---
title: GBrain — Garry Tan 的 AI Agent 记忆系统
created: 2026-05-13
updated: 2026-06-28
type: entity
tags: [ai-coding, agent, knowledge-graph, memory, openclaw, llm]
sources: [raw/gbrain/readme.md]
confidence: high
---

# GBrain

> 15.3K⭐ | Garry Tan 的 Agent Brain，17,888 页知识库 + 4,383 人 + 723 公司，12 天建成

*GitHub: https://github.com/garrytan/gbrain | Author: Garry Tan | Runtime: TypeScript + Bun + PGLite/Postgres*

## Overview

GBrain 是 Garry Tan 为 OpenClaw/Hermes Agent 构建的生产级记忆系统。核心理念：AI Agent 聪明但健忘，GBrain 给它一个大脑。

**生产数据**: Garry 的个人部署 — 17,888 页、4,383 人、723 公司、21 个 cron 任务自主运行。

**核心突破**: 知识图谱自动布线 — 每次写入自动提取实体引用并创建类型化链接（`attended`、`works_at`、`invested_in`、`founded`、`advises`），零 LLM 调用。

**检索性能**: P@5 49.1%, R@5 97.9%，比无图模式高 +31.4 points P@5。

## Key facts

- 34 个技能，安装 30 分钟 (→ [[gstack]] 对比：18 技能，安装 30 秒)
- 自布线知识图谱，类型化关系自动提取
- 混合搜索：Vector + Keyword + RRF Fusion + Multi-query Expansion + 4-layer Dedup
- PGLite 嵌入式 Postgres（零配置）→ Supabase 无缝迁移
- Minions 后台任务系统：753ms vs sub-agent 10s+ 超时
- 30+ MCP 工具，支持 Claude Code / Cursor / ChatGPT / Claude Desktop
- 14 种 Embedding 提供商配方（OpenAI、Voyage、Gemini、Zhipu、Ollama 等）
- OAuth 2.1 + 管理后台的 HTTP MCP 服务器

## 架构

```
┌──────────────────┐    ┌───────────────┐    ┌──────────────────┐
│   Brain Repo     │    │    GBrain     │    │    AI Agent      │
│   (git, Markdown)│───>│  Postgres +   │<──>│  34 skills       │
│   = source of    │    │  pgvector     │    │  RESOLVER.md     │
│     truth        │<───│  hybrid search│    │  routes intent   │
│   human can edit │    │  (vector +    │    │  to skill        │
│                  │    │   keyword +   │    │                  │
└──────────────────┘    │   RRF)        │    └──────────────────┘
                        └───────────────┘
```

**存储引擎**: PGLite（嵌入式 PG 17.5，零配置）→ Supabase（$25/mo，Postgres + pgvector）
**迁移**: `gbrain migrate --to supabase|pglite`（双向）

## 34 技能全览

### Always-on
| 技能 | 功能 |
|------|------|
| signal-detector | 每条消息触发，并行捕获原始思维 + 实体提及 |
| brain-ops | Brain-first 查找，读-丰富-写循环 |

### 内容摄入
| 技能 | 功能 |
|------|------|
| ingest | 路由器：检测输入类型 → 委派到对应摄入技能 |
| idea-ingest | 链接/文章/推文 → brain 页面 + 作者页面 + 交叉链接 |
| media-ingest | 视频/音频/PDF/书籍/截图/GitHub 仓库 |
| meeting-ingestion | 会议记录 → brain 页面，每个参会者自动丰富 |
| voice-note-ingest | 语音笔记逐字保存，路由到正确目录 |
| article-enrichment | 原始文章 → 结构化页面（摘要、引言、洞察） |

### 研究与综合 (v0.25.1)
| 技能 | 功能 |
|------|------|
| book-mirror | 🏅旗舰：书籍 → 个性化双栏章节分析（~$6/20章） |
| strategic-reading | 透镜式阅读：单一问题视角 → 应用 Playbook |
| concept-synthesis | 去重数千概念存根 → 分层智力地图 |
| perplexity-research | Brain 增强的网络研究 |
| archive-crawler | 个人文件归档通用处理器 |
| academic-verify | 研究声明追溯验证 |

### Brain 操作
| 技能 | 功能 |
|------|------|
| enrich | 分层丰富（T1/2/3），人物/公司页面自动升级 |
| query | 3 层搜索 + 综合 + 引用 |
| maintain | 健康检查：过期页面、孤立页、死链接、引用审计 |
| citation-fixer | 自动修复缺失/畸形引用 |
| repo-architecture | 新 brain 文件的存放决策协议 |

### 运营
| 技能 | 功能 |
|------|------|
| daily-task-manager | P0-P3 优先级任务管理 |
| daily-task-prep | 早间准备：日历预览 + brain 上下文 |
| cron-scheduler | 调度错开 + 安静时段 + 幂等性 |
| minion-orchestrator | 后台任务 DAG，shell jobs + LLM subagents |
| skillify | 10 步循环：失败 → 持久化技能 |
| soul-audit | 6 阶段面试生成 SOUL.md + USER.md |

## 知识模型

每页遵循"编译真相 + 时间线"模式：

```markdown
---
type: concept
title: Do Things That Don't Scale
tags: [startups, growth]
---
编译真相（当前最佳理解，新证据时重写）

---
- 2013-07-01: Published on paulgraham.com    ← 时间线（仅追加）
- 2024-11-15: Referenced in batch W25 kickoff
```

## 知识图谱

```
写入会议页面 → 提及 Alice 和 Acme AI
  → Auto-link 提取实体引用（零 LLM 调用）
  → 推断关系类型：
    "CEO of X" → works_at
    "invested in" → invested_in
    "founded" → founded
    "advises" → advises
    "attended" → attended
  → 对账过时链接
  → 反向链接提升排名
```

**实体自动升级**: 提及 1 次 → Tier 3 存根 → 3 次跨源 → Tier 2 Web 丰富 → 会议或 8+ 次 → Tier 1 完整管线

## Minions 后台任务系统

| 指标 | Minions | sub-agent |
|------|---------|-----------|
| 延迟 | **753ms** | >10,000ms（超时） |
| Token 成本 | **$0.00** | ~$0.03/run |
| 成功率 | **100%** | 0%（无法 spawn） |
| 内存/任务 | ~2 MB | ~80 MB |

**路由规则**: 确定性工作 → Minions；需要判断 → Sub-agents

## 搜索架构

```
Query
  → Intent classifier (entity? temporal? event? general?)
  → Multi-query expansion (Claude Haiku)
  → Vector (HNSW cosine) + Keyword (tsvector)
  → RRF fusion: score = sum(1/(60 + rank))
  → Cosine re-scoring + compiled truth boost
  → 4-layer dedup + compiled truth guarantee
  → Results
```

**~20 种确定性技术层叠**：递归分块、嵌入缓存、代码围栏剥离、类型推断级联、反向链接提升、意图分类器……

## 与 GStack 的关系

- **GStack** = 编码技能（ship, review, QA, investigate, office-hours, retro）
- **GBrain** = 记忆和运营技能（brain ops, signal detection, ingestion, enrichment, cron, reports）
- **hosts/gbrain.ts** = 桥接，告诉 GStack 编码前先查 brain

## 最新动态（截至 2026-06-28）

> [!note] 从"记忆系统"升级为"Agent 操作系统"，技能数 34 → 43
> 2026-04 正式开源后，GBrain 引入 **SkillPack** 概念和 **dream cycle**（记忆巩固），技能数从 34 增长到 **43**。Vectorize、MarkTechPost 等发布深度解析和实现教程。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| 技能数 | 34 | **43**（不同来源 34–43）|
| 新概念 | — | **SkillPack**（可移植技能包）+ **Dream Cycle**（记忆巩固）|
| 定位 | Agent 记忆系统 | **"Agent Brain / 操作系统"** |
| 架构 | Markdown + pgvector | **Markdown + Postgres/pgvector**（跨 10,000+ 文件混合搜索）|

### SkillPack —— 可移植技能包
> "A GBrain SkillPack is a portable bundle of skills, resolver triggers, deterministic scripts, and tests that you can install into any agent setup." —— Garry Tan

这是 GBrain 从"个人记忆系统"走向"生态平台"的关键——SkillPack 让其他人能打包并分发自己的技能组合，类似 Obsidian 的社区插件生态。

### Dream Cycle（梦境周期）
新增记忆巩固机制：Agent 在空闲时对记忆进行整理、关联、压缩，类比人类睡眠时的记忆巩固。这呼应了 [[automaton]] 的 SOUL.md 反思机制——都是让 agent 主动整理自我认知。

### 生态整合
- [[gstack]] v1.26.3.0 内置 `/sync-gbrain`，三件套（gstack + gbrain + graphify）正式闭环
- 被列为 2026 年五大 Agent 记忆系统之一（vs Mem0 / Zep / Letta / Cognee）
- Vectorize 等发布"GBrain 替代品"对比，侧面印证其已成为该品类标杆

### 仍待观察
- SkillPack 生态能否形成规模（目前主要 Tan 个人技能）
- 实体提取准确度对知识图谱质量的影响

## Counter-arguments & data gaps

- 安装复杂度较高（30 分钟 vs gstack 30 秒）
- 依赖 Postgres（PGLite 或 Supabase）
- 34 技能学习曲线陡峭
- 知识图谱质量依赖实体提取准确度
- 语音功能需 Twilio 额外付费

See also: [[gstack]], [[ruflo]], [[agentic-rag]]
