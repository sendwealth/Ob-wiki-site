---
title: LM Evaluation Harness — 评估框架与最佳实践
created: 2026-05-10
updated: 2026-05-10
type: concept
tags: [llm, evaluation, benchmark, mlops]
source: https://github.com/EleutherAI/lm-evaluation-harness
author: EleutherAI (Leo Gao, Stella Biderman, Niklas Muennighoff 等)
version: v0.4.3+
---

# LM Evaluation Harness — 评估框架与最佳实践

> 来源：[EleutherAI/lm-evaluation-harness](https://github.com/EleutherAI/lm-evaluation-harness) — 12.5k stars，4021 commits，HF Open LLM Leaderboard 后端

## 一句话总结

开源 LLM 评估的行业标准框架，支持 60+ 学术 benchmark、200+ 子任务，兼容几乎所有模型后端（HF/vLLM/SGLang/API/GGUF/Megatron 等）。

---

## 核心架构

### 安装（2025.12 重构后按需安装）

```bash
pip install lm_eval                           # 核心框架（不含 torch/transformers）
pip install "lm_eval[hf]"                    # HuggingFace 后端
pip install "lm_eval[vllm]"                  # vLLM 后端
pip install "lm_eval[api]"                   # API 模型（OpenAI/Anthropic/本地服务器）
pip install "lm_eval[hf,vllm,api]"           # 多后端
```

### CLI（2025.12 子命令重构）

```bash
lm-eval run   # 运行评估
lm-eval ls    # 列出可用任务/标签/分组
lm-eval validate  # 验证任务配置
```

### 基本用法

```bash
# HF 模型
lm_eval --model hf --model_args pretrained=gpt2 --tasks hellaswag --batch_size 8

# vLLM（推荐用于大规模评估）
lm_eval --model vllm --model_args pretrained=meta-llama/Llama-3-70B,tensor_parallel_size=4 \
  --tasks mmlu --batch_size auto

# API 模型
lm_eval --model openai-chat-completions --model_args model=gpt-4o \
  --tasks gsm8k --limit 100

# 本地 OpenAI 兼容服务器
lm_eval --model local-chat-completions \
  --model_args model=my-model,base_url=http://localhost:8000/v1/chat/completions \
  --tasks hellaswag

# GGUF 量化模型
lm_eval --model hf \
  --model_args pretrained=/path/to/gguf,gguf_file=model.gguf,tokenizer=/path/to/tokenizer \
  --tasks hellaswag
```

---

## 任务系统

### 任务定义（YAML 配置）

每个任务由 YAML 文件定义，核心字段：

```yaml
task: my_task
dataset_path: dataset_name
dataset_name: subset_name
output_type: multiple_choice  # generate_until | loglikelihood | loglikelihood_rolling
test_split: test
doc_to_text: "{{question}}\nA. {{choices[0]}}\nB. {{choices[1]}}\nC. {{choices[2]}}\nD. {{choices[3]}}\nAnswer:"
doc_to_target: answer
metric_list:
  - metric: acc
    aggregation: mean
    higher_is_better: true
  - metric: acc_norm
    aggregation: mean
    higher_is_better: true
fewshot_config:
  sampler: first_n
  samples: [...]
```

### output_type 四种类型

| 类型 | 说明 | 适用场景 |
|------|------|---------|
| `multiple_choice` | 计算 loglikelihood 选最优选项 | 选择题（MMLU, ARC） |
| `generate_until` | 自回归生成直到停止符 | 开放生成（GSM8k, HumanEval） |
| `loglikelihood` | 计算文本 log 概率 | 语言建模（LAMBADA） |
| `loglikelihood_rolling` | 滑动窗口 log 概率 | 困惑度评估（Perplexity） |

### 任务继承与组合

```yaml
# 任务组：一次运行多个子任务
group: my_benchmark
task:
  - task_a
  - task_b
  - task_c
```

支持通配符：`--tasks lambada_openai_mt_*` 匹配所有语言变体。

### 主要任务套件

| 套件 | 覆盖领域 | 任务数 |
|------|---------|-------|
| MMLU / MMLU-Pro | 57学科多选题 | 57+ |
| Open LLM Leaderboard | ARC/HellaSwag/MMLU/TruthfulQA/WInogrande/GSM8k | 6 |
| BIG-Bench Hard (BBH) | 困难推理 | 27 |
| GSM8k | 数学应用题 | 1 |
| HumanEval | 代码生成 | 1 |
| TruthfulQA | 事实准确性 | 1 |
| Belebele | 多语言阅读理解 | 122语言 |
| IFEval | 指令遵循 | 1 |

---

## 最佳实践

### 1. 模型后端选择

| 场景 | 推荐后端 | 原因 |
|------|---------|------|
| 单 GPU 小模型 | `hf` | 简单直接 |
| 大模型多 GPU | `vllm` | 最快，连续批处理 |
| API 评估 | `local-completions` | 兼容 OpenAI 格式 |
| 量化模型 | `hf` + GGUF | 支持 llama.cpp 量化 |
| 超大模型 | `vllm` + tensor_parallel | 分布式推理 |

### 2. Few-shot 设置

```bash
# 标准设置（与 Open LLM Leaderboard 对齐）
--num_fewshot 0    # GSM8k, TruthfulQA
--num_fewshot 5    # ARC, HellaSwag
--num_fewshot 25   # MMLU (原论文)
--num_fewshot 10   # MMLU (Leaderboard 版本)
```

**最佳实践**：报告结果时必须说明 few-shot 数量。不同数量之间不可比较。

### 3. 评估速度优化

```bash
# vLLM + 自动批大小（推荐）
--model vllm --batch_size auto --model_args max_model_len=4096

# HF 数据并行
accelerate launch -m lm_eval --model hf --batch_size 16

# HF 原生 Tensor Parallelism（新功能）
torchrun --nproc-per-node=4 -m lm_eval --model hf \
  --model_args pretrained=model,tp_plan=auto

# 缓存结果断点续评
--use_cache /path/to/cache_
--cache_requests true
```

### 4. 结果可复现

```bash
# 固定种子
--seed 42
# 或精确控制
--seed 0,1234,1234,1234  # python,numpy,torch,fewshot

# 记录样本
--log_samples --output_path results/

# 数据完整性校验
--check_integrity
```

### 5. 自定义任务流程

```bash
# 1. 创建 YAML 配置
# 参考 templates/new_yaml_task/ 模板

# 2. 验证配置
lm-eval validate --include_path /path/to/my/tasks

# 3. 先用 --limit 测试
lm_eval --model hf --model_args pretrained=gpt2 \
  --tasks my_task --include_path /path/to/my/tasks --limit 10

# 4. 检查 prompt 输出
--write_out  # 打印前几个样本的完整 prompt

# 5. 全量运行
lm_eval --model hf --model_args pretrained=my_model \
  --tasks my_task --include_path /path/to/my/tasks --log_samples
```

### 6. Chain-of-Thought 评估

```bash
# 对 Qwen3/DeepSeek-R1 等思考模型
lm_eval run --model vllm \
  --model_args pretrained=Qwen/Qwen3-32B,enable_thinking=True,think_end_token="</thinkmt>" \
  --tasks gsm8k --apply_chat_template
```

### 7. 结果追踪

```bash
# Weights & Biases
--wandb_args project=my-eval,name=run-1 --log_samples

# HuggingFace Hub
--hf_hub_log_args hub_results_org=my-org,push_results_to_hub=True

# 本地 JSON
--output_path results/ --log_samples
```

---

## 常见坑点

### 1. Prompt 格式影响巨大
- 同一任务不同 prompt 可以导致 10-30% 分数差异
- 使用 `--apply_chat_template` 对 chat 模型至关重要
- 报告结果时必须说明 prompt 格式

### 2. API 模型的限制
- `generate_until` 类任务可用，`loglikelihood` 类需要 API 返回 logprobs
- OpenAI ChatCompletions 不支持 logprobs → 只能用 generate_until 任务
- 先用 `--limit 10` 检查答案抽取是否正常

### 3. 多选题的对齐问题
- `multiple_choice` 类型计算每个选项的 loglikelihood
- 某些 tokenizer 的空格处理会导致分数偏差
- vLLM 和 HF 的结果可能有微小差异（HF 为参考标准）

### 4. 数据污染
- 使用 `--check_integrity` 校验数据完整性
- 框架内置 decontamination 模块（`lm_eval/decontamination/`）
- 评估训练数据中是否包含测试集样本

### 5. 统计显著性
- 小测试集上分数波动大（如 ARC-Easy 只有 ~2.5k 题）
- 建议多次运行不同 seed 取平均
- 报告时附上 confidence interval

### 6. GGUF tokenizer 陷阱
- 不提供 tokenizer 时 HF 会从 GGUF 重建，可能耗时数小时
- 始终用 `tokenizer=/path/to/tokenizer` 单独指定

---

## 竞品对比

| 框架 | 维护者 | 特点 | 适合场景 |
|------|--------|------|---------|
| **lm-eval-harness** | EleutherAI | 最全的任务覆盖，HF Leaderboard 后端 | 标准学术评估 |
| **lighteval** | HuggingFace | 与 HF 生态深度集成，轻量 | 快速评估 + HF Hub |
| **OpenCompass** | OpenGVLab | 中文任务覆盖好，多模态支持 | 中文模型评估 |
| **HELM** | Stanford CRFM | 严格标准化，详细分析报告 | 学术研究 |
| **lmms-eval** | Evolving LMMs-Lab | 多模态专用 | VLM 评估 |

---

## 与"一人公司 + AI Agent"方向的关系

1. **评估驱动开发**：fine-tune 或 RL 训练后用 harness 验证效果，形成闭环
2. **自定义任务**：为自己的业务场景创建 eval task，量化模型在目标领域的表现
3. **模型选型**：用标准 benchmark 快速筛选候选模型
4. **自动化 CI**：集成到训练 pipeline，每次迭代自动跑 eval

---

## 引用

```bibtex
@misc{eval-harness,
  author = {Gao, Leo and Tow, Jonathan and others},
  title = {The Language Model Evaluation Harness},
  year = {2024},
  doi = {10.5281/zenodo.12608602}
}
```
