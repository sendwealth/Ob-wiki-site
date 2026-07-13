---
title: 从 Caveman 项目学习开源分发与运营实践
created: 2026-07-13
updated: 2026-07-13
type: concept
tags: [open-source, distribution, developer-tools, prompt-engineering, cli, documentation, privacy, sponsorship]
sources:
  - https://github.com/JuliusBrussee/caveman
  - https://github.com/JuliusBrussee/caveman/blob/main/INSTALL.md
confidence: high
related:
  - "[[caveman]]"
  - "[[opensource-project-practices-from-multica]]"
  - "[[opensource-project-practices-from-openhuman]]"
---

# 从 Caveman 项目学习开源分发与运营实践

> Caveman 是一个 MIT 协议、88.9K⭐ 的 AI 编码代理"省 token"技能包。它体量不大，却在**分发策略、诚实营销、隐私设计、跨平台工程、生态化运营**上做得很巧。以下提炼中小开源项目可复用的实践。

---

## 1. 跨 harness 分发：用原生机制，不发明格式

Caveman 最大的工程亮点不是压缩算法，而是**一套技能能装到 30+ 种代理**上。做法是为每个代理用其**原生**扩展点，而非强推统一格式：

| 代理 | 安装方式 |
|------|----------|
| Claude Code | plugin marketplace：`claude plugin marketplace add JuliusBrussee/caveman` |
| Gemini CLI | extension：`gemini extensions install <repo>` |
| Cursor / Windsurf / Cline / Codex 等 | 通用 skills 注册表：`npx skills add JuliusBrussee/caveman -a cursor` |
| OpenClaw | 向 `SOUL.md` 追加带标记围栏的块，每轮自动注入 |
| 任意单一代理 | `install.sh --only <agent>`，或 `npx skills add ... -a <agent>` |

**可复用启示**：做开发者工具时，优先适配目标平台已有的插件/规则/扩展协议，借力其分发渠道，比自建封闭生态起步快得多。

---

## 2. 跨平台安装器：单一 Node 脚本，消灭双线漂移

早期 `install.sh` 与 `install.ps1` 各维护一份，导致逻辑漂移（issue #249）。收敛方案：

- `install.sh` / `install.ps1` 退化为**薄 shim**，只校验 `node ≥ 18` + `npx`
- 本地运行 → `exec node bin/install.js`；远程 `curl|bash` → `exec npx -y github:JuliusBrussee/caveman`
- 真实"探测代理 + 落盘路径 + 写 hook/flag"全部在 `bin/install.js` 一处实现

**可复用启示**：跨平台 CLI 的安装器，用一门跨平台语言（Node）写**一份**真逻辑，shell/ps1 只做引导，避免"双份代码必定漂移"的诅咒。

---

## 3. 诚实营销：把缺点写在前头，反而建立信任

README 显眼处放 `docs/HONEST-NUMBERS.md` 与 `> [!IMPORTANT]` 诚实警告：
- 只压**输出** token；每个回合额外 +1–1.5k 输入 token
- 已很简洁的任务上，整会话节省可能**净负**
- 真实收益是可读性 + 速度，成本节省是附赠
- 引用 arXiv:2604.00025（约束大模型写短，31 模型实测准确率 +26 分）

`benchmarks/`、`evals/` 提供可复现的真实计数（10 条 prompt，22–87% 区间），而非只喊"65%"。

**可复用启示**：对效果型工具，主动暴露边界和失败场景，比只放大数字更能赢得技术用户信任，也降低被"翻车"反噬的风险。

---

## 4. 隐私设计：无遥测即卖点

- 纯本地提示词 + 脚本；无遥测、无分析、无账号、无后端
- 安装后零网络调用；`/caveman-stats` 只读你磁盘上的日志
- 安装时的外部拉取在 `SECURITY.md` 里写明来源（GitHub + 各代理注册表）

**可复用启示**：对"注入你的开发环境/代理"的工具，把"不打电话回家"当成一等特性写进文档，是打消安全顾虑的最低成本方式。

---

## 5. 文档即治理：维护者指南 + 完整治理文件

| 文件 | 作用 |
|------|------|
| `CLAUDE.md` | 维护者指南：hook 架构、文件归属、CI 同步约定——让 AI 助手也能维护项目 |
| `INSTALL.md` | 30+ 代理安装矩阵、全部 flag、`--dry-run`、卸载 |
| `SECURITY.md` | 隐私/遥测说明、供应链（安装器拉取来源）|
| `CONTRIBUTING.md` / `CODE_OF_CONDUCT.md` | 贡献流程与行为准则 |

**可复用启示**：把"项目怎么维护"本身写成文档（尤其给 AI 助手读的 `CLAUDE.md`），能降低他人与你共同维护的门槛——和 [[opensource-project-practices-from-multica|Multica 的文档即规范]] 思路一致。

---

## 6. 生态化运营：一个想法，多个 repo

Caveman 不是单品，而是"agent do more with less"矩阵的入口：caveman（说）/ caveman-code（整代理）/ cavemem（记忆）/ cavekit（构建循环）/ cavegemma（烤进权重），每个维度一个独立 repo，MIT。再加 `JuliusBrussee/skills` 技能合集一次装 5 个。

**可复用启示**：把一个核心洞察拆成**互相独立又能组合**的多个小工具，比做一个巨型 monorepo 更易传播、更易各自找到用户；用"合集"降低发现成本。

**商业化**：GitHub Sponsors 接受赞助（如 Atlas Cloud），永久免费、无强制付费；Caveman 2 走团队级可验证收据/SaaS 方向，和免费开源技能层分层。

---

## 7. 可直接复用的实践清单

- [ ] **适配原生扩展点** — 用目标平台已有的插件/规则/扩展机制分发，不造新格式
- [ ] **安装器单一真逻辑** — shell/ps1 只做 shim，真逻辑用跨平台语言写一份
- [ ] **诚实数字** — 暴露效果边界与失败场景，附可复现基准
- [ ] **隐私写进文档** — "无遥测"作为卖点，注明外部拉取来源
- [ ] **CLAUDE.md 维护者指南** — 让 AI 助手也能接手维护
- [ ] **生态拆分** — 一个洞察拆成多个独立可组合小工具 + 一个合集
- [ ] **赞助而非付费墙** — MIT 免费 + GitHub Sponsors 养项目

---

## 核心启示

> **小工具也能成大项目，关键是"分发 + 信任 + 生态"三件套，而不是功能堆砌。**
>
> Caveman 用原生扩展点一夜覆盖 30+ 代理（分发），用诚实数字和零遥测建立信任（信任），用"压缩一切"的独立 repo 矩阵形成生态（生态）。它与 [[opensource-project-practices-from-multica|Multica]]（单一真相源 + 漂移防护 + 一键命令）走的是不同路径：Multica 解决中团队的工程效率，Caveman 解决个人开发者的 token 焦虑——但共通点是**把经验写成文档、把重复劳动交给机器、用最少的前提条件让用户用起来**。
