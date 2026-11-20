---
title: "Linger: 开源本地个人 AI Agent（Claude 级大脑跑在你的电脑上）"
created: 2026-11-20
updated: 2026-11-20
type: entity
tags: [ai-agent, local-inference, moe, personal-assistant, memory, open-source, product, active]
sources: [https://github.com/simplexai-labs/linger, ~/Projects/linger]
confidence: high
---

> [[browser-use]] | [[superpowers]] | [[agentspace]] | [[llama-cpp]]

# Linger 深度解析

Linger（simplexai-labs/linger）是一个开源的**本地个人 Agent**：一个 "Claude 级大脑" 完全运行在你自己的 Mac/PC 上，零 token 费用、数据不出设备。核心卖点是"忠诚的 AI 侧边伴"——它记住重要的事、主动推进工作、并和你的邮件/日历/Slack/浏览器深度集成。

## 1. 产品定位

- **本地推理的完整 Agent 体验**：不只是聊天，而是带工具、记忆、主动性的个人助理（对标 Grok Bot 的本地版）
- **消费级硬件可跑**：125B MoE 模型跑在 12 GB GPU + 64 GB RAM 的普通机器上
- **人在环中的安全模型**：Agent 用浏览器/发邮件前需要用户批准
- **自托管**：桌面应用（一人一机）或 Docker Compose（多机共享服务器）

## 2. 核心功能

| 功能 | 说明 |
|---|---|
| **本地模型** | 125B Qwen3.8-Flash-Next 在 12 GB 卡上 45.5 tok/s（12 GB RTX 3060） |
| **Wiki 与记忆** | LoCoMo 记忆基准 95%（超过 Zep 94.7%、Mem0 92.5%、OpenAI Memory 52.9%）；每晚把邮件/聊天/会议整理成 wiki 页面，"告诉一个 Agent，所有 Agent 都知道" |
| **主动式 Another Me** | 监视收件箱/日历/Slack，只在需要时开口；每晚 "Dreaming" 复盘自己的消息效果并**改写决策规则**（隐式强化：同类事件被拒绝两次→成规则；直接说一次→立即成规则），无需重训练 |
| **桌面与浏览器** | Agent 打开本机已登录的应用，像人一样点击输入（基于 Cua）；可操作日常 Chrome |
| **Agent 团队** | 一份 `team.md` 统一多个 Agent 的计划，缺的 Agent 现场创建 |
| **任务委派** | 长任务交给自己的后台副本，聊天不中断 |
| **模型调度** | 多 Agent 共享一个本地模型，前台工作优先、后台排队 |
| **BYO 运行时** | Claude Code / Codex / Pi 作为运行时，用本地模型或你已有的订阅 |
| **语音** | LiveKit 承载音频，会议录音+实时转写，追问内容并把后续交给 Another Me |

## 3. 技术架构

```
┌─ apps/web ──────── React/Vite 产品客户端（数据全部来自 TeamHub）
┌─ apps/teamhub ──── Go 服务：Account / Room / Work Item / 协作状态持久化
                     └─ River 跑后台任务；自带 teamhub-account CLI
┌─ apps/node-services 单 Node 进程多角色（NODE_SERVICES_ROLES）:
   ├─ agent    Agent 生命周期、Runtime 执行、TeamHub 回调
   ├─ memory   记忆（源自 Hindsight 的抽取与搜索）
   ├─ llm-wiki LLM Wiki 服务
   ├─ document Hocuspocus/Yjs + BlockNote 文档协同（独立端口，
   │           直接读写 TeamHub 库的 document_bodies 表）
   └─ voice    监督 voice-runtime 的隔离 ASR/录音/Live workers
┌─ apps/computer ─── 本地 Computer Daemon（Go）：把 Room 消息/文件带给 Runtime，
                     所有动作过 Guardrail 后交给 Cua/Playwright/Shell
┌─ apps/desktop ─── 桌面应用（macOS arm64 / Win x64 / Linux x64）
└─ packages/ ─────── document-files, document-model, knowledge-format,
                     local-installation, service-kit（共享 TS 工具）
```

- **Agent 侧**：Agent 在自己的 workspace 工作，直接调 LLM Gateway，通过 teamhub CLI 与 Room/Chat 交互；系统提示 + 5 个内置 Skill 教会 Agent 用 CLI
- **数据流**：用户消息 → provider_ready 路径是关键延迟路径（PR 必须声明是否增加网络往返）
- **契约**：OpenAPI 组件 + contracts/codegen 代码生成；Go 错误统一走 `writeError`
- **规范**：仓库纯英文（`make check-repository-gate` 拒绝 CJK 字符）；Go 用 `slog`、Node 用注入的 `createJsonLogger`；配置只在单一 config 模块读环境变量

## 4. 关键上游依赖

| 项目 | 作用 |
|---|---|
| **PolyStrata**（simplexai-labs） | MoE 推理引擎：热门专家驻 GPU、常用在 RAM、冷门在 SSD，分层换入换出，大幅降低显存需求 |
| **Strata** | PolyStrata 底层的推理引擎，跑 Qwen3.8-Flash-Next |
| **Hindsight**（vectorize-io） | Agent 记忆的事实抽取与搜索 |
| **Cua**（trycua） | Agent 操作桌面应用 |
| **BlockNote + Yjs + Hocuspocus** | 人和 Agent 共同编辑的文档 |
| **LiveKit** | 语音/会议音频 |
| **River** | TeamHub 后台任务队列 |

## 5. 模型推荐流水线（安装器）

1. 检测 GPU/VRAM/RAM/带宽
2. 过滤：权重+KV 需在内存内放下且上下文 ≥64K（MoE 专家可放 RAM）
3. 先按 SimplexAI 智能分排序、再按速度
4. 安装后**答对一道真实问题才算装好**

实验室规模：49 个模型 × 2 引擎 × IQ1_M–Q8_0 × 64K–256K 上下文，覆盖 NVIDIA 8–96 GB 和 Mac 16–128 GB，产出目录喂给安装器。

典型档位：Mac 24 GB → Qwen3.8-27B（≈Opus 4.5）；RTX 12 GB → Qwen3.8-Flash-Next（≈Opus 4.6）；RTX 24 GB → ≈Sonnet 4.6。

## 6. 设计亮点与权衡

- **规则即记忆的主动学习**：不做 RL/retraining，"学到的东西就是一短串规则"，可审计、可解释、成本极低 —— 与 [[superpowers]]/[[ecc]] 一类 skill-as-knowledge 的思路同源
- **个人 wiki 作为共享记忆**：一页一实体的图谱 + 每晚分节编辑并对旧页校验，是 [[adapted-6plus1-rss-obsidian-kb]] 所述"知识库作为 Agent 记忆"的产品化实践
- **显存分层换页**（GPU→RAM→SSD）换来了在消费卡上跑百亿级 MoE，代价是首 token 延迟（12 GB 档约 3 分钟首 token 的极端情况）
- **许可**：基于 Apache 2.0 的 Linger Open Source License，附加条件
- 与 [[agentspace]] 同属 "agent-native 工作台" 赛道，但 Linger 押注**本地推理 + 个人生活助理**，而非团队协作平台

## 7. 快速上手

- 桌面应用：下载 dmg/exe/tar.gz（macOS 未签名需 `xattr -dr com.apple.quarantine`）
- Docker Compose：`cp .env.example .env && docker compose up --build --detach --wait`，再 `teamhub-account create-owner` 建号
- 本地模型：`./scripts/install/install.sh`（macOS/Linux）或 `install.ps1`（Windows）
- 文档：docs.heylinger.com
