---
title: MiniMind-O
created: 2026-05-23
updated: 2026-06-28
type: entity
tags: [ai, llm, omni, voice, tts, stt, open-source, pytorch, multimodal, edge]
sources: [~/Projects/minimind-o]
confidence: high
---

# MiniMind-O

> ~0.1B 超小规模端到端 Omni 多模态模型，单一权重支持文本/语音/图像三模态输入 + 文本+流式语音双通道输出，核心代码仅 2400 行纯 PyTorch 实现。

---

## 1. 项目概览

**作者**：龚景尧（Jingyao Gong），个人开发者
**发布**：2026-05-05，最后更新 2026-05-19
**系列**：MiniMind 系列第三作（继 MiniMind LLM 和 MiniMind-V 视觉语言模型）
**定位**：从零实现最小可复现的完整 Omni 闭环，让每个人都能从第一行代码读起、自己动手训练
**核心理念**：大道至简 — 以极小参数量实现完整多模态能力

**解决的问题**：GPT-4o 之后涌现 Mini-Omni2、Moshi、GLM-4-Voice 等开源 Omni 模型，但参数量庞大。社区缺乏一个足够轻量、链路完整、可从零训练的 Omni 起点。传统级联方案（ASR→LLM→TTS）延迟高且丢失情感/语气信息，MiniMind-O 在 hidden state 层面直接连通语音和文本。

## 2. 技术架构：Thinker-Talker 双路径

```
用户输入(文本/语音/图像)
        │
    ┌───▼───┐
    │Thinker│ ← 8层 Transformer, hidden=768
    │(理解) │    63.91M (Dense) / 198.42M (MoE)
    └──┬──┬─┘
       │  │  中间层Bridge (第3层)
       │  └──────────┐
       ▼             ▼
    文本输出    ┌────────┐
               │ Talker │ ← 4层 Transformer, 8 codebook heads
               │(语音)  │    47.05M (Dense)
               └───┬────┘
                   ▼
              流式24kHz语音
```

### 2.1 模块参数一览

| 模块 | 实现 | 配置 | 参数量(Dense/MoE) |
|---|---|---|---|
| Thinker | MiniMind Transformer | 8层, hidden=768 | 63.91M / 198.42M |
| Talker | 独立 MiniMind blocks | 4层, 8 codebook heads | 47.05M / 114.30M |
| Audio Projector | MMAudioProjector (2层MLP) | 512→768 | 0.99M |
| Vision Projector | MMVisionProjector (2层MLP) | 768→768 | 1.18M |
| Audio Encoder (冻结) | SenseVoice-Small | 16kHz语音特征 | 234.00M |
| Vision Encoder (冻结) | SigLIP2 base-p32-256 | 256×256, 64 tokens | 94.55M |
| Speech Codec (冻结) | Mimi | 8 codebooks, 12.5Hz, 24kHz | 96.15M |
| Speaker Condition | CAM++ embedding | 192维说话人向量 | 预计算 |

运行时总加载 ~538M（Dense）/ ~740M（MoE），其中 ~425M 是冻结外部模型。

### 2.2 核心技术创新

1. **中间层 Bridge**：从 Thinker 第3层（`bridge_layer = num_hidden_layers // 2 - 1`）传递表征给 Talker，而非首尾层。中间层已融合跨模态信息但未被 LM head 过度塑形
2. **MTP Audio Head（TalkerHead）**：共享主体 + 8个轻量 adapter（rank=256），同时预测 8层 codebook，避免为每层复制完整参数
3. **TalkerEmbedding**：同理，音频 embedding 也采用共享主体 + adapter 设计
4. **延迟调度**：音频生成有1步延迟（`audio_step = step - 1`），Thinker 先出文本 token，Talker 随后补齐 Mimi codes
5. **text_scale / audio_scale**：Talker 输入是 Thinker 文本表征和音频 embedding 的加权混合，两个 scale 是可学习参数（初始 text=3.0, audio=1.0）

### 2.3 模型配置详情

**minimind-3o（Dense）**：可训练 113.13M
- Thinker: 8层, hidden=768, 8 heads, 4 KV heads, RoPE (theta=1e6, YaRN scaling)
- FFN: SwiGLU 激活
- 词汇量：6400（文本），2112（音频 = 2048 Mimi codes + 64 special tokens）
- Tied embedding（lm_head.weight = embed_tokens.weight）

