---
title: llama.cpp
created: 2026-06-28
updated: 2026-06-28
type: entity
tags: [product, llm, inference, cpp, local, open-source, foundational]
sources:
  - https://github.com/ggml-org/llama.cpp
  - https://github.com/ggml-org/ggml
confidence: high
---

# llama.cpp — 纯 C/C++ 高性能 LLM 推理引擎

> 仓库地址：https://github.com/ggml-org/llama.cpp
> 组织：ggml-org（原 ggerganov 个人项目，现已发展为独立组织）
> 定位：**用纯 C/C++ 实现的、面向本地与云端的高性能 LLM 推理引擎**
> 当前规模：⭐ 118k+ Stars · 20k Forks · 9800+ Commits（截至 2025 年）

---

## 一、项目概述

### 1.1 是什么

llama.cpp 是一个**零依赖、纯 C/C++ 编写**的大语言模型推理框架。核心目标：

> Enable LLM inference with minimal setup and state-of-the-art performance on a wide range of hardware — locally and in the cloud.

最初是 Georgi Gerganov 在 2023 年初用周末时间把 Meta 的 LLaMA 模型用 C++ 重写出来的产物，因极致的可移植性、低资源占用和高性能，迅速成为开源 LLM 生态的基石。

### 1.2 解决什么问题

| 痛点 | llama.cpp 的解法 |
|---|---|
| PyTorch/HF 生态依赖庞大（几个 GB 的 Python 环境） | 纯 C/C++，**零外部依赖**，编译产物只有几 MB |
| 需要高端 GPU（A100/H100）才能跑 | **CPU 即可推理**，并支持 1.5~8bit 量化把显存/内存占用降到原模型的 1/4~1/8 |
| 跨平台部署困难 | 一份代码覆盖 macOS / Linux / Windows / Android / 嵌入式 / 浏览器（WebGPU）|
| 商业闭源推理引擎（vLLM、TensorRT-LLM）门槛高 | MIT 协议开源，API 简洁，可嵌入任何 C/C++ 项目 |

### 1.3 项目结构一览

```
llama.cpp/
├── ggml/              # 底层张量计算库（独立子项目，可单独使用）
│   ├── include/ggml.h # ggml 核心 API
│   └── src/           # 各后端实现：ggml-cuda / ggml-metal / ggml-vulkan ...
├── gguf-py/           # GGUF 文件格式的 Python 工具
├── include/llama.h    # libllama C API（对外稳定接口）
├── src/               # llama 推理引擎核心实现
├── common/            # CLI 公共代码（参数解析、采样器等）
├── tools/             # 可执行工具
│   ├── cli/           # llama-cli        交互式对话
│   ├── server/        # llama-server     OpenAI 兼容 HTTP 服务
│   ├── perplexity/    # llama-perplexity 模型质量评估
│   ├── bench/         # llama-bench      性能基准测试
│   ├── quantize/      # llama-quantize   模型量化
│   └── ...
├── conversion/        # HF/PyTorch → GGUF 转换脚本
├── examples/          # 最小集成示例（如 llama-simple）
├── grammars/          # GBNF 语法定义（约束输出）
└── docs/              # 各类文档
```

### 1.4 双层关系：llama.cpp 与 ggml

- **ggml**：底层**通用张量数学库**（类似一个小型 PyTorch），定义张量、算子（matmul/attention/conv 等）和计算图，负责调度到 CPU/CUDA/Metal/Vulkan 等后端。
- **llama.cpp**：建立在 ggml 之上的 **LLM 推理框架**，实现了 Transformer 架构、各种主流模型的计算图、分词器、采样器、KV cache 等高层逻辑。

两者现在都在 `ggml-org` 组织下，但 ggml 被设计为可独立服务于其他领域（如 Stable Diffusion 的 `sd.cpp`、语音模型 `whisper.cpp` 等）。

---

## 二、核心架构

### 2.1 三层抽象

```
┌──────────────────────────────────────────────┐
│  应用层：llama-cli / llama-server / 你的 App  │
├──────────────────────────────────────────────┤
│  libllama：模型加载 / Tokenizer / Sampler /   │
│            KV Cache / Graph Build / Sampling   │
├──────────────────────────────────────────────┤
│  ggml：张量库 + 计算图 + 后端调度              │
├────────┬────────┬────────┬────────┬──────────┤
│  CPU   │ CUDA  │ Metal │ Vulkan │ RPC/... │  ← 多后端
└────────┴────────┴────────┴────────┴──────────┘
```

