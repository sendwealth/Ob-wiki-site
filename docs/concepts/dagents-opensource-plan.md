---
title: Dagents 开源改造与发布计划
created: 2026-08-20
updated: 2026-08-20
type: concept
tags: [open-source, planning, release, monorepo, ci-cd, community, documentation]
sources:
  - ~/Projects/dagents
  - "[[opensource-project-practices-from-multica]]"
  - "[[opensource-project-practices-from-openhuman]]"
  - "[[opensource-project-practices-from-langflow]]"
  - "[[opensource-project-practices-from-temporal]]"
  - "[[opensource-project-practices-from-caveman]]"
  - "[[opensource-practices-from-lobechat]]"
confidence: high
related:
  - "[[agentspace]]"
  - "[[flowise]]"
  - "[[ai-workflow-landscape]]"
---

# Dagents 开源改造与发布计划

> Dagents（~/Projects/dagents，git@github.com:sendwealth/dagents，148 commits）是 Chat-First 异构 coding agent 平台：console（Next）→ gateway（Hono）→ workflow 引擎 → CLI agent（claude/codex 等 16+ 种）。本计划基于 2026-08-20 全仓审计 + 六份开源实践笔记（Multica / OpenHuman / Langflow / Temporal / Caveman / LobeChat），给出从现状到公开发布的分阶段路线图。

---

## 1. 审计结论（2026-08-20）

### 1.1 已具备的底子（比多数同期项目好）

| 维度 | 现状 | 对应最佳实践 |
|---|---|---|
| CI | `ci.yml`：install→build→typecheck→lint→migration→test，含 Postgres service、并发取消、注释详尽 | Langflow / Temporal ✅ |
| E2E | `e2e.yml` + Mock LLM Provider（OpenAI 兼容 + 控制面）+ 专用测试库 | OpenHuman 分层测试 ✅ |
| 部署 | 根 `docker-compose.yml` 全栈（端口绑 127.0.0.1）+ Dockerfile + entrypoint | Multica 自托管 ✅ |
| 安全 | README 安全须知（GATEWAY_API_KEY / ENCRYPTION_KEY 等）；2026-08-16 审计修复过 SSRF/WS/HTTP 节点 | Langflow 安全层次 ✅ |
| 文档 | docs/README.md 地图 + CLAUDE.md + AGENTS.md + 6 篇主题文档 | OpenHuman 文档即规范 ✅ |
| 密钥卫生 | `.env` 未跟踪；工作区与 **git 全历史** 扫描无真实密钥（15 处命中均为测试 mock 占位符 `postgres://u:p@host`） | — ✅ |
| i18n | 中英双语自然键体系已内置（`useI18n`） | LobeChat i18n ✅ |

### 1.2 硬缺口（开源阻塞项）

1. **无 LICENSE** —— 最硬阻塞，无协议 = 无人敢用。
2. **vendor/agentflow 许可证不合规** —— vendored 自 FlowiseAI/Flowise 的 `packages/agentflow`（package.json 声明 Apache-2.0），但仓库内**未随附 LICENSE 文件与上游归属**。Apache-2.0 要求再分发时保留协议文本。
3. **个人痕迹泄漏**：5 个跟踪文件含 `/Users/rowan`（AGENTS.md、docs/archive×2、docs/superpowers×2）；CLAUDE.md 引用本地私有技能 `dagents-patterns` / `multica-ops` 与 multica issue tracker 个人工作流；AGENTS.md 引用 `~/.hermes/config.yaml`。
4. **无版本策略**：version 0.0.0、无 tag、无 CHANGELOG、无 Release 流程。
5. **无社区文件**：CONTRIBUTING / CODE_OF_CONDUCT / SECURITY / Issue 模板 / PR 模板 / CODEOWNERS 全缺。
6. **README 纯中文**：国际受众不可达（LobeChat 教训：README 是落地页）。
7. **小项**：`.env.example` 首行注释仍是旧名 "Mil-Agents"；`package.json` 无 `engines`（实际需 Node ≥22）。

---

## 2. 定位与叙事（先想清楚再动手）

