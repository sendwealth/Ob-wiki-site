---
title: ai-job-search
created: 2026-07-04
updated: 2026-07-04
type: entity
tags: [agent, agentic-ai, claude-code, agent-skill, job-search, latex, career, typescript]
sources:
  - https://github.com/MadsLorentzen/ai-job-search
  - https://mp.weixin.qq.com/s/9PZeMQpvdIJn6XOU-nnFjA
confidence: high
---

# ai-job-search

> **让 Claude 替你跑完求职全流程的结构化框架**。3.4k Star / 1.5k Fork，TypeScript + Claude Code。不是"帮我改改简历"的聊天工具，而是把求职编码成 `/setup → /scrape → /apply` 命令流水线，一条 `/apply` 跑 7 步出两份排版完美的 PDF。

**仓库**：https://github.com/MadsLorentzen/ai-job-search
**栈**：Claude Code + LaTeX + Bun（TypeScript）

## 核心定位：求职流水线，不是聊天机器人

三个命令把求职从"手工打磨每一份材料"变成"一条命令出成品"：

| 命令 | 作用 |
|------|------|
| **`/setup`** | 建立结构化个人画像（AI 可推理档案，非简单简历） |
| **`/scrape`** | 搜索多职位门户，自动去重 + 按匹配度排序 |
| **`/apply <URL>`** | 对指定职位跑完 7 步申请流程，输出简历 + 求职信 PDF |

> 核心流程**语言/国籍无关**——虽内置职位搜索针对丹麦市场，但起草、匹配评估、审阅修改全球通用。

## `/setup`：三种方式建画像

- **路径 A 文档夹**：把简历 PDF / LinkedIn 导出 / 学位证 / 推荐信扔进 `documents/`，Claude 自动提取生成画像
- **路径 B 单份简历**：聊天里粘贴一份简历
- **路径 C 访谈模式**：对话式挖掘简历没写但重要的内容（行为模式、文化偏好、写作风格）——最丰富也最耗时

不管哪条路，最终都输出同一份**结构化档案**（候选人资料 + 行为评估 + 写作风格 + 技能），作为后续所有操作的底座。

## `/apply`：7 步流水线

```
解析 → 评估匹配度 → 起草(LaTeX) → 独立审阅 → 修改 → 编译+视觉检查 → 呈现
```

1. **解析** — 从 URL/文本提取职位要求、公司信息、技能需求
2. **评估匹配度** — 基于完整画像，从技能/经验/文化/地点/职业路线 5 维度推理（非关键词比对）
3. **起草** — LaTeX 起草量身定制的简历 + 求职信，简历按相关性智能删减
4. **独立审阅** ⭐ — 生成独立审阅代理，全新上下文研究公司后批判草稿
5. **修改** — 按审阅反馈改稿，形成起草-审阅-修改循环
6. **编译与视觉检查** ⭐ — 编译 PDF 后 Claude 读取渲染页面，检查分页/字体/布局，自动迭代 LaTeX 直到完美
7. **呈现** — 展示成品 + 验证清单

## 三大差异化优势

### ① PDF 视觉验证循环（最独特）
LaTeX 简历常见痛点：`.tex` 看着没问题，PDF 编译后分页错乱、字体回退、内容溢出。本项目 **编译 PDF → Claude 读渲染结果 → 发现问题改 LaTeX → 重编译**，循环到布局完美。简历≤2 页、求职信恰好 1 页且签名可见。**其他 AI 求职工具都做不到。**

### ② 起草-审阅双代理机制
起草代理 vs **独立审阅代理**（全新上下文，无起草"思维惯性"），更敏锐捕捉通用措辞、弱框架、错位表述。草稿**内联传递**而非重读文件，优化 token。

### ③ 相关性加权简历删减
简历过长时不机械删最旧，而是按 **相关性 × 在文档中独特性 × 对求职信的支撑作用** 三维度评分，删总分最低项。10 年前但高度相关的经历也会保留。

## 其他命令

- **`/expand`（能力拓展）** — 扫描画像中关联的公开来源（GitHub / 作品集 / Kaggle / Google Scholar），自动提取项目、技术栈、成果，补进画像
- **`/upskill`（技能差距分析）** — 对比画像与目标职位，输出优先级热力图 + 学习计划。精确到"职位要 K8s，你只有 Docker，差距在编排层"，存入 `upskill/`
- **`/reset`** — 带确认的安全重置（可选清画像/文档夹/两者），每次操作前确认

## 技术架构

| 路径 | 职责 |
|------|------|
| `CLAUDE.md` | 主画像 + 工作流规则 |
| `.claude/commands/` | 自定义命令（/setup /scrape /apply …） |
| `.claude/skills/` | 核心技能包 |
| `.agents/skills/` | 本地职位搜索 CLI（内置 4 个丹麦门户，可套模式做自己的） |
| 简历/求职信模板 | 独立 LaTeX 模板目录（cover.cls + Lato/Raleway） |

## 上手

前置：Claude Code CLI + Python 3.10+ + Bun + LaTeX（TeX Live / MiKTeX）

```bash
gh repo fork MadsLorentzen/ai-job-search --clone
cd ai-job-search
cd .agents/skills/jobbank-search/cli && bun install && cd ../../../..
# 简历 PDF 扔进 documents/
claude
/setup
/scrape
/apply <职位URL>
```

## 与「AI 改简历」工具的本质区别

| 维度 | AI 改简历聊天工具 | ai-job-search |
|------|------|------|
| 覆盖范围 | 只改措辞 | 画像→搜索→评估→简历→求职信→PDF 验证→面试准备 |
| 输出质量 | 纯文本自己排版 | LaTeX PDF + 自动视觉验证 |
| 审阅机制 | 单次处理 | 起草-审阅双代理独立批判 |
| 简历删减 | 机械删最旧 | 相关性加权评分 |
| 可复用性 | 每次重新描述需求 | 一次建画像，后续自动引用 |

## 作为 Agent Skill 范式案例的价值

本项目是 [[openmontage]] 在**个人场景**的对偶：OpenMontage 把制片方法论编码成 12 条 YAML 流水线，ai-job-search 把求职方法论编码成 7 步命令流水线。两者共同验证——

> **把领域方法论编码成 Markdown/YAML 技能指令 + 让 AI 助手读指令走流程**，比让 AI「自由发挥」靠谱得多。这是 Agent Skill 范式的核心。

可借鉴的具体技术：PDF 视觉验证闭环（渲染→读图→改代码→重渲，可迁移到任何"生成→校验"场景）、双代理审阅机制（起草者 vs 独立批判者）。

## 相关页面

- [[openmontage]] — Agent Skill 在生产场景的极致，与本项目的个人场景对偶，共同定义 Agent Skill 范式
- [[leaferjs]] — 同样"把领域方法论做厚"的范式，绘图语言标准 vs 求职流程标准
- [[design-as-code]] — 设计↔代码范式，与"求职流程↔代码"同构