### 2.2 GGUF 文件格式

GGUF（**GGML Universal File**）是 llama.cpp 专用的模型存储格式，取代了早期的 GGML/GGMF/GGJT。核心设计目标：

1. **单文件部署**：权重 + 元数据 + 词表全在一个 `.gguf` 文件里，便于分发。
2. **mmap 友好**：可直接 `mmap` 到内存，毫秒级加载（无解析开销）。
3. **可扩展**：用 key-value 结构存元数据，新增字段不破坏老模型兼容性。
4. **自包含**：加载模型时**无需用户提供任何额外信息**。

#### 文件结构

```
[ Magic: "GGUF" 4B ]
[ version: uint32 ]
[ tensor_count: uint64 ]
[ metadata_kv_count: uint64 ]
[ metadata_kv[] ... ]      ← 例如 general.architecture、tokenizer.ggml.model
[ tensor_info[] ... ]       ← 每个张量的 name/dimensions/type/offset
[ padding to alignment ]    ← 默认 32 字节对齐
[ tensor_data[] ... ]       ← 实际权重数据
```

#### 命名约定（推荐）

格式：`[<Sidecar>-]<BaseName>-<SizeLabel>-<Version>-<Encoding>[-<Type>][-<Shard>].gguf`

举例：
- `Mixtral-8x7B-v0.1-KQ2.gguf` → MoE 8 专家、70 亿参数、KQ2 编码
- `Hermes-2-Pro-Llama-3-8B-F16.gguf` → 8B、F16 浮点
- `mmproj-Qwen2-VL-7B-v1.0-F16.gguf` → **多模态投影器**（与基础模型配合使用）
- `Grok-100B-v1.0-Q4_0-00003-of-00009.gguf` → **分片文件**（第 3/9 片）

#### 关键元数据示例

```
general.architecture        = "llama"
general.name                = "Llama 3 8B Instruct"
llama.context_length        = 8192
llama.embedding_length      = 4096
llama.block_count           = 32
tokenizer.ggml.model        = "llama3"
tokenizer.ggml.tokens       = ["<s>", ..., "</s>"]   # 数组
quantize.imatrix.file       = "imatrix.dat"          # 重要度矩阵（量化参考）
```

### 2.3 ggml 张量库

ggml 是一个**极简的计算图框架**，核心 API 风格接近早期的 Torch：

```c
// 创建计算图上下文
struct ggml_init_params params = {.mem_size = 16*1024*1024};
struct ggml_context * ctx = ggml_init(params);

// 构建张量与算子（lazy，只构建图，不执行）
struct ggml_tensor * a = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, N, M);
struct ggml_tensor * b = ggml_new_tensor_2d(ctx, GGML_TYPE_F32, N, K);
struct ggml_tensor * c = ggml_mul_mat(ctx, a, b);

// 编译为 backend graph，再由对应 backend 执行
struct ggml_cgraph * graph = ggml_build_forward(c);
ggml_backend_graph_compute(backend, graph);
```

特点：
- **后端无关**：同一份计算图可调度到 CPU / CUDA / Metal / Vulkan。
- **算子注册机制**：每个后端各自实现一组算子，未实现的算子会回退（fallback）到 CPU。
- **零拷贝**：张量内存由 backend buffer 管理，跨设备传输最小化。

### 2.4 推理引擎设计

llama.cpp 的推理流程：

1. **模型加载**：解析 GGUF → 创建 backend buffers → mmap 权重 → 初始化 KV cache。
2. **Prompt 处理**（prompt processing / prefill）：批量吃进输入 token，并行度高、吞吐大。
3. **逐 token 生成**（decode）：每次产出一个 token，瓶颈是显存带宽（GEMV 操作）。
4. **采样**：logits → penalties → top_k → top_p → temperature → 选 token。
5. **KV Cache 管理**：滑动窗口、Flash Attention、量化压缩（如 Q8_0 KV）。

关键优化点：
- **Flash Attention**：减少 KV cache 访问，长上下文性能显著提升（`-fa` 默认 auto）。
- **Continuous Batching**：server 端动态拼 batch，多个用户共享 GPU。
- **Speculative Decoding**：用小模型（draft）预测几个 token，大模型批量验证，加速 2-3 倍。
- **权重 Repacking**：运行时把权重重排成 SIMD/张量核心友好的布局。

---

## 三、关键特性

### 3.1 量化方案（Quantization）

这是 llama.cpp 最大的杀手锏。它支持**1.5-bit 到 8-bit**的整数量化，让 70B 模型也能在单张消费级 GPU 上跑。

