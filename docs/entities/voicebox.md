---
title: Voicebox — 开源 AI 语音工作室
created: 2026-05-13
updated: 2026-06-28
type: entity
tags: [ai, voice, tts, stt, mcp-server, desktop-app, local-first]
sources: [raw/voicebox/readme.md]
confidence: high
---

# Voicebox

> 25.5K⭐ | 开源 AI 语音工作室：克隆、口述、创作，全栈本地运行

*GitHub: https://github.com/jamiepine/voicebox | Author: Jamie Pine | License: MIT*
*官网: https://voicebox.sh | 文档: https://docs.voicebox.sh*

## Overview

Voicebox 是一个 **本地优先** 的 AI 语音工作室，ElevenLabs + WisprFlow 的开源替代品。克隆任何声音（几秒音频），23 种语言语音合成，全局热键听写，MCP Agent 语音输出。

**核心**: 完整的语音 I/O 栈，全部在本地运行，数据不离开你的机器。

**数据**: 25,510 ⭐ | Tauri (Rust) + React + FastAPI (Python) | MIT License

## Key facts

- **7 个 TTS 引擎**: Qwen3-TTS, Qwen CustomVoice, LuxTTS, Chatterbox Multilingual/Turbo, HumeAI TADA, Kokoro
- **23 种语言**: 英语、中文、日语、阿拉伯语、印地语、斯瓦希里语等
- **零样本声音克隆**: 几秒音频即可克隆
- **50+ 预设声音**: Kokoro + Qwen CustomVoice 策展
- **全局听写**: 热键按住说话，松开自动粘贴到任何文本框（macOS）
- **MCP 服务器**: `voicebox.speak` 一行调用让任何 Agent 用你克隆的声音说话
- **Voice Personalities**: 给声音附加人格，本地 LLM 重写后 TTS
- **8 种音频效果**: Pitch Shift, Reverb, Delay, Chorus, Compressor 等
- **Stories 编辑器**: 多轨道时间线，对话/播客/叙事
- **全平台**: macOS (MLX/Metal), Windows (CUDA), Linux, AMD ROCm, Intel Arc, Docker

## 7 个 TTS 引擎

| 引擎 | 语言数 | 特点 |
|------|--------|------|
| **Qwen3-TTS** (0.6B/1.7B) | 10 | 高质量多语言克隆，语速/音量指令控制 |
| **Qwen CustomVoice** | 10 | 9 个预设声音，自然语言控制，无需参考音频 |
| **LuxTTS** | EN | 轻量（~1GB VRAM），48kHz，CPU 150x 实时 |
| **Chatterbox Multilingual** | 23 | 最广语言覆盖 |
| **Chatterbox Turbo** | EN | 350M 快速模型，支持 `[laugh]` `[sigh]` 情感标签 |
| **TADA** (1B/3B) | 10 | HumeAI 语音语言模型，700s+ 连贯音频 |
| **Kokoro** | 8 | 82M 微型模型，CPU 快速推理，50 预设声音 |

## 语音 I/O 全栈

### 输入（Speech → Text）
- **全局听写**: 可配置热键，按住说话/点击切换
- **macOS 自动粘贴**: Accessibility 验证的文本注入，原子化剪贴板恢复
- **应用内麦克风**: 每个 Voicebox 文本框都有麦克风按钮
- **Whisper STT**: Base/Small/Medium/Large/Turbo，MLX (Apple Silicon) 或 PyTorch
- **LLM 精炼**: 可选清理 "嗯"、口吃、误起音

### 输出（Text → Speech）
- **无限长度**: 自动分句 + 交叉淡入淡出，最大 50,000 字符
- **版本管理**: Original / Effects 版本 / Takes（重新生成）
- **异步队列**: 非阻塞生成，串行执行避免 GPU 竞争
- **后处理效果**: 8 种音频效果，4 个内置预设

### Agent 语音（MCP）
```ts
// 任何 MCP-aware Agent:
await voicebox.speak({
  text: "部署完成。",
  profile: "Morgan",
  personality: true,  // 通过人格 LLM 重写
});
```

4 个 MCP 工具: `voicebox.speak`, `voicebox.transcribe`, `voicebox.list_captures`, `voicebox.list_profiles`

**Per-agent 声音绑定**: Claude Code → Morgan, Cursor → Scarlett，听声辨 Agent