- **一句话定位候选**：「Chat-First 的异构 coding agent 编排平台 —— 用聊天驱动 claude/codex 等 16+ CLI agent，本地优先，零配置可跑」。核心差异化：**CLI 第一性**（不绑特定 LLM 厂商）+ **Agent 人格库生态**（agency-agents 类 270+ 人格挂载）+ **流程模板中心**。
- **诚实营销（Caveman 实践）**：把 `docs/workflow-engine.md` 的「现状与限制」（Agent 节点无工具循环、LLM fetch 无超时、new Function 非沙箱等）提炼进 README/KNOWN-LIMITATIONS —— 主动暴露边界比翻车反噬便宜得多。
- **竞品坐标**：见 [[ai-workflow-landscape]]（Dify/n8n/Flowise 是低代码编排，dagents 是 CLI-agent-native 编排，错位竞争）。

---

## 3. Phase 0 —— 法律与合规硬门（~半天，不做完不能公开）

- [ ] **选定并落盘 LICENSE**：推荐 **Apache-2.0**（与 vendored agentflow 同协议最干净；含专利授权，对 AI 基础设施更稳）。备选 MIT（更简但与 vendored Apache-2.0 混用时仍需在 vendor 目录保留 Apache 协议文本）。
- [ ] **vendor/agentflow 合规**：目录内补 Apache-2.0 LICENSE + NOTICE（上游 FlowiseAI/Flowise `packages/agentflow`），根 README 加 Attribution 节。
- [ ] **个人路径清理**：AGENTS.md / docs/archive/{design,plans} / docs/superpowers/specs 中 5 处 `/Users/rowan` 改为相对路径或通用描述。
- [ ] **CLAUDE.md / AGENTS.md 去个人化**：移除 `multica-ops`、`dagents-patterns` 本地技能段、multaca issue 映射、一键重启脚本绝对路径（改为通用 `bash restart-gateway.sh`）、`~/.hermes/config.yaml`。
- [ ] **确认 git 历史干净**：已验证（2026-08-20，全历史密钥模式扫描），写入 SECURITY.md 备查，无需 squash 重写历史。

## 4. Phase 1 —— 治理文件与仓库整备（1~2 天）

