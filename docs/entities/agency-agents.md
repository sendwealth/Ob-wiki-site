---
title: Agency Agents (The Agency)
created: 2026-08-19
updated: 2026-08-19
type: entity
tags: [product, ai, agent, prompt-engineering, open-source, multi-tool]
sources:
  - https://github.com/msitarzewski/agency-agents
  - https://agencyagents.app
confidence: high
---

# Agency Agents (The Agency)

> 230+ 专业 AI Agent 人格库（msitarzewski/agency-agents，MIT，2025-10 创建）。每个 agent 是一个带 YAML frontmatter 的 Markdown 文件：人格化角色 + 领域关键规则 + 可交付物模板 + 工作流 + 成功指标。17 个"部门"（divisions）覆盖工程/设计/营销/销售/安全/GIS/游戏开发/学术等。核心工程亮点：一次编写 → convert.sh 自动转换成 16 种 AI 编码工具的原生格式（Claude Code/Codex/Cursor/Gemini CLI/Kimi/OpenClaw…），配 CI 一致性门禁与"换皮 agent"查重。

---

## 概览

The Agency 起源于一条 Reddit 帖子和数月迭代，定位是 **"一整个 AI 代理公司"**：前端巫师、Reddit 社区运营、俏皮感注入器、现实核查员……每个 agent 都有性格、流程和成型的可交付物。

核心理念（README 明确与"通用提示词库"划清界限）：
- 🎭 **强人格** — 不是 "Act as a developer" 式模板，而是真实角色与语调
- 📋 **明确可交付物** — 产出具体（代码/框架/清单），不是模糊建议
- ✅ **成功指标** — 每个 agent 自带可衡量的质量标准
- 🔄 **成熟工作流** — 一步步可复现的流程
- 💡 **学习记忆** — agent 文件中写明"我记得什么、从什么经验中学到什么"

典型样例 Whimsy Injector（设计部）：人格"俏皮/创造/以愉悦为导向"，核心使命是战略性地注入品牌俏皮感（微交互/彩蛋/游戏化），关键规则"每个 playful 元素必须服务功能或情感目的"、"whimsy 不得干扰屏幕阅读器"，可交付物包含完整的 Brand Personality Framework 模板和微交互 CSS 代码。

## 规模与指标

| 指标 | 数值 |
|------|------|
| Agents 总数 | 230+ |
| Divisions（部门） | 17 |
| 支持下游工具 | 16（tools.json） |
| 最大部门 | engineering ×58、specialized ×57、marketing ×36 |
| 单文件规模 | ~200-450 行（含代码示例） |
| 创建时间 | 2025-10-13 |
| 许可证 | MIT |
| 官方 App | agencyagents.app（原生 macOS/Linux/Windows，brew cask 可装） |
| 社区翻译 | 9 个（zh-CN ×2、pt-BR、ru、id、ar、ko、ja、vi） |

## 17 个 Divisions

engineering（58）/ specialized（57）/ marketing（36，含中国平台：小红书/知乎/B站/抖音/快手/公众号/私域）/ gis（13）/ security（12）/ design（10）/ sales（9）/ testing（9）/ project-management（7）/ paid-media（7）/ spatial-computing（6）/ academic（6）/ support（6）/ game-development（21，含 unity/unreal/godot/blender/roblox 子目录）/ finance（5）/ product（5）/ healthcare（3）。

部门元数据（label/Lucide icon/品牌色）以根目录 `divisions.json` 为**唯一事实源**，被 Agency Agents App 及目录工具消费。

## Agent 文件解剖

```markdown
---
name: Whimsy Injector
description: 一行专业描述
color: pink
emoji: ✨
vibe: 一句人格钩子
services:            # 可选：依赖的外部服务（含 tier: free/freemium/paid）
  - name: ...
---

# Agent Name
## 🧠 Your Identity & Memory    # 角色/性格/记忆/经验
## 🎯 Your Core Mission         # 3 项核心职责 + Default requirement
## 🚨 Critical Rules You Must Follow   # 领域关键规则（定义 agent 方法论）
## 📋 Deliverables              # 模板 + 代码示例（最大篇幅）
## Workflow Process             # 步骤化流程
## Success Metrics              # 可衡量的成功标准
## Communication Style          # 语调
```

lint-agents.sh 强制：frontmatter 必含 `name/description/color`（ERROR），建议含 Identity/Core Mission/Critical Rules（WARN）。

## 架构：一次编写 → 16 工具分发

```
agency-agents/
├── {division}/*.md        # 源：17 个部门的 agent 文件（唯一手写层）
├── divisions.json         # 部门事实源（label/icon/color）
├── tools.json             # 工具事实源（16 工具的安装契约）
├── scripts/
│   ├── convert.sh         # 转换器：.md → 各工具原生格式 → integrations/<tool>/
│   ├── install.sh         # 安装器：交互向导 + --division/--agent 选择 + dry-run + parallel
│   ├── lint-agents.sh     # frontmatter + 章节 lint
│   ├── check-divisions.sh / check-tools.sh / check-runbooks.sh   # CI 一致性门禁
│   ├── check-agent-originality.sh   # 换皮查重（8 词 shingle 重叠）
│   └── i18n/              # 中文本地化脚本
├── integrations/          # 生成产物（非源码）：codex TOML、cursor .mdc、
│   │                      #   antigravity/osaurus SKILL.md、openclaw 工作区、
│   │                      #   kimi YAML、aider/windsurf 合并 roster、hermes 插件…
│   └── mcp-memory/        # 跨会话记忆方案（MCP remember/recall/rollback）
├── strategy/              # NEXUS 编排层（非 agent：playbooks + runbooks）
└── examples/              # 多 agent 工作流示例（MVP/落地页/出书 + MCP 记忆版）
```

