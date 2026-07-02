---
title: BitNet (bitnet.cpp)
created: 2026-05-16
updated: 2026-06-28
type: entity
tags: [ai, llm, quantization, 1-bit, inference, microsoft, cpu, gpu, edge]
sources:
  - https://github.com/microsoft/BitNet
  - https://arxiv.org/abs/2402.17764
  - https://arxiv.org/abs/2410.16144
  - https://arxiv.org/abs/2502.11880
confidence: high
see_also:
  - "[[llama.cpp]]"
  - "[[T-MAC]]"
---

# BitNet (bitnet.cpp)

> ⭐ 39K Stars | Microsoft Research | MIT License
> 1-bit LLM 推理框架 — 在 CPU/GPU 上快速、无损推理 1.58-bit 模型

## 概览

BitNet 是微软研究院的 **1-bit 大语言模型**项目，`bitnet.cpp` 是其官方推理框架。核心思想：将 LLM 权重量化到 **1.58 bit**（三值：-1, 0, +1），大幅降低模型大小和推理开销，同时保持精度。

**一句话**：让 100B 参数模型在单个 CPU 上以人类阅读速度运行。

## 核心创新

### 1.58-bit 量化
- 权重只有三个值：**-1, 0, +1**
- 模型大小缩小 **~10x**（相比 FP16）
- 推理时矩阵乘法变成加减法，无需乘法器

### 性能数据

**CPU 推理**（vs llama.cpp）：

| 平台 | 加速比 | 能耗降低 |
|------|--------|----------|
| ARM | 1.37x ~ 5.07x | 55.4% ~ 70.0% |
| x86 | 2.37x ~ 6.17x | 71.9% ~ 82.2% |

**GPU 推理**（A100 vs BF16）：最高 3.63x 加速

### 里程碑
- **100B BitNet b1.58** 在单个 CPU：5-7 tokens/s
- 2B 模型在 Apple M2 流畅运行

## 技术架构

```
bitnet.cpp (基于 llama.cpp)
├── CPU Kernels
│   ├── I2_S (x86 + ARM)
│   ├── TL1 (ARM)
│   └── TL2 (x86)
├── GPU Kernels (CUDA)
│   ├── W2A8 GEMV
│   ├── dp4a 加速
│   └── 16×32 block 优化
└── NPU (计划中)
```

## 官方模型

**BitNet-b1.58-2B-4T** — 2.4B 参数，4T tokens 训练

支持的社区模型：0.7B ~ 10B (Falcon3, Llama3 等)

## 快速开始

```bash
git clone --recursive https://github.com/microsoft/BitNet.git && cd BitNet
conda create -n bitnet-cpp python=3.9 && conda activate bitnet-cpp
pip install -r requirements.txt

# CPU 推理
huggingface-cli download microsoft/BitNet-b1.58-2B-4T-gguf --local-dir models/BitNet-b1.58-2B-4T
python setup_env.py -md models/BitNet-b1.58-2B-4T -q i2_s
python run_inference.py -m models/BitNet-b1.58-2B-4T/ggml-model-i2_s.gguf -p "You are a helpful assistant" -cnv
```

## 时间线

| 时间 | 事件 |
|------|------|
| 2023-10 | BitNet 原始论文 |
| 2024-02 | 1.58-bit 论文 |
| 2024-10 | **bitnet.cpp 1.0** |
| 2025-04 | 官方 2B 模型 |
| 2025-05 | GPU 内核 |
| 2026-01 | CPU 优化 v2 |

## 最新动态（截至 2026-06-28）

> [!note] 2026 年主线：从"研究原型"走向"可部署基础设施"
> 2026 上半年没有新旗舰模型发布（仍是 **BitNet b1.58-2B-4T**），但工程化和生态在快速成熟。

- **推理优化持续**（2026-01-15）：官方框架更新 "BitNet CPU Inference Optimization v2"，进一步压榨 CPU 内核性能。微软研究院同期发布《1-bit AI Infra》系列论文，聚焦 ternary 模型在 CPU 上的 fast & lossless 推理内核。
- **官方站点独立**：上线 [bitnet.live](https://bitnet.live/)，主张 **16× memory reduction**，从 GitHub 项目升级为有独立品牌的基础设施产品。
- **微调生态成型**：Hugging Face 发布 [BitNet LoRA 微调指南](https://huggingface.co/blog/qvac/fabric-llm-finetune-bitnet)，支持异构边缘设备上的微调；社区 GUI（Electron-BitNet）跟进支持官方 2B-4T 模型。
- **Serverless 部署验证**：AWS 发布在 Lambda 上部署 BitNet 1.58-bit LLM 的教程，证明 1-bit 模型适合 serverless 冷启动场景（小体积 + CPU 友好）。
- **仍待突破**：官方最大模型仍卡在 2.4B；NPU 支持仍"计划中"；不支持后量化（只能用原生的 1.58-bit 训练模型）。

## 应用场景

1. **边缘设备** — 手机/IoT 无需 GPU
2. **本地 LLM** — CPU 即可跑
3. **大规模部署** — 成本降 10x
4. **绿色 AI** — 能耗降 70-82%

## 限制

- 只支持 1.58-bit 训练的模型（不能后量化）
- 官方最大仅 2.4B
- NPU 支持待开发

---
*学习时间: 2026-05-16 | 最新动态更新: 2026-06-28*

## 应用场景

1. **边缘设备** — 手机/IoT 无需 GPU
2. **本地 LLM** — CPU 即可跑
3. **大规模部署** — 成本降 10x
4. **绿色 AI** — 能耗降 70-82%

## 限制

- 只支持 1.58-bit 训练的模型（不能后量化）
- 官方最大仅 2.4B
- NPU 支持待开发

---
*学习时间: 2026-05-16*