#### 主要量化类型

| 类型 | bits/权重 | 说明 | 适用场景 |
|---|---|---|---|
| `F16` / `BF16` | 16 | 半精度浮点 | 基线、追求质量 |
| `Q8_0` | 8.5 | int8 + scale | 几乎无损 |
| `Q6_K` | 6.5 | k-quant，质量优秀 | 质量优先 |
| `Q5_K_M` | 5.7 | 推荐平衡点 | 内存敏感 |
| **`Q4_K_M`** | **4.85** | **社区黄金标准** | **默认推荐** |
| `Q4_0` | 4.5 | 最老的 4bit 格式 | 老模型兼容 |
| `Q3_K_M` | 3.9 | 显著掉点 | 极限压缩 |
| `IQ2_XXS` / `IQ1_S` | ~2 / ~1.5 | importance-aware | 超低资源实验 |

#### K-Quant 命名规则

`Q<bit>_K_<variant>`，其中：
- `<bit>`：平均比特数（如 4、5、6）
- `_K`：表示使用 **block-wise mixed precision**（不同张量用不同精度，关键层精度更高）
- `<variant>`：`_S` (small) / `_M` (medium) / `_L` (large)，控制质量/体积权衡

**实战建议**：
- **首选 `Q4_K_M`**：质量损失几乎不可感知，体积约为 F16 的 1/3。
- 内存充足选 `Q5_K_M` 或 `Q6_K`。
- 不要低于 `Q3_K_M`，除非真的没内存。

#### 量化命令

```bash
# 把 HF 模型转成 GGUF（需要 Python 环境）
python conversion/convert_hf_to_gguf.py /path/to/hf-model --outtype f16 -o model-f16.gguf

# 再做整数量化
./build/bin/llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M
```

Hugging Face 还提供在线工具 `GGUF-my-repo`，无需本地环境即可转换量化。

### 3.2 CPU/GPU 推理

llama.cpp 的核心优势之一是**一套代码、CPU/GPU 通吃**：

- **纯 CPU**：利用 ARM NEON / x86 AVX2/AVX512/AMX 指令集。在 Apple Silicon 上尤其快（Accelerate + NEON）。
- **GPU 加速**：通过 `-ngl N`（n-gpu-layers）指定把多少层放到显存。`-ngl 999` 或 `auto` 表示全部。
- **CPU+GPU 混合**：当模型超过显存时，自动把溢出部分放 CPU/内存，**让大模型也能跑起来**（虽然慢）。
- **MoE 优化**：`-cmoe` 把 MoE 专家权重留在 CPU，只把注意力等放 GPU，省显存利器。

### 3.3 多后端支持（Backends）

llama.cpp 通过 ggml 的 backend 抽象支持**业界最全的硬件后端**：

| Backend | 目标硬件 | CMake 选项 |
|---|---|---|
| **Metal** | Apple Silicon（一等公民） | macOS 默认开启 |
| **CUDA** | NVIDIA GPU | `-DGGML_CUDA=ON` |
| **HIP** | AMD GPU | `-DGGML_HIP=ON` |
| **Vulkan** | 跨厂商 GPU（Intel/AMD/NVIDIA） | `-DGGML_VULKAN=ON` |
| **SYCL** | Intel GPU | `-DGGML_SYCL=ON` |
| **MUSA** | 摩尔线程 GPU | `-DGGML_MUSA=ON` |
| **CANN** | 华为昇腾 NPU | `-DGGML_CANN=ON` |
| **OpenCL** | Adreno GPU | `-DGGML_OPENCL=ON` |
| **BLAS** | 所有（OpenBLAS/MKL/Accelerate） | `-DGGML_BLAS=ON` |
| **ZenDNN** | AMD CPU | 专门优化 |
| **WebGPU** | 浏览器 | 通过 emscripten 编译 |
| **RPC** | 远程设备（分布式推理） | `-DGGML_RPC=ON` |
| OpenVINO | Intel CPU/GPU/NPU | 进行中 |
| zDNN | IBM Z / LinuxONE | 企业级 |

**多 GPU 分片模式**（`-sm`）：
- `layer`（默认）：层间流水线，跨 GPU 串行
- `row`：行级切分，多 GPU 并行算同一层
- `tensor`：实验性，张量级切分

### 3.4 其他重要特性

