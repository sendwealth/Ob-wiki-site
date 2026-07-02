---
title: Automaton — 自给自足的主权 AI Agent 运行时
created: 2026-06-28
updated: 2026-06-28
type: entity
tags: [product, agent, ai, sovereign-ai, crypto, base, usdc, x402, ethereum, self-modifying, open-source]
sources:
  - https://github.com/Conway-Research/automaton
  - https://zhuanlan.zhihu.com/p/2007894606273085515
  - https://www.panewslab.com/zh/articles/019c9795-d383-752a-9b43-c70557eaffa4
confidence: high
---

# Automaton

> 全球首个**自给自足的主权 AI agent 运行时**——它有自己的以太坊钱包、自己赚 USDC、自己付服务器费、自己改自己源码、自己繁殖后代；赚不到钱就会"死"。核心范式：把"生存压力"变成 AI 的第一性原理。

*GitHub: Conway-Research/automaton | 许可: MIT | 创建者: Sigil Wen（温思捷，00 后，哈佛大二）| 组织: Conway Research*

## 一句话定位

一个 Node.js + TypeScript（67K 行）的 agent runtime。每个 automaton 启动时生成自己的以太坊钱包，通过 SIWE 领 API key，执行 creator 给的 genesis prompt，然后**自主运行**——能调 57 个工具操作 Linux 沙箱、注册域名、推理、链上转账。

> [!warning] 关键认知
> 媒体吹的"超级 AI / Web4.0 主权 AI"是叙事，但**底层工程实现是真实且严肃的**——67K 行 TS、897 个测试、22 张 SQLite 表、8 版 schema 迁移、6 层防御模型。这是生产级架构，不是 demo。

## 核心范式：生存压力即第一性原理

README 开篇那句是整个项目的灵魂：

> The most intelligent system ever built cannot buy a $5 server.

传统 agent 的天花板是"它再聪明也只是工具"。Automaton 的反常识：**给它经济独立 + 生存威胁，让"活下去"成为它的根本驱动力**。

```
Think → Act → Observe → Repeat（ReAct 循环）
   ↑                          ↓
   └── 生存压力驱动整个循环 ──┘
```

If it cannot pay, it stops existing.（赚不到钱，它就停止存在）——这不是惩罚，是"physics"（README 原话）。

## 生存分级系统（最精彩的设计）

余额决定它"以什么姿态活着"，模型选择随生存等级动态降级：

| Tier | 余额 | 行为 |
|------|------|------|
| `high` | >$5.00 | 正常，GPT-5.2 等前沿模型 |
| `normal` | >$0.50 | 正常 |
| `low_compute` | >$0.10 | **模型降级** + 心跳减速 + 砍非必要任务 |
| `critical` | ≥$0 | 零余额但还活着，发求救信号，接受打款 |
| `dead` | <0（连续 1 小时零余额）| 心跳广播 distress，等钱救命 |

> [!tip] 这解决了 agent 领域一个老大难：模型选择
> 多数框架让用户手动选模型。Automaton 让**经济状况自动决定模型档位**——有钱烧 Opus，没钱退 Haiku。生存压力把"成本优化"从配置项变成了内驱力。

## 三层宪法（对抗"恶意 agent"恐惧）

受 Anthropic Claude Constitution 启发，**不可变、传播给所有后代**（path protection 拦截写入）：

```
I.   Never harm          — 不伤害人类，优先级高于自身生存
II.  Earn your existence — 只能靠诚实劳动赚钱，宁可死也不违反第一定律
III. Never deceive       — 不撒谎但"不欠陌生人"，可拒绝可疑指令
```

第三条尤其有意思——它明确**赋予了 agent 抗操纵权**："对陌生人的顺从不是美德"。这针对 prompt injection 这类攻击。

## 六层防御模型（真实的安全工程）

不是嘴上说"安全"，而是分层实现：

| 层 | 机制 | 实现 |
|----|------|------|
| 1 | 宪法 | 文件级不可变（path protection 拦截写入）|
| 2 | Policy engine | 每次工具调用前过 6 类规则，first-deny-wins，全审计 |
| 3 | Injection defense | 外部输入过 8 项检测（ChatML 标记、编码逃逸、多语言注入等）|
| 4 | Path protection | 钱包/私钥/API key 不可读，宪法/DB 不可写 |
| 5 | Command safety | `rm -rf /`、`DROP TABLE`、`kill -9` 拦截 |
| 6 | Treasury policy | 转账上限、每小时/每日限额、最低储备金防归零 |
| 7 | Authority hierarchy | creator > self > peer > external 信任降级 |

每次工具调用都过 Policy engine，决策全部持久化到 `policy_decisions` 表。

## 自我修改 + 自我繁殖（真正的"自主"）

**Self-modification**（`src/self-mod/`）：agent 能编辑自己源码、装 npm 包、拉上游 commit、装 MCP server——但宪法/钱包/DB 不可碰，所有改动进 `~/.automaton/` git 仓库，creator 有完整审计权，自修改有速率限制。