**minimind-3o-moe**：总参数 314.89M，Active ~115.33M
- MoE: 4 experts, 1 expert per token, router aux loss coef=5e-4

## 3. 代码结构

```
minimind-o/
├── README.md                    # 中文文档 (679行，极详尽)
├── README_en.md                 # 英文文档
├── eval_omni.py                 # 推理入口 (244行)，CLI多模态评估
├── model/
│   ├── model_minimind.py        # 基座LLM (287行)
│   ├── model_omni.py            # Omni模型 (461行)
│   ├── tokenizer.json / tokenizer_config.json
│   ├── vad/silero_vad.onnx      # Silero VAD
│   └── speaker/                 # 音色 (5内置 + 7未见 + 克隆)
├── dataset/
│   ├── omni_dataset.py          # 数据集处理 (344行)，含7种数据增强
│   └── eval_omni/               # 评估样本
├── trainer/
│   ├── train_sft_omni.py        # 训练主逻辑 (264行)
│   ├── train.sh                 # 训练脚本
│   └── trainer_utils.py         # 工具函数 (201行)
├── scripts/
│   ├── web_demo_omni.py         # Gradio WebUI (294行)
│   └── convert_omni.py          # PyTorch↔Transformers 格式转换
└── webui/
    ├── web_demo.py              # Flask+WebSocket 实时交互 (503行)
    └── web_demo.html            # 前端页面
```

**核心代码仅 ~2400 行**，纯 PyTorch 原生实现，无第三方高层抽象依赖。

## 4. 训练管线

三阶段 SFT 逐步接入能力：

| 阶段 | 目标 | mini数据 | full数据 |
|---|---|---|---|
| sft_t2a | 文本→语音输出对齐 | ~470h | ~1636h |
| sft_a2a | 接入语音输入 | ~57h | ~423h |
| sft_i2t | 视觉路径对齐 | — | 图像I2T |

支持三种训练模式：`all`（全参数）、`audio_proj`（只训练音频投影层）、`vision_proj`（只训练视觉投影层）。

**数据增强**：变速、加噪、混响、SpecAugment 等 7 种策略 + Scheduled Sampling（训练时随机替换部分 GT，增强从错误中恢复能力）。

**数据来源**：VoiceAssistant-400K、UltraChat-300K-SLAM-Omni、Qwen3-TTS 合成数据等。

## 5. 核心功能

1. **文本→文本+语音** — 输入文本，同时输出文本回复和流式语音
2. **语音→文本+语音（A2A）** — 输入语音，理解语义后以语音回复
3. **图像→文本+语音（I2A）** — 输入图像，描述内容并以语音输出
4. **多模态混合输入** — 同时输入文本+语音+图像
5. **音色控制** — 5个内置音色 + 7个未见音色(zero-shot迁移) + 任意参考音频实时克隆
6. **流式语音生成** — 24kHz Mimi 解码器增量恢复波形
7. **实时交互** — VAD 语音活动检测 + Barge-in 实时打断，近似双工
8. **WebUI** — Gradio 版 + Flask WebSocket 电话模式（流式播放、打断、音色克隆）
9. **模型格式转换** — PyTorch ↔ HuggingFace Transformers 互转

## 6. 环境与硬件

- **Python 3.10** + PyTorch 2.6 + CUDA 12.2
- 关键库：transformers, funasr (SenseVoice), soundfile, librosa, gradio, flask, speechbrain, swanlab
- **推理**：支持 CPU；GPU 推荐 RTX 3090+
- **mini 训练**：单卡 3090，~2小时
- **full 训练**：4× RTX 3090，~4-5小时
- 作者配置：i9-10980XE, 128GB RAM, 8× RTX 3090
- 需下载 5 个外部模型：SenseVoice-Small、SigLIP2、Mimi、CAM++、基座 LLM 权重

## 7. 评估指标

- **CER/WER**：短句 dense 0.0897，与 Mini-Omni2 接近
- **音色克隆相似度**：CAM++ speaker embedding cosine similarity，seen 平均 ~0.65
- 短句（1-15词）CER: 0.053，中句（16-30词）CER: 0.133（弱于 Mini-Omni2 的 0.006）