### Voice Personalities
- 给声音附加自由格式人格描述
- **Compose**: 随机生成符合人格的台词
- **Speak in character**: 输入文本 → 人格 LLM 重写 → TTS
- 本地 Qwen3 (0.6B/1.7B/4B) 驱动，一个 GPU 内存占用

## REST API

```bash
# 生成语音
curl -X POST http://127.0.0.1:17493/generate \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "profile_id": "abc123"}'

# Agent 语音输出
curl -X POST http://127.0.0.1:17493/speak \
  -d '{"text": "Deploy complete.", "profile": "Morgan"}'

# 转录
curl -X POST http://127.0.0.1:17493/transcribe \
  -F "audio=@recording.wav" -F "model=whisper-turbo"
```

## 技术栈

| 层 | 技术 |
|----|------|
| 桌面应用 | Tauri (Rust) |
| 前端 | React + TypeScript + Tailwind |
| 后端 | FastAPI (Python) |
| TTS | 7 引擎（见上表） |
| STT | Whisper / Whisper Turbo |
| 本地 LLM | Qwen3 (0.6B/1.7B/4B) |
| MCP | FastMCP (HTTP + stdio) |
| 效果 | Pedalboard (Spotify) |
| 推理 | MLX (Apple Silicon) / PyTorch (CUDA/ROCm/CPU) |
| 数据库 | SQLite |

## GPU 支持

| 平台 | 后端 | 备注 |
|------|------|------|
| macOS (Apple Silicon) | MLX (Metal) | Neural Engine 4-5x 加速 |
| Windows/Linux (NVIDIA) | PyTorch (CUDA) | 自动下载 CUDA |
| Linux (AMD) | PyTorch (ROCm) | 自动配置 HSA_OVERRIDE |
| Windows (any GPU) | DirectML | 通用 Windows GPU |
| Intel Arc | IPEX/XPU | Intel 独显 |
| Any | CPU | 通用，较慢 |

## Roadmap 亮点

- Windows/Linux 自动粘贴
- STT 引擎扩展: Parakeet v3, Qwen3-ASR
- 流式转录: WebSocket `/transcribe/stream`
- 端到端语音 LLM: Moshi, GLM-4-Voice, Qwen2.5 Omni
- Voice Design: 从文字描述创建新声音
- 插件架构

## 最新动态（截至 2026-06-28）

> [!note] 2026 年初开源语音工作室黑马，Qwen3-TTS 驱动
> Voicebox 2026-02-04 首发，4 周内冲到 **11K+ stars**，成为 2026 年初开源语音品类的 breakout 项目。核心卖点是"本地优先 + MCP for agents"——把语音 I/O 变成 AI agent 的原生能力。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| Star | 25.5K | 持续增长（首发 4 周 11K+）|
| 定位 | ElevenLabs + WisprFlow 开源替代 | **"free and local alternative to ElevenLabs"**（官方叙事强化）|
| 核心引擎 | 7 TTS 引擎 | **Qwen3-TTS** 成为主打（几秒音频克隆）|
| 发布 | — | **2026-02-04 首发** |

### 生态信号
- **MCP for agents 是差异化**：多份评测指出 Voicebox 的独特性在于"让编码 agent 用你克隆的声音说话"——这是 ElevenLabs 不具备的 agent-native 视角
- 被列为 2026 开源 TTS/语音克隆代表（vs Chatterbox / Coqui XTTS / OpenVoice / Bark / RVC）
- 与 [[gstack]]/[[gbrain]]/[[ruflo]] 的配合场景被广泛讨论（agent 语音通知、会议摄入）

### 仍待观察
- 声音自然度与 ElevenLabs 商业方案的差距
- Roadmap 中的端到端语音 LLM（Moshi/GLM-4-Voice/Qwen2.5 Omni）落地进度

## Counter-arguments & data gaps

- Linux 预构建二进制尚未提供
- Windows/Linux 自动粘贴待实现
- 非英语 STT 质量可能不如专门方案
- 多引擎 GPU 内存占用较大
- 与 ElevenLabs 相比声音自然度可能仍有差距
- Chatterbox Turbo 的情感标签仅限英语

## 与其他工具的关系

- 可与 [[gstack]] Agent 配合：`/investigate` 结果语音播报
- 可与 [[gbrain]] 配合：会议记录 → voice input → brain ingestion
- 可与 [[ruflo]] Agent 配合：Agent 任务完成语音通知
- MCP 服务器使其成为任何 AI 工具的语音 I/O 层

See also: [[gstack]], [[gbrain]], [[ruflo]]
