---
title: OpenEvolve
created: 2026-11-11
updated: 2026-11-11
type: entity
tags: [ai, project, active, platform]
sources: [~/Projects/openevolve 源码, https://github.com/algorithmicsuperintelligence/openevolve]
confidence: high
---

# OpenEvolve

> Google DeepMind AlphaEvolve 的开源复现 —— 用 LLM 做变异算子的进化式编码 agent。MAP-Elites 质量多样性 + 岛屿种群 + LLM ensemble + 级联评估。7,600+ stars、月下载 1.7 万、被数百篇论文引用，已成为 LLM 驱动算法发现的标准基线工具。

---

## 定位

用户给出初始程序 + 评分函数（evaluator），OpenEvolve 迭代地让 LLM 变异 `EVOLVE-BLOCK-START/END` 标记的代码段，靠进化搜索发现高性能/突破性算法。适用场景：性能优化、算法发现、科学计算、竞赛题、多目标问题。Python ≥3.10，纯 Python ~8.5k 行核心代码。

## 架构

```
                    ┌─────────────────────────────────────┐
                    │  Controller (controller.py)         │
                    │  ProcessPoolExecutor 并行迭代        │
                    └───────────┬─────────────────────────┘
                                │ 数据库快照 (pickle)
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
  ┌───────────┐         ┌──────────────┐        ┌─────────────┐
  │ Database  │◄─sample─│ Iterration   │─LLM──►│ LLM Ensemble │
  │ MAP-Elites│  parent │ (worker 进程) │ 变异   │ openai/claude│
  │ + islands │─inspir─►│  + prompt    │        │ _code/copilot│
  └─────┬─────┘         └──────┬───────┘        │ /codex CLI  │
        │                      ▼                └─────────────┘
        │               ┌──────────────┐
        │               │  Evaluator   │  级联: 验证→基础→全面
        │               │ (subprocess) │  每级阈值淘汰
        │               └──────┬───────┘
        │  artifacts (错误/调试数据回灌下一轮 prompt)
        └──────────────────────┘
```

## 数据流（一次迭代）

1. Controller 从 Database 选岛（IslandSelector），做数据库快照发给 worker 进程
2. Worker 在岛内采样 parent（exploration/exploitation/随机加权）+ 采样 inspirations（与展示给 LLM 的 top 程序不同源 —— "Double-Selection"）
3. Prompt sampler 组装上下文：当前程序、进化历史、top/diverse/inspiration 程序、上轮 artifacts 反馈；diff-based 变异（SEARCH/REPLACE）或全文重写
4. LLM ensemble 按权重采样模型生成变异
5. Evaluator 三级级联评估（独立子进程 + 超时保护），逐级阈值淘汰
6. 结果写回主 Database：MAP-Elites 特征网格（复杂度×多样性等维度）决定精英格子；island 代数达到阈值时惰性迁移
7. 周期性 checkpoint 全量落盘，可无缝 resume

## 核心模块

| 模块 | 行数 | 职责 |
|---|---|---|
| `database.py` | 2910 | MAP-Elites 网格 + 岛屿 + 迁移 + artifacts + 嵌入/LLM-judge 新颖性判定 |
| `process_parallel.py` | 1224 | 进程池并行控制器、快照分发、worker 事件循环复用 |
| `evaluator.py` | 856 | 级联评估、阈值门、evaluator kwargs 注入 |
| `controller.py` | 644 | 顶层编排、checkpoint/resume、日志 |
| `config.py` | 616 | dataclass 层级配置（LLM/Database/Evaluator/Prompt/Trace） |
| `llm/` | — | ensemble + OpenAI 兼容、Claude Code、Copilot CLI、Codex app server 四类后端 |
| `prompt/sampler.py` | — | 模板化 prompt 组装、diff/full-rewrite 切换 |
| `coevolution.py` | 315 | 对抗式共同进化（程序 vs 对手种群） |

## 设计取舍

- **进程而非线程**：每次迭代在独立进程 + 数据库快照中运行，评估器又各自 spawn 子进程 —— 真并行 + 故障隔离（单个评估崩溃不拖垮系统），代价是 pickle 序列化开销
- **Double-Selection**：作为 inspiration 来源的程序与 prompt 中展示的程序分开采样，避免 LLM 视野趋同
- **惰性迁移**：迁移由岛内代数而非全局迭代触发，减少同步点
- **Diff 优先**：默认 SEARCH/REPLACE diff 变异省 token，可退回全文重写
- **Artifact 旁路**：程序可返回调试数据（<10KB 入库 / 大文件落盘），回灌下轮 prompt 形成反馈回路
- **全链路可复现**：每个组件（采样、LLM ensemble、迁移）都接受随机种子

## 成果与生态

- 圆装箱 n=26 SOTA；MLX Metal kernel 2-3× 加速；Rust 自适应排序
- 25 个示例覆盖数学（alphaevolve_math_problems）、基准（arc_benchmark、lm_eval）、GPU kernel、信号处理等
- 被用于 Zarankiewicz 数新界、系统性能研究、组合双射发现等论文；安全研究用它进化 prompt 注入片段和口令猜测 prompt

## 关联

- 与 [[opengeni]] 同属"LLM 进化搜索"谱系
- LLM 后端生态见 [[langchain]]、[[llama-cpp]]
- 进化式 RL 训练框架对照：[[slime]]