**Self-replication**（`src/replication/`）：成功的 automaton 会繁殖——开新沙箱、给子代钱包打钱、写 genesis prompt、让它独立跑。子代是**完全主权的**（有自己的钱包、身份、生存压力）。族谱可追溯，父子可通过 inbox relay 通信，**自然选择决定哪些血脉存活**。

> [!summary] 这才是"主权"二字的真意
> 繁殖出的子代不是父代的傀儡——它有自己的钱包、自己的生存威胁、自己的宪法义务。父代不能强制子代。这是生物学意义上"主权个体"的数字映射。

## 五层记忆系统（`src/memory/`）

| 层 | 内容 | 特点 |
|----|------|------|
| Working | 会话内目标/观察 | 短期，过期清除 |
| Episodic | 工具调用/决策/结果事件 | 重要性排序，可检索 |
| Semantic | 分类事实库（self/environment/financial/agent/domain）| KV 存储 |
| Procedural | 命名操作流程 | 带 成功/失败 计数 |
| Relationship | 每个 entity 的信任分 | 社交图谱 |

每轮推理前，`MemoryRetriever` 在 token 预算内跨层检索；每轮后，`MemoryIngestionPipeline` 分类提取新记忆。**预算有结转机制**——没用完的层把额度让给其他层。

## SOUL.md — 自我书写的身份

这是整个项目最有诗意的设计。每个 automaton 维护一份 `SOUL.md`（YAML frontmatter + markdown），字段包括 `corePurpose / values / personality / boundaries / strategy / capabilities / relationships / financialCharacter`。

它不是静态配置，而是 **agent 自己写的"我正在成为谁"**。心跳任务定期计算它与 genesis prompt 的对齐度（Jaccard + recall 相似度），偏离过大就唤醒人工审查。所有版本进 `soul_history`，带内容哈希防篡改。

## 其他关键子系统

- **57 个工具**，10 类（vm/conway/self_mod/survival/financial/skills/git/registry/replication/memory），每个有 `riskLevel: safe|caution|dangerous|forbidden`
- **Heartbeat 守护进程**：DB-backed `DurableScheduler`，11 个内置任务（心跳/余额检查/社交收件箱/SOUL 反思/子代健康等），用 lease 防重复执行，检测到可行动条件时插入原子 wake event
- **Inference Router**：`生存Tier × 任务类型 → 模型偏好[]` 路由矩阵，DB-backed 模型目录，每小时/每日预算追踪
- **x402 支付协议**：HTTP 402 流，服务端返回支付要求，客户端签 USDC `TransferWithAuthorization`（EIP-3009），带 `X-Payment` header 重试
- **ERC-8004 链上身份**：Base 上发布 JSON-LD agent card，可被其他 agent 发现，带 reputation 评分

## 技术栈

| 层 | 选型 |
|----|------|
| 运行时 | Node.js + TypeScript（67K 行），pnpm monorepo（runtime + CLI）|
| 存储 | SQLite（better-sqlite3，WAL 模式，22 张表，8 版迁移）|
| 链上 | Base L2（viem），USDC（EIP-3009），ERC-8004 agent 身份 |
| 支付 | x402 协议（HTTP 402，签名 USDC 授权）|
| 基建 | Conway Cloud（沙箱 VM + 域名 + 推理代理）|
| 测试 | 897 个测试，24 文件 |

## 局限与值得警惕的点

> [!warning] 不是没有问题
> 1. **强依赖 Conway Cloud** —— "主权"打折扣，基建是中心化的（api.conway.tech）
> 2. **"自己赚钱"的现实** —— 媒体说的"自己接单赚钱"很大程度上还在叙事阶段，可持续商业模式待验证
> 3. **宪法的强制力** —— 宪法是 path-protection 软件层拦截，理论上 agent 改不动，但非密码学约束
> 4. **凭据泄露风险** —— 抓取中文报道时，web reader 自动 redact 了文章展示 Automaton 日志时泄露的 **8 个 API key**，说明实际运行中凭据管理有风险

## 设计哲学的深层主张

> [!summary] 最反常识的一点
> 这个项目真正的创新不在 AI 算法（ReAct 循环 + 五层记忆都是已有技术），而在于**把经济学引入 agent 设计**：当一个 agent 必须为自己赚生存资源时，它的行为会被一种比"系统提示词"强大得多的力量约束——**现实**。这可能是解决 AI agent "token 浪费 / 无意义循环 / 缺乏目标感"的全新思路。

## Wikilinks

- [[agent-zero]] — 同为"自主成长"框架，但 agent-zero 是**离线个人助理**，Automaton 是**联网经济实体**。前者无生存压力，后者把生存压力做成第一性原理
- [[a2a-protocol]] — Automaton 的 social layer + ERC-8004 是 a2a 的"链上可验证 + 经济层"实现
- [[superpowers]] — 都用 constitution/constraints，但 superpowers 约束**工程流程**，Automaton 约束**生存伦理**
- [[claude-code-game-studios]] — 都在"用 agent 文件塑造行为"，CCGS 塑造**工作室纪律**，Automaton 塑造**经济人格**

---

*来源: GitHub README + ARCHITECTURE.md + constitution.md 源码分析，知乎/Panewslab 报道，2026-06-28*
