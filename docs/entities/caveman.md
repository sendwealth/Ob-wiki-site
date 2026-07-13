---
title: Caveman (caveman skill)
created: 2026-07-13
updated: 2026-07-13
type: entity
tags: [product, ai, developer-tools, prompt-engineering, token-optimization, cli, active, mcp]
sources:
  - https://github.com/JuliusBrussee/caveman
confidence: high
---

# Caveman (caveman skill)

> 面向 AI 编程代理的「技能/插件」包，slogan 是 *"why use many token when few token do trick"*。核心理念：**压缩代理"说"的内容，而不是它"知道"的内容**——丢弃填充词、用片段化表达，但代码/命令/错误信息保持字节级精确。输出 token 平均减少 65%（区间 22–87%），可读性反而提升。MIT 协议，永久免费。

---

## 概览

Caveman 不是新模型，而是一个**提示词约束层**。它把一段系统提示注入到你的 AI 编码代理里，告诉代理："少说废话、保留实质、用碎片句，但永远不要改代码、命令或报错。" 代理的推理能力和知识不变（"Brain still big. Mouth small."），只是输出更短。

支持 Claude Code、Codex、Gemini、Cursor、Windsurf、Cline、Copilot、OpenClaw 等 **30+ 种代理**——安装一次，自动探测机器上所有代理并逐一注入。

## 规模与指标

| 指标 | 数值 |
|------|------|
| GitHub Stars | ~88.9K |
| Forks | ~5.1K |
| Watchers | ~283 |
| Releases | 16（最新 v1.9.1 "65%, honestly"，2026-07-03）|
| 平均输出 token 缩减 | **65%**（10 条 prompt 实测，Claude API 真实计数）|
| 单条缩减区间 | 22% – 87% |
| `caveman-compress` 输入 token 缩减 | 平均 46%（记忆文件，永久生效）|
| 语言占比 | JavaScript 69.1% · Python 24.1% · PowerShell 3.6% · Shell 3.2% |
| 许可证 | MIT |

> [!warning] 诚实数字警告
> Caveman 只压缩**输出** token。输入和推理 token 不受影响，且技能本身每个回合会额外增加约 1–1.5k 输入 token。所以在已经很简洁的任务上，整会话净节省可能为负。真正的收益是**可读性与速度**，成本节省是附赠。项目用 `docs/HONEST-NUMBERS.md` 和 `benchmarks/`、`evals/` 把这点讲得很透。

---

## 技术架构

### 1. 技能注入模型（核心）

安装脚本把一段"穴居人"提示词落到对应代理的配置目录（Claude Code 的 plugin、Gemini 的 extension、Cursor 的 rule 文件等）。这段提示要求代理：
- 丢弃 filler（"I'd be happy to help" 之类）
- 用片段化、去修饰的表达
- **硬性禁止**改动任何代码、命令、错误信息（字节级精确）

### 2. Hook 机制（自动开启）

在 Claude Code / Codex / Gemini 上，安装会写入一个 **hook**，每个会话自动写一个极小的 flag 文件。于是代理从第一条消息起就进入穴居人模式，**无需手动输入 `/caveman`**。其他代理（如 OpenClaw）则是向 `SOUL.md` 追加一个带标记围栏的块，由代理每轮自动注入。

### 3. 命令集

| 命令 | 作用 |
|------|------|
| `/caveman [lite\|full\|ultra\|wenyan]` | 压缩每条回复；级别在会话内保持（full 默认，wenyan = 文言文模式进一步压缩）|
| `/caveman-commit` | Conventional Commit，≤50 字符 subject，讲 why 而非 what |
| `/caveman-review` | 单行 PR 评论：`L42: 🔴 bug: user null. Add guard.` |
| `/caveman-stats` | 读本地会话日志，算真实 token 节省 + USD 估算；`--share` 出 tweetable 文案 |
| `/caveman-compress <file>` | 把记忆文件（如 `CLAUDE.md`）改写成穴居人风格，后续每个会话加载更小上下文；代码/URL/路径字节保留 |
| `caveman-shrink` | **MCP 中间件**：包裹任意 MCP server，压缩其工具描述（npm 包）|
| `cavecrew-*` | 调查/构建/审查子代理，比原生省约 60% token，延长主上下文 |

### 4. 压缩级别（六个层级）

