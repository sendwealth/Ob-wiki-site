---
title: Skill 自进化闭环：darwin-skill × skill-evolver × EmbodiSkill
created: 2026-06-14
updated: 2026-06-14
type: concept
tags: [ai-agent, skill, self-evolution, hermes, meta-skill]
sources: [https://mp.weixin.qq.com/s/VTAwjgWJ5QR2bsaUuNh_hQ]
confidence: high
---

# Skill 自进化闭环：darwin-skill × skill-evolver × EmbodiSkill

> 来源：KK大叔「大叔笔记」公众号文章《这样做可以让Hermes Agent"打通任督二脉"，闪电般进化！》
> 核心论文：清华 SkillEvolver (arXiv:2605.10500) · 微软 SkillLens (arXiv:2605.23899) · 南大+微软+清华AIR EmbodiSkill (arXiv:2605.10332)

## 核心结论

> **AI 不需要更强的模型，只需要更好的"操作说明书"。**

不换模型、不调参数、不加数据，只通过让 AI 自进化 skill（操作说明书），就能实现能力提升。skill-evolver 4轮迭代从61分→86分，darwin-skill 从81.5→84.7分。

## 三个组件

| 组件 | 来源 | 角色 | 关键机制 |
|------|------|------|---------|
| **darwin-skill** | 微软 SkillLens 启发 | 评估专家（WHEN to stop, HOW to score） | 9维rubric、棘轮机制、独立评审 |
| **skill-evolver** | 清华 SkillEvolver 论文 | 进化专家（HOW to improve, WHAT to change） | 角色分离、策略多样化、对比式更新 |
| **EmbodiSkill** | 南大+微软+清华AIR | 诊断裁判（WHY it failed） | 四类失败归因、技能体/附录分离 |

### darwin-skill — 给 AI 打分的"质检员"

- **9维评估体系**（满分100）：frontmatter质量、工作流清晰度、失败模式编码、检查点设计、可执行具体性、资源整合度、整体架构、实测表现、反例与黑名单
- **棘轮机制**：分数只能涨不能跌，退步自动回滚
- **独立评审**：改skill的AI ≠ 评skill的AI（AI自评准确率仅46.4%，接近抛硬币）
- GitHub: [alchaincyf/darwin-skill](https://github.com/alchaincyf/darwin-skill)

### skill-evolver — 让 AI 自进化的"进化器"

核心思想：**角色分离，闭环进化**。作者写skill，执行者照章办事，信息不对称让缺陷自然暴露。

**三阶段：**
1. **策略多样化探索** — 同一任务生成3-4条不同策略（方法路径/步骤顺序/参数必须有实质差异）
2. **对比式更新** — 成功vs失败轨迹对比，找分叉点，只做补丁式修订
3. **独立审计** — 全新AI会话当审计官，看不到修改理由

GitHub: [oceanxu1989/hermes-skillevolver](https://github.com/oceanxu1989/hermes-skillevolver)

### EmbodiSkill — 四类失败归因

| 归因类型 | 处理方式 |
|---------|---------|
| 技能缺陷 (SkillDefect) | 改skill |
| 执行失误 (ExecutionLapse) | 记附录，不改skill |
| 新发现 (Discovery) | 记录不回滚 |
| 优化机会 (Optimization) | 微调参数 |

关键区分：说明书是对的但执行者手抖了 → 改说明书反而更糟。

GitHub: [z77orz/Skill-Enrichment](https://github.com/z77orz/Skill-Enrichment)

## 互优化实验（4轮迭代）

### 技能注入流向

```
darwin ──9维rubric+棘轮+探索性重写──→ skill-evolver
skill-evolver ──四类失败归因+补丁式修订──→ darwin
EmbodiSkill ──技能体/附录分离──→ 两者
```

### 迭代结果

| 轮次 | skill-evolver | darwin-skill | 关键改动 |
|------|--------------|--------------|---------|
| Round 1 | 61→81 (+20) | — | 补8个if-then失败场景 |
| Round 2 | 81→85.8 (+4.8) | — | Pitfalls与反例合并去重，4轴策略差异，STOP条件Δ定义 |
| Round 3 | 85.8→86.0 (+0.2) | — | delegate_task模板+evolution-log实例（触顶信号） |
| Round 4 | 86.0→79.1(权重修正) | 81.5→84.7 | darwin注入四类归因，Phase 2从二分法→四类分支 |

### darwin-skill 升级要点

- Phase 2 优化循环从"keep/revert二分法"→"四类分支决策"
- results.tsv 新增 failure_type 列
- 反例黑名单新增归因列
- 约束规则 #9：归因驱动修订

## 达尔文进化论类比

| 进化论 | AI版 |
|--------|------|
| 变异 | 策略多样化（生成不同策略） |
| 选择 | 对比式更新（成功vs失败轨迹对比） |
| 遗传 | 棘轮锁定（只保留改进） |

## 实践指南：在 Hermes Agent 中使用

三个 skill 已安装到 `~/.hermes/skills/`：

```bash
# 给 skill 打分（darwin-skill）
说："帮我评分这个skill" / "优化skill" / "达尔文"

# 让 skill 自进化（skillevolver）
说："进化skill xxx" / "skillevolver"

# 反思技能改进（skill-enrichment）
说："反思技能" / "进化技能" / "优化技能"
```

### 互优化工作流

1. 用 darwin-skill 给目标 skill 打分（9维rubric）
2. 用 skillevolver 生成改进策略并对比执行
3. 用 skill-enrichment 做四类失败归因
4. 改进后重新用 darwin-skill 评分
5. 分数涨→保留，分数跌→回滚（棘轮机制）
6. 重复直到 Δ<2（触顶信号）

## 相关页面

- [[heuristic-learning]] — coding agent 替代梯度训练的新学习范式
- [[agent-world]] — Agent World 智能体世界设计：生存沙盒 + A2A 协作 + 进化系统
- [[humanizer-skill]] — Humanizer：AI写作痕迹检测+消除方法论
