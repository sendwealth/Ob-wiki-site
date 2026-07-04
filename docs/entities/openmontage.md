---
title: OpenMontage
created: 2026-07-04
updated: 2026-07-04
type: entity
tags: [agent, agentic-ai, video-production, open-source, python, remotion, ffmpeg, claude-code, cursor]
sources:
  - https://github.com/calesthio/OpenMontage
  - https://github.com/calesthio/OpenMontage/blob/main/AGENT_GUIDE.md
  - https://github.com/calesthio/OpenMontage/blob/main/docs/ARCHITECTURE.md
confidence: high
---

# OpenMontage

> **世界首个开源、Agentic（智能体驱动）的视频生产系统**。把 AI 编程助手（Claude Code / Cursor / Copilot / Windsurf / Codex）变成一整间视频制片厂——一句话需求，agent 自动完成调研、剧本、资产生成、剪辑、合成成片。

**仓库**：https://github.com/calesthio/OpenMontage
**协议**：AGPL-3.0　**语言**：Python + Node.js　**Stars**：32k+　**创建**：2026-03
**口号**：12 pipelines · 52 tools · 500+ agent skills

## 核心理念：Agent-First，没有代码编排器

这是 OpenMontage 最反常识、也最值得关注的设计：

> **"There is no code orchestrator. Your AI coding assistant IS the orchestrator."**

它**不是一个 SDK/库**让你写 Python 调用，而是把整套制片流程编码成「YAML 流水线清单 + Markdown 技能指令」，交给**你已有的 AI 编程助手**去读、去执行。Python 只提供**工具**（tools）和**持久化**，所有创作决策、编排逻辑、质检标准都活在可读的指令文件里。

这等于把"Agent Skill（智能体技能包）"这个范式推到了极致——不是给 Agent 一个工具，而是给 Agent 一整套**可读、可改、可审计的制片方法论**。

## 12 条流水线（Pipeline）

每条都是完整制片工作流：`research → proposal → script → scene_plan → assets → edit → compose`

| Pipeline | 产出 |
|----------|------|
| Animated Explainer | 带调研/旁白/配乐的科普解说 |
| Animation | 动效、kinetic typography |
| Avatar Spokesperson | 数字人演讲 |
| Cinematic | 电影感预告片/teaser |
| Clip Factory | 长视频切成一批短视频 |
| **Documentary Montage** | ⭐ 从免费素材库用 CLIP 语义检索剪辑真实纪录片 |
| Hybrid | 真实素材 + AI 生成画面 |
| Localization & Dub | 字幕/配音/翻译 |
| Podcast Repurpose | 播客高光 → 视频 |
| Screen Demo | 软件录屏讲解 |
| Talking Head | 真人演讲视频 |

> **Web 调研是一等公民**：写剧本前，agent 先跑 15-25+ 次网络搜索（YouTube / Reddit / HN / 新闻 / 学术），把视频建立在真实、最新的信息上，而不是幻觉。

## 三层知识架构（关键创新）

```
Layer 1: tools/ + pipeline_defs/   "存在什么" —— 可执行能力 + 编排
Layer 2: skills/                    "怎么用"   —— OpenMontage 约定与质量基线
Layer 3: .agents/skills/            "原理是啥" —— 外部技术深度知识包
```

每个 tool 声明它依赖哪些 Layer 3 技能。Agent 先读 L1 知道有什么，再读 L2 知道 OpenMontage 要求怎么用，需要时读 L3 拿到底层技术细节。**这是「技能路由」思想在大型工程项目里的成熟实践**。

## Backlot：活的故事板（Living Storyboard）

不只是聊天里看 agent "说了什么"，而是开一个本地看板**实时展示生产在发生什么**：阶段亮起、剧本以剧本页形式落下、场景卡在资产生成时闪烁、每个 provider 决策与花费都上墙。