| 级别 | 同一句话的压缩 |
|------|------|
| normal | You should wrap the object in `useMemo`, since a new reference is created on every render. |
| `lite` | Wrap object in `useMemo`. New ref created every render. |
| `full`（默认）| New ref each render. Wrap object in `useMemo`. |
| `ultra` | New ref/render. `useMemo` it. |
| `wenyan` | New ref every render, so wrap in `useMemo` ——文言文，单 token 信息密度最高 |

> 语言保持：Caveman 保留用户原有语言（只压风格不翻译），`wenyan` 是刻意例外——文言文每 token 承载意义最多。

### 5. 安装架构（跨平台工程）

`install.sh` / `install.ps1` 只是**薄包装层（shim）**，实际逻辑统一在 `bin/install.js`（Node）：
- 仅校验 `node ≥ 18` 与 `npx`
- 本地克隆运行 → `exec node bin/install.js`；远程 `curl|bash` → `exec npx -y github:JuliusBrussee/caveman`
- 动机：之前 shell/ps1 双线维护导致逻辑漂移（issue #249），故收敛为单一 Node 脚本跨平台
- 真正的"探测每个代理 + 落盘路径 + 写 hook/flag"逻辑都在 `bin/install.js` 里
- 需要 Node ≥18，跳过机器上没有的代理，可安全重跑，`--uninstall` 卸载

### 6. 隐私架构

纯本地提示词 + 脚本：**无遥测、无分析、无账号、无后端**。安装后零网络调用——技能是提示，hook 是本地脚本，`/caveman-stats` 只读你磁盘上已有的日志。安装时的网络拉取（GitHub + 各代理自身注册表）在 `SECURITY.md` 里写明了。

---

## 生态矩阵（一个想法：agent do more with less）

Caveman 是"5 个工具、一个想法"生态的入口，每个 repo 压缩不同维度：

| Repo | 压缩什么 |
|------|------|
| **caveman**（本页）| 代理**说**的内容 |
| [caveman-code](https://github.com/JuliusBrussee/caveman-code) | **整个代理**端到端（~2× 少于 Codex，20+ provider，MIT）|
| [cavemem](https://github.com/JuliusBrussee/cavemem) | 代理**记住**的内容（跨会话）|
| [cavekit](https://github.com/JuliusBrussee/cavekit) | **构建循环**（spec-driven，不瞎猜）|
| [cavegemma](https://github.com/JuliusBrussee/finetune-caveman) | 把压缩**烤进权重**（Gemma 微调）|

另有兄弟技能合集 `JuliusBrussee/skills`（grill-me / interface-kit / junior-to-senior / loop-factory + caveman），`npx skills add` 一次装 5 个，覆盖 40+ 代理。

**Caveman 2（规划中）**：从"本地估算"走向"团队可验证"——真实收据、仪表盘、可证明 token 下降（waitlist: caveman.so）。

---

## 技术栈

| 层 | 技术 |
|----|------|
| 安装器 | Node.js ≥18（`bin/install.js`，跨平台单一脚本）|
| 包分发 | npm（`caveman-shrink`）、Claude Code plugin marketplace、Gemini extension、npx skills registry |
| Hook | 各代理原生 hook / marker-flag 文件 |
| 测试与基准 | `tests/`、`benchmarks/`、`evals/`（可复现）|
| 治理文档 | `CLAUDE.md`（维护者指南：hook 架构 + CI 同步）、`CONTRIBUTING.md`、`SECURITY.md`、`CODE_OF_CONDUCT.md`、`INSTALL.md` |
| 赞助 | GitHub Sponsors（如 Atlas Cloud），无强制付费 |

---

## 关键观察

1. **提示词即产品**——不需要训练/微调，纯系统提示约束就实现 65% 输出压缩，是"上下文工程"的极简范例。
2. **跨 harness 分发是核心能力**——用每个代理的**原生**插件/扩展/规则机制各装各的，而非发明新格式，这是它能一夜覆盖 30+ 代理的关键。
3. **honesty 即营销**——主动讲"整会话可能净负""只压输出"，反而建立信任（呼应 arXiv:2604.00025：约束长模型写短能提升 ~26 分准确率）。
4. **生态而非单品**——caveman / caveman-code / cavemem / cavekit / cavegemma 形成"压缩一切"矩阵，每个维度一个 repo，降低单点复杂度。

---

**相关页面**: [[ecc]] | [[superpowers]] | [[context-mode]] | [[opensource-project-practices-from-caveman]]