- [ ] **CONTRIBUTING.md**（Temporal 零知识假设标准）：前置依赖（Node ≥22、pnpm 10、Docker）、`pnpm install → infra compose up → migration:run → dev` 首跑路径、测试金字塔（vitest 单测 / 需 Postgres 的集成 / e2e 与 Mock LLM 说明）、已知坑（dev server 运行期间勿跑 build）。
- [ ] **CODE_OF_CONDUCT.md**：Contributor Covenant v2.0（Langflow 同款）。
- [ ] **SECURITY.md**：漏洞披露流程（私有 advisory）+ in-scope（gateway 鉴权、SSRF、daemon 协议）+ 隐私声明（**无遥测、无后端上报**——Caveman 实践：把零遥测写成一等特性）。
- [ ] **.github/ISSUE_TEMPLATE/**（bug.yml / feature.yml）+ **PULL_REQUEST_TEMPLATE.md**（Temporal 四段式：What changed / Why / How did you test it / Potential risks）。
- [ ] **engines 字段**：根 + 各 workspace `package.json` 声明 `node >=22`。
- [ ] `.env.example` 注释 Mil-Agents → Dagents；全仓 grep 复查旧名。
- [ ] **docs 去留决策**：`docs/superpowers/`（spec/plan 流水线）与 `docs/archive/` 建议保留 —— 开发过程透明本身是差异化卖点（架构真相源 spec 已是高质量文档）；但需清掉其中的个人验证报告类内容。

## 5. Phase 2 —— 贡献者体验（1~2 天）

- [ ] **README 落地页化 + 双语**（LobeChat 实践）：`README.md` 英文为主 + `README.zh-CN.md` 中文；结构 = badge 墙（CI/License/Docker）→ 一句话定位 → 架构图 → 60 秒跑起来（docker compose up 单命令）→ 功能截图/GIF → KNOWN-LIMITATIONS 诚实节 → 贡献指南链接。
- [ ] **5 分钟体验路径**：确保 `docker compose up` + 首页聊天开箱可用（CLI 兜底零配置），这是「CLI 第一性」叙事的最强演示。
- [ ] **Dev Container**（LobeChat 实践，可选）：`.devcontainer/devcontainer.json`。
- [ ] **Worktree/多实例说明**：端口与 `.env` 已天然隔离，写进 CONTRIBUTING 即可（Multica 实践的轻量版）。

## 6. Phase 3 —— CI/CD 与发布基建（1~2 天）

- [ ] **保留现有 ci.yml/e2e.yml**（已是好实践），增强：
  - ci.yml 加 **dorny/paths-filter** 路径感知（gateway/console/packages 变更分道测试 —— Langflow 实践，e2e 已有 paths 先例）；
  - **CodeQL**（js/ts）+ **Dependabot 或 Renovate**（月度、安全更新优先）。
- [ ] **Release 流程**（Multica 模板）：git tag `v*` 触发 → semver 校验 → 构建镜像推 **GHCR**（Dockerfile 已有）→ GitHub Release + CHANGELOG 生成 → `if: github.repository_owner == '<org>'` fork 保护。
- [ ] **版本策略**：从 `v0.1.0` 起，`main` 持续开发 + tag 即发布（单人维护阶段无需 release 分支）；CHANGELOG.md 用 conventional commits 自动生成。
- [ ] **npm 发布决策**：当前 `private: true` 全 workspace —— 首期只发 Docker 镜像 + 源码运行，npm 包（如 @dagents/workflow）待有独立用户需求再拆。

## 7. Phase 4 —— 发布与社区运营（上线日 + 持续）

- [ ] **仓库与命名决策**：现 remote 在个人 org `sendwealth`。建议为开源单独建 org（如 `dagents-ai` 或类似，先查重），避免与私有 wiki 同 org；也可以直接翻转现有仓库可见性（历史已验证干净）。
- [ ] **发布检查单**：GitHub topics、社交预览图（OG image）、Discussions 开启、release v0.1.0。
- [ ] **发布渠道**（可用 agent-reach skill 分发）：Show HN、r/LocalLLaMA、r/selfhosted、V2EX、即刻；叙事重点打「不绑厂商的 CLI agent 编排」+「270+ 人格库生态」。
- [ ] **社区自动化**（LobeChat 前沿实践，按需渐进）：先 GitHub 原生（stale bot、labeler），有人气后再上 AI triage / AI 翻译评论。
- [ ] **维护节奏承诺写进 README**：issue 响应时限（如 7 个工作日，Langflow 标准），防期望错位。

---

## 8. 决策点汇总（需要项目负责人拍板）

| # | 决策 | 推荐 | 备选 |
|---|---|---|---|
| D1 | License | Apache-2.0 | MIT |
| D2 | 仓库归属 | 新建独立 org | 翻转 sendwealth/dagents 可见性 |
| D3 | README 语言策略 | 英文主 + 中文链接 | 中文主（受众在国内时） |
| D4 | docs/superpowers + archive | 保留（透明开发卖点） | 移出仓库精简门面 |
| D5 | npm 包发布 | 首期不发，只 Docker+源码 | 立即拆包发布 |

## 9. 时间线估算

```
Phase 0  法律合规硬门        0.5 天   ← 公开的唯一硬前置
Phase 1  治理文件与整备      1~2 天
Phase 2  贡献者体验          1~2 天   （可与 Phase 1 并行）
Phase 3  CI/CD 与发布基建    1~2 天
Phase 4  发布运营            上线日 + 持续
─────────────────────────────────────
合计约 4~6 个工作日达到可公开发布状态
```

---

## Wikilinks

- [[opensource-project-practices-from-multica]] · [[opensource-project-practices-from-openhuman]] · [[opensource-project-practices-from-langflow]] — 工程治理参照系
- [[opensource-project-practices-from-temporal]] · [[opensource-project-practices-from-caveman]] · [[opensource-practices-from-lobechat]] — 发布与社区运营参照系
- [[agentspace]] — 同类 TS monorepo agent 平台开源先例（Apache-2.0）
- [[flowise]] — vendored agentflow 的上游项目
- [[ai-workflow-landscape]] — 竞品定位坐标系