### tools.json：安装契约的三正交轴

每个工具条目用三个正交概念描述分发方式：
- **format** — 渲染契约：同名 format 保证字节级相同输出（claude-code/copilot 共享 `identity`；antigravity/osaurus 共享 `skill-md`）
- **installKind** — 安装机制：`per-agent`（每 agent 一个文件）/ `roster`（全 roster 合并单文件，aider CONVENTIONS.md）/ `plugin`（构建产物，仅 CLI）
- **scope** — user（`~/.claude/agents/`）vs project（`.cursor/rules/`）目标路径模板

这与 [[agentspace]] 用 AgentRouter 归一 8 个 harness 是同一问题的两种解法：agency-agents 走**编译期格式转换**（静态文件分发），agentspace 走**运行期归一**（统一执行契约）。

### convert.sh 的 OpenClaw 灵魂抽取

转换成 OpenClaw 工作区时需要从 agent 正文抽出"灵魂"（SOUL.md）。lint 脚本内置 `classify_header_target()`：把 Identity/Learning Memory/Communication/Style/Critical Rules 等章节归类为 `soul`，其余归 `body`——即**章节标题本身就是转换语义**。

## CI 工程亮点

### 1. 双事实源一致性门禁
`divisions.json` ↔ 磁盘目录 ↔ convert.sh/lint-agents.sh 的 `AGENT_DIRS` ↔ CI path filters，四处必须一致否则 check-divisions.sh 失败。tools.json ↔ install.sh 的 ALL_TOOLS ↔ convert.sh 转换器集合同理。**元数据漂移在 CI 就死掉**。

### 2. check-agent-originality.sh（换皮查重）
动机写在脚本头注释里：新 agent 应该是真正的新 agent，"换个国家名/平台名"的 find-forplace 重皮 PR 格式正确、能合并、review 容易漏。方案：**实体中立化后做 8 词 shingle 重叠比对**——换掉专有名词也藏不住抄袭。阈值：≥40% FAIL（exit 1）、≥20% WARN。校准依据：现有库最差同对相似度 ~1.5%（中位数 0%），双位数即强异常。无参运行 = 全库两两审计。

### 3. OpenCode 上游 bug 的防御性提示
README 注明 OpenCode 运行时只注册 ~119 个 agent 会静默丢弃其余（upstream bug），安装器在選择超限时主动警告，引导用 `--division` 子集安装。

## NEXUS 编排层（strategy/）

把 230 个 agent 从"逐个激活"升级为协调流水线：
- **NEXUS-Full**（全产品，12-24 周）/ **NEXUS-Sprint**（MVP，15-25 agents，2-6 周）/ **NEXUS-Micro**（单任务，5-10 agents，1-5 天）
- 7 阶段 playbooks：discovery → strategy → foundation → build → hardening → launch → operate
- 与 [[gstack]] 的 Sprint 流程（Think→Plan→Build→Review→Test→Ship→Reflect）同构——两者都是给 AI 团队定交付纪律

examples/ 给出可抄的现成组合：startup MVP 五人组、付费媒体接管六人组、八部门并行产品发现（Nexus Spatial Discovery）、以及 **MCP memory 版工作流**——用 remember/recall/rollback 工具替代人工 copy-paste 交接，解决会话超时丢上下文、多 agent 共享上下文、QA 失败回滚三类问题。

## 关键观察

1. **"Agent = 结构化 Markdown"的最纯粹样本** — 没有运行时、没有 SDK，agent 就是带 frontmatter 的人格说明书。人格/规则/可交付物/指标四件套是全部复杂度所在，与 [[skill-architect-methodology]] 的五层 Skill 架构（触发/角色/原则含反例/流程含检查点/资源）互相印证。
2. **分发即产品** — 16 工具转换矩阵 + 交互安装器 + 原生 App + 9 语言翻译，工程量大都花在"让同一份内容长在任何 harness 里"，与 [[caveman]]（跨 harness 原生分发）和 [[ecc]]（跨 harness 优化系统）是同一赛道。
3. **元数据治理小而美** — divisions.json/tools.json 双事实源 + CI 强制四处一致 + 换皮查重，是开源目录型项目防漂移防灌水的范式级做法。
4. **章节标题即语义** — OpenClaw 转换器按章节标题分类抽取 SOUL/body，说明 agent 文件结构不只是文档习惯，而是被工具消费的接口。
5. **贡献流程高度模板化** — CONTRIBUTING 规定完整模板 + divisions.json 加部门三步走 + 查重门禁，PR 流水线化（近期 #700-#749 密集合入，社区翻译各自独立成仓）。
6. **中国本地化深** — marketing 部门 36 个 agent 中约 14 个是中国平台原生（小红书/知乎/B站/抖音/快手/微淘/公众号/私域），另有中英双语 CONTRIBUTING 与 i18n 脚本。

---

**相关页面**: [[ecc]] | [[gstack]] | [[skill-architect-methodology]] | [[claude-code-game-studios]] | [[agentspace]] | [[caveman]] | [[superpowers]]