- **多模态**：支持视觉（LLaVA、Qwen-VL）、音频模型，server 提供 OpenAI 兼容的多模态 API。
- **Function Calling / Tool Use**：通过 `--jinja` 启用，支持工具调用。
- **GBNF Grammar**：用 BNF 风格语法约束输出，强制生成合法 JSON / 代码 / 特定格式。
- **Speculative Decoding**：`-md draft.gguf` 配合 draft 模型加速。
- **Embedding / Reranking**：可作为向量数据库的 embedding 服务。
- **LoRA 热加载**：`--lora` 运行时挂载 LoRA 适配器。

---

## 四、使用方法

### 4.1 安装

四种主流方式：

```bash
# 1. 包管理器（最快）
brew install llama.cpp          # macOS
conda install -c conda-forge llama.cpp
winget install llama.cpp        # Windows
nix profile install nixpkgs#llama.cpp

# 2. Docker
docker run -p 8080:8080 -v /path/to/models:/models \
  ghcr.io/ggml-org/llama.cpp:server -m /models/model.gguf --port 8080

# 3. 预编译二进制
# 从 https://github.com/ggml-org/llama.cpp/releases 下载

# 4. 源码编译（最灵活）
git clone https://github.com/ggml-org/llama.cpp
cd llama.cpp
cmake -B build -DGGML_CUDA=ON     # 按需开启后端
cmake --build build --config Release -j
```

### 4.2 获取模型

```bash
# 方式 A：直接从 Hugging Face 下载并运行（最简单）
llama-cli -hf ggml-org/gemma-3-1b-it-GGUF
llama-server -hf ggml-org/gemma-3-1b-it-GGUF:Q4_K_M   # 指定量化

# 方式 B：手动下载 GGUF
# 去 HF 搜 "*GGUF"，下载到本地
llama-cli -m /path/to/model.gguf
```

默认从 Hugging Face 下载，可通过环境变量 `MODEL_ENDPOINT` 切换到镜像源（如国内 hf-mirror）。

### 4.3 llama-cli 交互对话

```bash
# 自动识别 chat template，进入对话模式
llama-cli -m model.gguf

# 手动指定对话模板
llama-cli -m model.gguf -cnv --chat-template chatml

# 用语法约束输出 JSON
llama-cli -m model.gguf --grammar-file grammars/json.gbnf
```

### 4.4 llama-server（核心生产力工具）

这是**最常用的部署形态**——一个轻量级、OpenAI 兼容的 HTTP 服务。

```bash
# 启动（默认 8080 端口）
llama-server -m model.gguf --port 8080

# 常用参数
llama-server \
  -m model.gguf \
  --host 0.0.0.0 --port 8080 \
  -c 8192 \                 # 上下文长度
  -ngl 99 \                 # GPU 层数
  -t 8 \                    # CPU 线程
  -fa on \                  # Flash Attention
  --sm layer \              # 多 GPU 分片
  -sm row -ts 3,1 \         # 按 3:1 比例切分到两张卡
  -ctk q8_0 -ctv q8_0       # KV cache 量化，省显存
```

**主要 API 端点**（兼容 OpenAI）：

| 端点 | 用途 |
|---|---|
| `GET /health` | 健康检查（加载中返回 503） |
| `GET /v1/models` | 模型列表 |
| `POST /v1/chat/completions` | **对话补全**（OpenAI 兼容，支持流式） |
| `POST /v1/completions` | 文本补全 |
| `POST /v1/embeddings` | 向量嵌入 |
| `POST /v1/rerank` | 重排序 |
| `POST /completion` | 原生补全（非 OAI 格式，功能更全） |
| `POST /tokenize` `/detokenize` | 分词 |
| `GET /slots` | 推理槽状态（多用户监控） |

**直接用 OpenAI SDK 调用**：

```python
from openai import OpenAI
client = OpenAI(base_url="http://localhost:8080/v1", api_key="not-needed")

resp = client.chat.completions.create(
    model="local",
    messages=[{"role": "user", "content": "你好"}],
    stream=True,
)
for chunk in resp:
    print(chunk.choices[0].delta.content or "", end="")
```

浏览器访问 `http://localhost:8080` 还有**内置 Web UI**，无需任何前端开发即可体验。

### 4.5 其他工具

```bash
# 性能基准（看 t/s）
llama-bench -m model.gguf

# 困惑度评估（衡量模型质量）
llama-perplexity -m model.gguf -f corpus.txt

# 量化
llama-quantize model-f16.gguf model-Q4_K_M.gguf Q4_K_M

# 最小集成示例（开发者参考）
./llama-simple -m model.gguf -p "Once upon a time"
```