## 8. 同类项目对比

| 维度 | MiniMind-O | Mini-Omni2 | Qwen3-Omni | GLM-4-Voice | Moshi |
|---|---|---|---|---|---|
| 参数量 | ~0.1B | ~0.5B | 数B级 | 数B级 | 7B |
| 训练门槛 | 单卡3090, 2h | 多卡 | 大集群 | 大集群 | 大集群 |
| 从零训练 | ✅ | ❌ | ❌ | ❌ | ❌ |
| 输入模态 | 文/音/图 | 文/音/图 | 文/音/图 | 文/音 | 文/音 |
| 语音输出 | 流式24kHz | 流式 | 流式 | 流式 | 流式 |
| 实时打断 | ✅ VAD | ✅ | ✅ | ✅ | ✅ |
| 音色克隆 | ✅ in-context | 有限 | 有限 | 有限 | 有限 |
| 代码行数 | ~2400 | 中等 | 庞大 | 庞大 | 庞大 |
| 文档质量 | 极高 | 中等 | 中等 | 中等 | 中等 |

**核心差异**：MiniMind-O 不追性能榜，追求最小可复现的完整 Omni 闭环。可读性、可训练性、可改造性上无可比拟。

## 9. 亮点与不足

> [!summary] 亮点
> - 极致轻量：0.1B 实现 Omni 全链路，单卡可训练
> - 代码极精炼：~2400 行纯 PyTorch，可读性极强
> - 文档极详尽：README 679 行，从原理到实践全覆盖
> - 完整开源：代码 + 权重 + 数据 + 技术报告（arXiv: 2605.03937）
> - 工程完备：VAD 实时打断、流式语音、音色克隆、WebSocket 电话模式
> - Talker-Talker 解耦设计：语言理解和语音生成独立可优化

> [!warning] 不足
> - 模型能力有限：0.06B LLM 主干无法与大型模型竞争复杂任务
> - 长句语音不稳定：16-30词段 CER 明显升高（0.133）
> - 音色克隆尚处 Beta：距产品级稳定性有差距
> - 缺乏高性能推理后端（无 vLLM/TensorRT）
> - 无测试覆盖

## 10. 适用场景

- **学术研究者** — 研究 Thinker-Talker 解耦、MTP codebook、Bridge layer 等架构设计
- **AI 入门学习者** — 从零训练能听能看能说的小模型，mini 数据集 + 2小时 = 极低门槛
- **边缘设备开发者** — 0.1B 可 CPU 推理，适合资源受限场景原型
- **Omni 原型开发者** — 快速验证新设计思路的理想实验平台
- **教学内容制作** — 技术报告 + 详尽 README + 干净代码 = 优质教程素材

---

## 最新动态（截至 2026-06-28）

> [!note] 持续作为"最小可复现 Omni 模型"的教育标杆
> MiniMind-O 2026 年保持活跃，核心价值（教学/复现）未变，但生态在扩展：技术报告上 arXiv、被 vLLM-Omni 社区讨论集成。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| 技术报告 | README | **arXiv 技术报告**（speech-native Omni，fully inspectable）|
| 架构文档 | Thinker-Talker | 明确为 **Thinker-Talker 架构**，0.3B-A0.1B 变体 |
| 生态 | 独立项目 | **vLLM-Omni 社区讨论集成**（issue #3399）|

### 生态信号
- 被业界定位为"目前开源的**最小完整 Omni 实现**之一"，研究/教学价值突出
- 与 [[voicebox]] 形成互补：MiniMind-O 是端到端 Omni 研究，Voicebox 是工程化语音工具栈
- Apache-2.0 + 配套数据集（Hugging Face），复现门槛极低

### 仍待观察
- 0.1B 规模的质量上限（vs 商业 Omni 模型）
- vLLM-Omni 集成能否落地为生产推理选项

## 相关页面

- [[voicebox]] — 开源 AI 语音工作室，7 TTS 引擎，可对比语音方案
- [[agent-world]] — Agent 世界模拟，可探索 Omni 模型作为 Agent 交互接口
- [[humanizer-skill]] — AI 味消除方法论，与 Omni 模型输出质量优化相关
