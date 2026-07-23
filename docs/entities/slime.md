---
title: slime
created: 2026-07-23
updated: 2026-07-23
type: entity
tags: [project, product, ai, platform, active]
sources: [https://github.com/THUDM/slime, https://thudm.github.io/slime/, https://lmsys.org/blog/2025-07-09-slime/]
confidence: high
---

# slime

> 清华 THUDM / Z.ai 出品的开源 LLM 后训练 RL 框架，基于 Megatron（训练）+ SGLang（rollout）+ Ray（编排），是 GLM-4.5 ~ GLM-5.2 全系列 SOTA 模型的官方 RL 训练基础设施。设计哲学：以 SGLang 为唯一 rollout 后端，避免多引擎抽象造成的能力稀释；把 Megatron/SGLang 参数原样透传，自身只聚焦 RL 数据流、权重同步与正确性检查。

---

## 核心价值主张

| 维度 | 说明 |
|---|---|
| 定位 | LLM post-training 的 **RL scaling 框架**，而非又一个 trainer / rollout service / agent framework 的缝合体 |
| 战场验证 | GLM-5.2 / 5.1 / 5 / 4.7 / 4.6 / 4.5 全系列官方训练框架；Qwen3 系列、DeepSeek V3/R1、Llama3 也支持 |
| 双能力 | ① 高性能训练（Megatron↔SGLang）；② 灵活数据生成（自定义 generate / reward / verifier / environment 即插即用） |
| 设计目标 | 让"训练 + rollout + 数据生成"在**同一条 train/rollout/data-buffer 路径**上相互强化，而非拆成互不相干的组件 |
| 核心克制 | 只选 SGLang 一个 rollout 后端，深度优化而非把多个推理引擎拍平成最小公分母 |

---

## 整体架构

```
                           train.py / train_async.py  (Ray driver)
                                      │
        ┌─────────────────────────────┼──────────────────────────────┐
        │                             │                              │
        ▼                             ▼                              ▼
 ┌──────────────┐            ┌────────────────┐            ┌──────────────────┐
 │  Placement   │            │   Actor        │            │   RolloutManager │
 │  Groups(Ray) │            │   (Megatron    │            │   (Ray actor,    │
 │  PACK策略    │            │    trainers)   │            │    0 GPU)        │
 │  按节点IP+   │            │  RayTrainGroup │            │  ┌────────────┐ │
 │  GPU排序     │            │  .async_train  │◄──权重同步──►│ │SGLang      │ │
 └──────────────┘            │  .update_weights│  update_   │ │ engines +  │ │
        │                     │  .save_model   │   weight   │ │ router     │ │
        │                     │  .create/offload│            │ └─────┬──────┘ │
        │                     └───────┬────────┘            └───────┼────────┘
        │                             │                             │
        │                     critic(可选)                           │
        │                             │                             │
        └─────────────────────────────┴─────────────────────────────┘
                                      │ Data Buffer (in-memory)
                                      ▼
                         ┌────────────────────────────┐
                         │  DataSource / 自定义       │
                         │  generate_rollout(args,    │
                         │    rollout_id, data_source)│
                         │  → RolloutFnTrainOutput    │
                         │  + reward/verifier/env     │
                         └────────────────────────────┘
```

三大模块（README 原话）：
- **training (Megatron)**：主训练流程，从 Data Buffer 读数据，训练后把参数同步到 rollout
- **rollout (SGLang + router)**：生成新数据（含 reward/verifier 输出）写回 Data Buffer；自定义 generate 可包装多轮/工具/环境/沙箱/verifier
- **data buffer**：桥接模块，管理 prompt 初始化、自定义数据、rollout 生成方法（含 agentic workflow，统一接口产出样本）

---

## 核心组件

### 1. Ray Placement Group（`slime/ray/placement_group.py`）

GPU 分配与拓扑排序的基石：
- `_create_placement_group(num_gpus)`：按 `PACK` 策略创建 placement group，**轮询等待就绪**（每 30s 打印已注册/可用 GPU 数，对自动扩缩容友好）
- `InfoActor`（每 GPU 一个）：获取节点 IP + 物理 GPU id
- `sort_key`：按节点 IP 数值 → GPU id 排序，得到**物理位置连续的 bundle 顺序**
- `_get_placement_group_layout`：计算 layout，支持四种模式——`rollout_external`（外部 rollout）、`debug_rollout_only`（只 rollout）、`colocate`（训推同卡，取 max）、**默认分离**（actor + rollout_num_gpus，offset 后给 rollout）
- `create_placement_groups`：返回 `actor` / `critic`（复用 actor）/ `rollout` 三组 bundle + gpu id 映射

> 关键洞察：slime 自己做 GPU 物理拓扑排序而非交给 Ray，是为了精确控制 colocate 模式下训练/推理在同一组卡上的布局，避免跨卡权重同步。

### 2. RayTrainGroup（`slime/ray/actor_group.py`）

训练侧抽象，包装一组 Megatron Ray workers（`actor` 或 `critic` 角色）：
- `async_train(rollout_id, rollout_data_ref, external_data=None)`：一次 rollout 训练，返回每个 worker 的 Ray ref（critic 的 ref 含 `{"values":...}`）
- `update_weights()`：rank0 广播权重到 rollout。两种路径：
  - **常规**：`ray.get([actor.update_weights.remote()])`
  - **full disk**（`update_weight_mode=full & transport=disk`）：trainer 先写磁盘权重版本，再调用 `_reload_rollout_weights_from_disk` 让 rollout 从磁盘重载
- `save_model` / `create` / `clear_memory` / `onload` / `offload` / `release`
- `_release_train_enabled()`：release_train 模式下，每步训练后 kill 掉 actor 再按需重建（极致显存回收）

### 3. RolloutManager（`slime/ray/rollout.py`，Ray actor）

rollout 侧的总指挥（**0 GPU**，CPU-only 协调器）：
- `generate(rollout_id)`：核心方法，流程见下方数据流
- `eval(rollout_id)`：调 `eval_generate_rollout`，不转训练数据
- `offload/onload_weights/onload_kv`：与训练侧的显存/KV 卸载与重载（colocate 模式核心）
- `check_weights(action)`：`snapshot / reset_tensors / compare`，**RL 正确性校验**——确认权重同步后训推一致
- `get_updatable_engines_and_lock`：拿到可更新权重的 engine（冻结的 ref/reward model 自动排除）
- `recover_updatable_engines`：故障恢复后重启 dead engines 并补做参数更新
- `RolloutHealthMonitor`：每个 server_group 一个，做 SGLang 健康检查 + 超时重启

### 4. SGLang Rollout（`slime/rollout/sglang_rollout.py`）

具体生成逻辑，全是 `async` 函数：
- `generate(args, sample, sampling_params)`：单条样本生成，POST `/generate` 到 SGLang router；支持 `consistent_hashing` 路由（用 `X-SMG-Routing-Key` 头，多轮 agent 会话亲和）
- `generate_and_rm` / `generate_and_rm_group`：生成 + reward model / 分组 reward
- `generate_rollout_async`：完整一轮 rollout（async 版）
- `GenerateState`（单例）：持有 tokenizer/processor、dp_rank 上下文、生成任务提交队列
- `abort(rollout_id)`：取消长尾样本（配合故障容忍）
- trace 全程埋点：`trace_span(sample, "sglang_generate", ...)`

### 5. DataSource（`slime/rollout/data_source.py`）

Data Buffer 的抽象接口：
```python
class DataSource(abc.ABC):
    def get_samples(num_samples) -> list[list[Sample]]
    def add_samples(samples)
    def save(rollout_id) / load(rollout_id=None)
    def __len__()   # 随 add/fetch 变化
```
- `RolloutDataSource`：从 HF Dataset 加载 prompt，支持 `rollout_global_dataset`（全局共享、按 epoch 切分、可 save/load）
- `RolloutDataSourceWithBuffer`：带经验回放 buffer（off-policy 复用）

### 6. 数据生成接口契约（`slime/rollout/base_types.py`）

用户自定义的统一接口，**RL 内核不 fork**：
```python
def generate_rollout(args, rollout_id, data_source, evaluation=False)
    -> RolloutFnTrainOutput(samples: list[list[Sample]]) | RolloutFnEvalOutput(data: dict)
# 可选钩子：
#   def generate(args, sample, sampling_params) -> Sample   # 仅替换核心生成
#   def custom_rm(args, sample) -> float                    # 自定义 reward
#   def custom_fn(args, rollout_data) -> None               # 后处理
#   def convert_samples_to_train_data(args, samples) -> dict
```
所有钩子通过 `--rollout-function-path` 等 `--*-path` 参数以 `load_function` 动态导入。

### 7. Agent 模块（`slime/agent/`）

把 agentic / 多轮 / TITO（tool-in-tool-out）转成训练轨迹：
- `adapters/`：`anthropic.py` / `openai.py` / `common.py`——对接外部 Agent harness（如 Claude Code / Codex）的 SDK
- `harness/`：`claude_code.py` / `codex.py`——包装具体 Agent CLI 作为 rollout 生成器
- `trajectory.py`：`TrajectoryManager`——每个 session 一条轨迹；`record_turn` 喂入每一轮（prompt + sglang snapshot），构建 per-sid message tree；`get_trajectory` 把树**线性化成 loss-masked 的 `list[Sample]` 训练行**，容忍 TITO 重分词漂移（fork/replace）
- `sandbox.py`：代码执行沙箱接入
- `parsing.py`：输出解析

> 关键洞察：这是 slime 区别于普通 RLHF 框架的"agentic"内核——把任意 Agent 工作流（含外部 harness 如 Claude Code）通过 TurnRecord/MessageNode 统一成训练样本，不碰训练内核。

### 8. 权重同步后端（`slime/backends/megatron_utils/update_weight/`）

四种权重更新策略，按 transport/mode 组合选用：
| 类 | 场景 |
|---|---|
| `UpdateWeightFromTensor` | 默认，tensor 直传（colocate / 同机） |
| `UpdateWeightFromDistributed` | 分布式广播到多 engine |
| `UpdateWeightFromDisk` | 全量 HF checkpoint 落盘重载（跨机/外部 engine） |
| `UpdateWeightFromDiskDelta` | **delta 增量**（继承 distributed），只传变化字节 |

配套 `HfWeightIteratorBase/Bridge/Direct`：遍历 HF 权重张量，支持 bridge（slime 内部 HF 格式）与 direct（原生 HF）两种。

---

## 数据流（一轮 rollout 的执行序列）

**同步模式（`train.py`）：**
1. `create_placement_groups` → Ray PACK + 物理拓扑排序
2. `create_rollout_manager`（先建，算 `num_rollout_per_epoch`）→ `create_training_models`（actor + 可选 critic）
3. `actor_model.update_weights()`：首次把 Megatron 权重推给 SGLang
4. （可选）`check_weights("compare")`：RL 正确性校验
5. **主循环** `for rollout_id in range(num_rollout)`：
   1. `rollout_manager.generate(rollout_id)` → `rollout_data_ref`
      - `RolloutManager.generate`：`_get_rollout_data` → 调用户 `generate_rollout(args, rollout_id, data_source)`
      - 用户 `generate_rollout` 内部：`DataSource.get_samples` → SGLang `generate` → `generate_and_rm`（reward/verifier）→ `RolloutFnTrainOutput`
      - `_save_debug_rollout_data`（可重放）、`_log_rollout_data`、`_convert_samples_to_train_data`、`_split_train_data_by_dp`
   2. （colocate）`offload.remote()` 释放 rollout 显存
   3. `actor_model.async_train(rollout_id, rollout_data_ref)`（critic 先 train，actor 消费 `value_refs`）
   4. 周期性 `save_model` + `rollout_manager.save`
   5. 周期性 `actor_model.update_weights()`（按 `update_weights_interval`）
   6. 周期性 `rollout_manager.eval(rollout_id)`

**异步模式（`train_async.py`）：**
- `assert not args.colocate`（异步不支持 colocate）
- **重叠**：`rollout_data_next_future = rollout_manager.generate.remote(rollout_id+1)` 在当前轮训练前提前启动下一轮 rollout
- 训练与生成交错；`update_weights` 前先 drain 当前生成 future，避免生成中途换权重
- `fully_async`（examples/fully_async）更进一步解耦

---

## 持久化层 / 数据模型

- **训练样本**：`Sample`（`slime/utils/types.py`）dataclass，含 prompt/tokens/logprobs/status/multimodal_inputs/session_id，可 `from_dict`/`append_response_tokens`
- **Data Buffer**：默认内存（Ray object store），`--rollout-data-transport nixl` 启用 NIXL tensor transport（启用 `enable_tensor_transport`）
- **Checkpoint**：Megatron 原生 ckpt + `megatron_to_hf/` 转换器（deepseekv3/gemma4/glm4/glm4moe/gpt_oss/llama/mimo/minimax_m2/qwen2/qwen3_5/qwen3moe/qwen3_next/qwen3_vl）导出 HF 格式
- **Delta Weight Sync**（`docs/en/advanced/delta-weight-sync.md`）：
  - trainer 发布 canonical HF ckpt 目录 → engine 的 `/pull_weights`（slime 的 sglang patch）扇出到每台 host 就地 apply + 校验 → 普通 `update_weights_from_disk` 重载
  - 配置：`--update-weight-mode delta --update-weight-transport disk --update-weight-disk-dir ... --update-weight-delta-encoding xor --update-weight-delta-checksum xxh3-128`
  - delta 恒用 zstd 压缩（level 1，profile 后优于 lz4/gzip/snappy/brotli，非可调项）

---

## 项目结构

```
slime/
├── train.py / train_async.py      # 两个 driver 入口（同步/异步）
├── pyproject.toml / setup.py      # wheel 自定义类 + requirements
├── slime/                         # 核心包
│   ├── ray/
│   │   ├── placement_group.py     # GPU 分配 + 拓扑排序 + create_*
│   │   ├── actor_group.py        # RayTrainGroup（actor/critic 训练抽象）
│   │   ├── rollout.py            # RolloutManager（Ray actor，rollout 指挥）
│   │   ├── train_actor.py / ray_actor.py / rollout_validation.py
│   ├── rollout/                   # rollout 逻辑 + 数据生成
│   │   ├── sglang_rollout.py     # 核心：generate/generate_and_rm/generate_rollout
│   │   ├── data_source.py        # DataSource / RolloutDataSource(+Buffer)
│   │   ├── base_types.py         # RolloutFnTrainOutput/EvalOutput 契约
│   │   ├── fully_async_rollout.py / sglang_streaming_rollout.py / sft_rollout.py / sleep_rollout.py
│   │   ├── filter_hub/            # 动态采样过滤 + metric 收集
│   │   ├── rm_hub/                # reward model hub（deepscaler/f1/math_dapo）
│   │   ├── on_policy_distillation.py / forge_load.py
│   ├── agent/                     # agentic rollout：adapters / harness / trajectory / sandbox
│   ├── backends/
│   │   ├── sglang_utils/          # arguments/external/server_control/sglang_config/sglang_engine
│   │   ├── megatron_utils/        # actor/arguments/checkpoint/model_provider/loss/
│   │   │   ├── update_weight/     # 4 种权重同步策略 + HF iterator
│   │   │   ├── megatron_to_hf/    # 14+ 模型的 ckpt 转换器 + processors（量化）
│   │   │   ├── kernels/           # fp8 / int4_qat
│   │   │   ├── server/            # sglang serving patch
│   ├── utils/                     # arguments/trace_utils/logging/health_monitor/disk_delta/ppo_utils...
│   ├── plugins/ (rollout_buffer 等)
├── slime_plugins/                 # 模型特定插件（mbridge / megatron_bridge / models）
│   ├── mbridge/                   # deepseek_v32/gemma4/glm4/glm4moe(_lite)/gpt_oss/mimo/minimax_m2/qwen3_5/qwen3_next
│   ├── models/                    # glm5/gpt_oss/gemma4/glm4/hf_attention/learnable_softmax/flash_dot_product
├── examples/                       # 12 个完整用例（coding_agent_rl/multi_agent/retool/search-r1/tau-bench/geo3k_vlm/on_policy_distillation/delta_weight_sync/fully_async...）
├── tests/                          # CPU 单测 + 契约测 + GPU E2E（dense/MoE/PPO/OPD/ckpt/数值/async/debug replay）
├── docs/ (en + zh)                 # advanced / developer_guide / examples / get_started / blogs
├── docker/                         # CUDA/AMD/NPU patch
├── tools/                          # ckpt 转换 / profile / trace 工具
├── scripts/ (low_precision, models)
└── .github/workflows/             # pr-test.yml（GPU self-hosted, label-gated）+ pre-commit
```

---

## 技术栈

| 类别 | 技术 |
|---|---|
| 训练内核 | Megatron-LM（透传参数，不包一层） |
| 推理/Rollout | SGLang + sglang-router（唯一后端，`--sglang-*` 透传） |
| 分布式编排 | Ray（placement group / remote actors / object store） |
| 模型库 | transformers, safetensors |
| 追踪 | wandb, tensorboard, 自研 trace_utils（trace_id/span/event，跨 rollout 边界） |
| 分析 | memray, profile_utils, trace_timeline_viewer |
| 校验 | xxh3 / blake3 / adler32（delta checksum）, xxhash |
| 压缩 | zstandard（delta） |
| 多模态 | qwen_vl_utils, pillow |
| Agent 生态 | anthropic, openai, openai-agents, mcp[cli], e2b（沙箱） |
| 其他 | accelerate, omegaconf, blobfile, datasets, ring_flash_attn, numba |

---

## 构建与测试

```bash
# 安装（推荐 Docker，slime 带 sglang/megatron 临时 patch）
pip install -e . --no-deps
BASE_DIR=/root bash build_conda.sh        # CI 用的 conda 构建

# 训练
python train.py <args>           # 同步
python train_async.py <args>     # 异步

# 关键参数族（slime/utils/arguments.py）
#   --actor-num-nodes/--actor-num-gpus-per-node/--rollout-num-gpus*
#   --colocate/--offload/--offload-rollout/--offload-train
#   --rollout-function-path / --eval-function-path / --data-source-path
#   --custom-reward-post-process-path / --custom-rm-path
#   --update-weight-mode {tensor|full|delta} --update-weight-transport {distributed|disk|nixl}
#   --use-fault-tolerance / --use-critic / --use-opd / --release-train
#   --rollout-external（外部 rollout engine） --sglang-* (透传)

# 测试
pytest tests/ -m "not gpu"           # CPU 单测 + 契约测
# GPU E2E（self-hosted, label run-ci-*）覆盖 dense/MoE/PPO/OPD/ckpt/async/debug-replay

# 调试路径（RL bug 常静默）
#   --debug-rollout-only   只 rollout，不训练，产出可重放 dump
#   --debug-train-only     只训练，从 dump 读数据
#   --load-debug-rollout-data / --save-debug-rollout-data
#   --check-weight-update-equal  训推权重一致性校验
```

---

## 设计权衡

1. **单一 rollout 后端（SGLang）vs 多后端抽象**：选前者。多后端须抽象出公共子集，会掩盖各后端最强特性（路由/缓存/disaggregation/weight-sync）。代价：想用 vLLM 等需走 external engine 接口。→ 这是 slime "native" 哲学的根基。
2. **引擎参数透传 vs 再封装**：选透传。Megatron 参数直接读，SGLang 加 `--sglang-` 前缀即可用全部上游参数。上游优化零成本可用，但学习曲线需懂上游。
3. **显式数据流 vs 框架自动编排**：选显式。train.py 主循环肉眼可见，debug-rollout-only / debug-train-only 分离调试路径，因为 "RL bug 常静默"。
4. **统一训练/rollout/data-buffer 路径 vs 拆成多 trainer/agent framework**：选统一。math/code/search/tool/sandbox/verifier/多 agent/长 horizon workflow 全以"数据生成或 reward workflow"插入，不 fork 训练内核。
5. **Delta weight sync 仅磁盘传输**：跨集群/数据中心大模型 disaggregation，全量 ckpt 是主导成本；只传变化字节。zstd 压缩 + xxh3 校验；profile 后不做可调项。代价：需共享文件系统。
6. **轻量且 opionated**：只深度优化 Megatron+SGLang 大规模 RL 这条路径，不追求覆盖所有算法/所有引擎。

---

## 生态系统

| 层 | 内容 |
|---|---|
| 上游引擎 | Megatron-LM（训练）、SGLang（推理/Rollout）、Ray |
| 模型插件 | GLM 全系、Qwen3/3.5/3Next/3MoE、DeepSeek V3/V3.1/R1、Llama3、Gemma4、GPT-OSS、MiMo、MiniMax-M2 |
| 高级特性 | PD disaggregation、speculative decoding、low-precision（fp8/int4 rollout+QAT）、on-policy distillation、外部 rollout engine、SGLang Config YAML、session-affinity 路由 |
| 工程 | CI（self-hosted GPU, label-gated）、reproducibility、fault-tolerance、trace viewer、profiling |
| 示例 | coding_agent_rl（SWE）、multi_agent、retool、search-r1、tau-bench、geo3k_vlm（含多轮）、on_policy_distillation、delta_weight_sync、fully_async、eval_multi_task、train_infer_mismatch_helper |

---

## 相关链接

- GitHub: https://github.com/THUDM/slime
- 文档: https://thudm.github.io/slime/
- 愿景博客: https://lmsys.org/blog/2025-07-09-slime/
- v0.1.0 发布: https://thudm.github.io/slime/blogs/release_v0.1.0.html
- Agent-Oriented Design: https://www.notion.so/Agent-Oriented-Design-An-Asynchronous-and-Decoupled-Framework-for-Agentic-RL-2278e692d081802cbdd5d37cef76a547
- DeepWiki: https://deepwiki.com/THUDM/slime

关联：[[codegraph]]（本项目用其做代码图谱）、[[graphify]]（知识图谱方法论）、[[context-mode]]（本会话所用上下文工具）、[[mlflow]] / [[zenml]]（MLOps 编排参考）、[[langfuse]]（LLM tracing 参考）、[[heuristic-learning]]（Agent 学习范式）、[[agno]] / [[ruflo]]（多 agent 编排对照）