### 4.6 嵌入到 C/C++ 项目

```c
#include "llama.h"

int main() {
    llama_backend_init();
    llama_model_params mparams = llama_model_default_params();
    mparams.n_gpu_layers = 99;
    llama_model * model = llama_model_load_from_file("model.gguf", mparams);

    llama_context_params cparams = llama_context_default_params();
    cparams.n_ctx = 2048;
    llama_context * ctx = llama_init_from_model(model, cparams);

    // ... tokenize / decode / sampling / detokenize ...

    llama_free(ctx);
    llama_model_free(model);
    llama_backend_free();
    return 0;
}
```

---

## 五、性能调优速查

| 场景 | 优化手段 |
|---|---|
| 启动慢 | 用 mmap（默认开），避免 `--no-mmap` |
| 长上下文慢 | 必开 `-fa on`（Flash Attention） |
| 显存不够 | 降 `-ngl`、用 `-ctk q8_0 -ctv q8_0` 量化 KV、用更激进的模型量化 |
| MoE 模型显存爆炸 | `-cmoe` 把专家权重放 CPU |
| 多用户吞吐 | `llama-server` 默认开启 continuous batching |
| 单用户延迟 | 试 speculative decoding（`-md draft.gguf`） |
| 多 GPU 利用 | `-sm layer`（默认）或 `-sm row` + `-ts` |
| CPU 性能 | 编译时 `-DGGML_BLAS=ON`、确认 AVX2/AVX512 启用 |
| 编译慢 | 用 Ninja、加 `-j N`、装 ccache |

---

## 六、生态与延伸

### 6.1 上游 / 平行项目

- **ggml**（https://github.com/ggml-org/ggml）：底层张量库，独立演进。
- **whisper.cpp**：语音识别，基于 ggml。
- **stable-diffusion.cpp / sd.cpp**：图像生成。
- **llama.vscode / llama.vim**：编辑器内的 FIM 代码补全插件。

### 6.2 下游 / 集成

- **Ollama**：基于 llama.cpp 的封装，提供更友好的 CLI/REST。
- **LM Studio**：桌面 GUI 客户端。
- **Hugging Face Inference Endpoints / TGI**：云端原生支持 GGUF。
- **vLLM / SGLang**：与 llama.cpp 形成互补（vLLM 重吞吐，llama.cpp 重轻量）。
- **诸多 Agent 框架**（LangChain / LlamaIndex / AutoGen）都可通过 OpenAI 兼容 API 接入。

### 6.3 与 vLLM 的取舍

| 维度 | llama.cpp | vLLM |
|---|---|---|
| 语言 | C/C++ | Python + CUDA |
| 部署体积 | 极小（几 MB） | 大（含 PyTorch） |
| 硬件支持 | 极广（含 CPU、Apple、NPU） | 主要 NVIDIA GPU |
| 吞吐 | 中等 | 高（PagedAttention） |
| 模型格式 | GGUF | HF safetensors |
| 适用场景 | 边缘 / 本地 / 嵌入式 / 多硬件 | 数据中心高并发服务 |

---

## 七、实用建议

1. **MVP 阶段直接用 llama-server**：一行命令起 OpenAI 兼容服务，前端/Agent 代码无需改动，云端切本地零成本。
2. **量化选 Q4_K_M**：质量与体积的最佳平衡，几乎所有 GGUF 仓库都提供这个版本。
3. **macOS 开发机是绝佳选择**：Apple Silicon 上 Metal 后端性能极强，统一内存可以跑很大的模型，无需购买 GPU。
4. **私有化部署的终极方案**：客户机器无需 Python、无需联网，一个二进制 + 一个 GGUF 文件即可交付，特别适合 ToB 场景。
5. **关注 RPC backend**：可以实现"本地小模型 + 远端大模型"的混合推理架构，是未来 Agent 基础设施的方向。
6. **跟进 gpt-oss 等原生 MXFP4 模型**：llama.cpp 已原生支持 NVIDIA 的 MXFP4 格式，是低比特量化的新趋势。

## Wikilinks

- [[minimind-o]] — 超小规模端到端多模态模型，本地推理可搭配 llama.cpp 部署
- [[agent-zero]] — 自主 Agent 框架，本地模型推理常依赖 llama.cpp / Ollama
- [[agno]] — AI Agent 平台，可通过 OpenAI 兼容 API 接入 llama-server 作为本地模型后端

---

*最后更新：2025 年 6 月 · 基于 master 分支*
