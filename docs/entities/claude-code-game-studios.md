---
title: Claude Code Game Studios — 单会话虚拟游戏工作室
created: 2026-06-28
updated: 2026-06-28
type: entity
tags: [product, ai-coding, agent, skills, game-dev, claude-code, workflow, open-source]
sources:
  - https://github.com/donchitos/claude-code-game-studios
  - https://starlog.is/articles/ai-agents/donchitos-claude-code-game-studios
confidence: high
---

# Claude Code Game Studios

> 把单个 Claude Code 会话改造成"虚拟游戏工作室"——49 个 AI agent、73 个 slash skill、12 个 hook、11 条 path-scoped rule、41 个模板，全部由 `.claude/` 目录配置驱动。核心命题不是"让 AI 更聪明"，而是"让 AI 学会说不"。

*GitHub: donchitos/claude-code-game-studios | 许可: MIT*

## 一句话定位

这不是代码框架，而是一套 **`.claude/` 目录配置**（agents + skills + hooks + rules + templates），劫持 Claude Code 的 agent 系统，在**单个会话内**制造"持久化角色工作流"，模拟真实游戏工作室的层级与协作纪律。

## 核心问题与解法

AI 辅助游戏开发真正的瓶颈不是智能不足，而是**太顺从**——没有人说"先写 GDD 再动代码""这个 magic number 要抽出来""这个玩法缺 QA 验证"。

| 问题 | 表现 |
|------|------|
| AI 一口答应所有请求 | 缺架构评审、跳过设计文档、无 QA 门禁 |
| 单一"万能助手"无角色边界 | 同一会话既当策划又当程序员，建议互相矛盾 |
| 无成本意识 | 任何决策都烧最贵模型 token |
| 工程纪律无人强制 | 你知道该做 review/QA，但没人逼你 |

**解法**：用 agent 文件定义角色 + skill 串工作流 + hook 自动拦截 + rule 按目录加载规范，把工作室的协作纪律注入会话。

## 核心机制：单会话角色切换

> [!warning] 关键认知
> 49 个 agent **不是 49 个 AI 实例**。它们是 49 个带 YAML frontmatter 的 markdown 文件，让同一个 Claude 会话**依次披上不同人设**。所谓"多 agent 协作"在运行时只是会话内的角色切换。

每个 agent 文件长这样：

```yaml
---
name: gameplay-programmer
tier: 3
reports_to: lead-programmer
escalates_to: technical-director
requires_approval: [lead-programmer]
complexity_threshold: medium
---
# Gameplay Programmer
## Quality Gates
- No magic numbers — all values configurable via data
- Input handling must support rebinding
```

### Tier → 模型档位映射

`tier` 字段把角色层级映射到模型成本，**按决策重要性动态切换贵/便宜模型**——只在高层架构决策时烧 Opus token，执行层用 Sonnet/Haiku。这是它最聪明的经济设计。

```
Tier 1 — Directors       → Opus      creative-director, technical-director, producer
Tier 2 — Department Leads → Sonnet    game-designer, lead-programmer, art-director
Tier 3 — Specialists      → Sonnet/Haiku  gameplay-programmer, ai-programmer, level-designer
```

### 四向协调模型

```
         垂直委派 (director → lead → specialist)
              ↑
   横向咨询 ←──┼──→ 冲突升级 (→ director 拍板)
              ↓
         变更传播 (producer 跨部门协调)
```

- **垂直委派**：director → lead → specialist 自上而下分派
- **横向咨询**：同级可问，但不能跨域拍板
- **冲突升级**：设计分歧→creative-director，技术分歧→technical-director
- **变更传播**：跨部门改动由 producer 协调

## 四类基础设施的协同

| 层 | 数量 | 作用 | 例子 |
|----|------|------|------|
| **agents/** | 49 | 定义人设与质量门 | gameplay-programmer 禁止 magic number |
| **skills/** (slash 命令) | 73 | 编排跨角色工作流 | `/team-combat` 串起 systems-designer→gameplay-programmer→ai-programmer→ta→qa |
| **hooks/** | 12 | 自动化拦截 | `validate-commit.sh` 查硬编码值/TODO 格式；`detect-gaps.sh` 发现"有代码没设计文档" |
| **rules/** | 11 | 按目录加载领域规范 | 编辑 `src/networking/**` 自动注入"服务端权威+版本化消息+安全" |

> [!tip] Path-scoped rules 是隐藏亮点
> 编辑不同目录的代码，自动注入对应领域规范。AI 给出的建议就不会和框架惯例打架——Unity 专家主动考虑 DOTS/ECS，Godot 专家懂 GDScript 习语，网络代码自动套用服务端权威原则。

## 强协作、非自治

这点它和大多数"autopilot agent"框架划清界限。每个 agent 遵守严格协议：

```
Ask → 给 2-4 个选项带 pros/cons → 你拍板 → 出草稿 → 你批准
```

> [!warning] 没有任何东西不经你签字就写盘
> 这是它的设计哲学，也是它最大的局限来源（见下）。

## 局限与 Gotcha

1. **本质是 prompt engineering，无强制力** — 49 个 agent 拦不住你提交烂代码，只能"建议你别"。一旦你学会忽略 AI QA 的告警，整个结构就崩了。
2. **上下文窗口** — 项目一大，"lead-programmer" 会和之前 "gameplay-programmer" 说的自相矛盾，因为会话丢了之前的上下文。
3. **hooks 比看上去弱** — 只对 staged 文件生效、容易绕过、缺工具就静默降级。
4. **重型基础设施** — 49 agent + 73 skill 的学习成本，对 weekend game jam 是负担。

## 适用边界

| 场景 | 判断 |
|------|------|
| solo / 小团队做中大型游戏 + Claude Code | ✅ 用 |
| 缺乏流程纪律（知道该做架构评审/文档/QA，但没人逼） | ✅ 用 |
| 已有真人团队 | ❌ 结构冗余，真人协调更有效 |
| 用 Cursor / Copilot / 非 Claude Code 工具 | ❌ 强绑 Claude Code agent 系统 |
| 解谜/叙事/game jam 等小品类 | ❌ 49 agent 过度工程 |

## 设计哲学的深层主张

> [!summary] 关键洞察
> 这套东西真正的价值不在"让 AI 写游戏代码"，而在于**把组织基础设施（org chart、职责边界、审批流、质量门）编码进 AI 工作流**。它用游戏工作室这个具体场景，验证了一个更通用的范式：**AI 的产出质量上限，往往受限于它被嵌入的协作结构，而非它本身的智力**。

## Wikilinks

- [[superpowers]] — 同范式的通用版：用 SKILL.md + Hook 强制工程流程（TDD/系统化调试）。CCGS 是这套思路在游戏开发的垂直大型应用
- [[claude-code-workflow]] — 确定性多 agent 编排引擎。CCGS 的 `/team-*` slash 命令编排是同类思路的不同实现
- [[ecc]] — 63 agents + 249 skills 的跨 harness 生态；CCGS 专注游戏垂直，ecc 走通用广度
- [[agents-cli]] — Google 官方 CLI + Skills 工具链，与 CCGS 的 skills 层可类比

---

*来源: GitHub README、Starlog 技术深度文，2026-06-28 分析*