- **Storyboard 是真实的审批闸门**：资产生成会在每场景的 contact sheet 上暂停（含 takes / prompt / 单资产成本 / 质量分），让你在渲染前而非渲染后审批画面。
- `python -m backlot open` 打开库；`▶ REPLAY RUN` 可按时间戳回放整条生产链。

## 质量门禁（Production-Grade Gates）

| 机制 | 作用 |
|------|------|
| **Delivery Promise** | 拦截"幻灯片式"渲染——承诺是视频就得是真视频 |
| **Pre-compose validation** | 渲染前校验 plan，不浪费 GPU |
| **Post-render self-review** | ffprobe + 抽帧 + 音频电平分析 + promise 核验 |
| **Scored selector** | 跨 7 维度（任务契合/质量/控制力/可靠性/成本/延迟/连续性）给每个 provider 打分，留可审计决策日志 |
| **Budget governance** | 执行前估成本、消费上限、逐动作审批阈值 |

## Provider 生态（无厂商锁定）

- **视频生成 14 家**：Kling / Runway Gen-4 / Veo 3 / Grok / Higgsfield / MiniMax / HeyGen + 本地 WAN2.1 / Hunyuan / CogVideo / LTX + 免费素材 Pexels/Pixabay/Wikimedia
- **图片 10 家**：FLUX / Imagen 4 / Grok / GPT Image 2 / Recraft / 本地 SD / ManimCE 数学动画 + 免费图库
- **TTS 4 家**：ElevenLabs / Google TTS（700+ 声音）/ OpenAI / **Piper（完全免费离线）**
- **音乐**：Suno / ElevenLabs Music & SFX
- **合成**：**Remotion**（React 编程式视频）或 **HyperFrames**（HTML/CSS/GSAP），运行时在 proposal 阶段锁定为 `render_runtime`，静默切换属治理违规

### 零 API Key 也能出真视频

| 能力 | 免费工具 |
|------|----------|
| 旁白 | Piper TTS（离线） |
| 素材 | Archive.org + NASA + Wikimedia + Pexels/Unsplash/Pixabay |
| 合成 | Remotion / HyperFrames |
| 后期 | FFmpeg |

三条免费路径：① 图像视频（Piper 旁白 + 图像 + Remotion 动画）② 本地角色动画（SVG rig + GSAP）③ **真实素材纪录片**（CLIP 检索免费素材库 → 时间线剪辑 → 渲染）。

## 与同类/相关范式的关系

- **vs 普通 AI 视频工具**：别人给你"一个 prompt 一个 clip"，OpenMontage 给你**端到端制片流水线**——同一个真实制片团队会走的结构化流程。
- **vs SDK/库**：它不是让你写代码，而是教 Agent 走流程。Agent Skill 范式在大型工程里的标杆案例。
- **可对标**：[[leaferjs]]（Canvas 端把"绘图语言标准"做厚）、[[design-as-code]]（设计↔代码范式）—— OpenMontage 是「**制片流程↔Agent 技能**」范式的代表。

## 学习路径

1. 读 [`AGENT_GUIDE.md`](https://github.com/calesthio/OpenMontage/blob/main/AGENT_GUIDE.md) 和 [`PROJECT_CONTEXT.md`](https://github.com/calesthio/OpenMontage/blob/main/PROJECT_CONTEXT.md) —— 契约优先
2. clone 后 `make setup`，跑 `make demo` 看零 Key 出片
3. 把每个视频请求当成**流水线选择问题**：先选 pipeline → 读 manifest → 读 stage skill → 用 tools
4. 试 `PROMPT_GALLERY.md` 里带预期成本和成片示例的 prompt

## 相关页面

- [[leaferjs]] — 同样"把领域方法论做厚"的渲染引擎，可对照「绘图语言标准」与「制片流水线标准」两种范式
- [[design-as-code]] — 设计系统编码为纯文本，OpenMontage 把制片方法论编码为 YAML+Markdown 是同类思想
- [[awesome-design-md]] — 设计↔代码范式集合，OpenMontage 是「流程↔代码」范式的延伸
