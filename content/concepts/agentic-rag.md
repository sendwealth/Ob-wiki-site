---
title: Agentic RAG 代理式检索增强生成
created: 2026-05-05
updated: 2026-05-05
type: concept
tags: [ai, rag, agent, llm, framework]
sources: []
confidence: high
---

# Agentic RAG（代理式检索增强生成）

> 概括：传统 RAG 是「检索 → 回答」的固定流水线；Agentic RAG 赋予 LLM 自主决策权——何时检索、查什么源、检索结果够不够、要不要换个方式再查。

---

## 核心概念

**Agentic RAG** = 传统 RAG + AI Agent 范式。

### 传统 RAG 的局限

传统 RAG 是**线性流水线**：用户提问 → 检索一次 → 塞进 Prompt → LLM 生成。问题：

- 不管需不需要，每次都检索（浪费延迟和成本）
- 检索质量差时强行瞎编，无自我纠错能力
- 只能查一个向量库，不能查 SQL、调 API、用计算器
- 没法拆解复杂问题做多步推理

### Agentic RAG 的突破

Agentic RAG 让 LLM 变成一个能自主决策的**代理**：

| 能力 | 说明 |
|------|------|
| **自适应检索** | 自己判断是否需要检索、查什么源 |
| **多步推理** | 检索 → 反思 → 重写查询 → 再检索 → 验证 |
| **工具使用** | 向量库 + SQL + Web 搜索 + API + 计算器 |
| **路由分发** | 不同问题路由到不同检索策略 |
| **自我反思** | 评估检索质量，不行就换个方式再来 |

> [!summary] 一句话总结
> 传统 RAG 是「检索 → 回答」的两步流水线；Agentic RAG 是「思考 → 检索 → 反思 → 再检索 → 验证 → 回答」的自主循环。

---

## 关键论文

### 三大奠基论文

| 论文 | 时间 | 核心贡献 |
|------|------|---------|
| **ReAct** (Yao et al., [arXiv:2210.03629](https://arxiv.org/abs/2210.03629)) | 2022.10 | Reasoning + Acting 交织模式，Agentic RAG 理论基础。LLM 交替生成「思考轨迹」和「行动」，观察结果再思考 |
| **Self-RAG** (Asai et al., [arXiv:2310.11511](https://arxiv.org/abs/2310.11511)) | 2023.10 | 反思令牌（Reflection Tokens），让 LLM 自主学习「是否需要检索」「检索结果是否相关」「生成是否支持检索结果」 |
| **CRAG / Corrective RAG** (Yan et al., [arXiv:2401.15884](https://arxiv.org/abs/2401.15884)) | 2024.01 | 轻量级检索评估器 + 纠正机制。检索质量低时自动触发 Web 搜索补充。首个工程化的自纠正 RAG 方案 |

### 最新方向（2025-2026）

截至 2026 年 5 月，arXiv 上 "agentic retrieval augmented generation" 相关论文已达 **1,184 篇**。近期值得关注：

- **DocSync**（2026.05）：Agentic 文档维护，自动同步代码变更到文档
- **Agentic Legal RAG**（2026.05）：法律判决生成中的多 Agent 协作
- **GRAVITY**（2026）：长时对话记忆的 Agentic RAG
- **GRAIL**（2026）：用小模型（SLM）增强索引的轻量方案
- **Tiny-Critic RAG**（2025）：极小评估模型（<1B）做检索质量判断

---

## 主流框架

> Star 数截至 2026 年 5 月，浏览器实时访问 GitHub。

| 框架 | Stars | 定位 | 关键特点 |
|------|:---:|------|------|
| **AutoGen**（微软） | 57.7k | 多 Agent 对话 | 角色式多 Agent 协作，⚠️ 已进入维护模式，社区转向 AG2 |
| **CrewAI** | 50.7k | 角色扮演式多 Agent | 低门槛，定义角色+任务即可编排。商业化最积极 |
| **LlamaIndex** | 49.1k | RAG 全栈框架 | 数据连接器最全 + Document Agent + Workflow |
| **DSPy**（斯坦福） | 34.2k | 编程式 LLM 控制 | 声明式编程替代提示工程，自动优化 Prompt |
| **GraphRAG**（微软） | 32.8k | 知识图谱 RAG | v3.0.9 模块化，全局摘要 + 局部检索 |
| **LangGraph**（LangChain） | 31.2k | 图状态机编排 | 有向图定义 Agent 流程，与 LangSmith 深度集成 |
| **Haystack**（deepset） | 25.1k | 模块化 AI 编排 | 生产级 Pipeline 设计，成熟稳定 |
| **RAGAS** | 13.8k | RAG 评估 | Faithfulness/Relevancy/Precision/Recall，事实标准 |

### 选型指南

```
简单问答                     → LlamaIndex + 基础 RAG
多步推理 + 工具调用          → LangGraph Agent
多角色分工                   → CrewAI
企业级可控                   → LangGraph + LangSmith
知识图谱场景                 → GraphRAG
自动优化 Prompt              → DSPy
```

---

## 架构模式

### 单 Agent vs 多 Agent

| 维度 | 单 Agent | 多 Agent |
|------|----------|----------|
| 架构 | 一个 Agent 负责全部 | 角色分工（检索员/评估员/生成员/核查员） |
| 延迟 | 低（3-5s） | 高（10-30s） |
| 成本 | 低 | 高（多次 LLM 调用） |
| 可靠性 | 单点故障风险 | 交叉验证更可靠 |
| 代表 | LangGraph Agent、Self-RAG | CrewAI、AutoGen |
| 适用 | 常规问答 | 复杂多源多步任务 |

### 四种多步检索模式

```
模式1：ReAct 循环
  Think（分析问题）→ Act（检索/调工具）→ Observe（评估）→ Think...

模式2：检索-评估-重写
  检索 → 相关性评估 → 不相关则重写查询 → 再检索

模式3：逐层深挖
  原始问题 → 拆成子问题 → 逐一检索 → 汇总融合

模式4：多源融合
  向量库 + 知识图谱 + Web 搜索 + API → 聚合排序
```

### LangGraph 五种 Agent 工作流

1. **Prompt Chaining**：串联处理，上一步输出 → 下一步输入
2. **Parallelization**：并行处理多个子任务
3. **Routing**：按问题类型分发到不同处理分支
4. **Orchestrator-Worker**：主 Agent 拆任务，分发 Worker
5. **Evaluator-Optimizer**：生成 → 评估 → 优化 → 再生成

---

## 传统 RAG vs Agentic RAG

| 维度 | 传统 RAG | Agentic RAG |
|------|----------|-------------|
| 检索触发 | 固定，每次都检索 | 自适应，按需检索 |
| 检索次数 | 单次 | 多轮（0-N 次） |
| 检索源 | 单一向量库 | 向量库 + SQL + KG + Web + API |
| 质量评估 | 无 | 自我反思 / 评估器评分 |
| 纠错能力 | 无 | 重写查询 / 切换源 / 承认不知道 |
| 工具调用 | 不支持 | Function Calling |
| 延迟 | 1-2s | 3-30s |
| Token 消耗 | 低 | 中高（多次 LLM 调用） |
| 适用场景 | 简单问答、文档查询 | 复杂推理、多源验证、研究分析 |
| 幻觉风险 | 检索不准时高 | 有反思机制，降低但未消除 |

---

## 评估与基准

### RAGAS（事实标准）

RAGAS（13.8k Stars）提供了标准化的评估维度：

- **Faithfulness**（忠实度）：生成内容是否忠于检索结果
- **Answer Relevancy**（答案相关性）：答案是否切题
- **Context Precision**（上下文精度）：检索到的文档中有多少相关
- **Context Recall**（上下文召回）：相关文档有多少被检索到
- **Agentic 扩展**：工具选择准确率、推理步数效率、纠错成功率

### 其他基准

- **HotpotQA**：多步推理问答
- **FEVER**：事实验证
- **WebArena**：Web 环境下的 Agent 能力
- **GAIA**：通用 AI 助手基准（Meta）

> [!warning] 评测缺口
> **缺乏专门的 Agentic RAG 基准测试**。现有基准要么测传统 RAG 质量，要么测 Agent 规划能力，缺少评估「Agent 自主决定检索策略」这个核心行为的专用测试集。

---

## 关键挑战

| 挑战 | 说明 | 当前解法 |
|------|------|---------|
| **延迟控制** | 多轮 LLM 调用导致 10-30s 响应 | 小模型评估器、缓存、并行化 |
| **成本管理** | Token 消耗是传统 RAG 的 3-10 倍 | 按需检索、SLM 替代 LLM |
| **幻觉传导** | 检索结果有误 → Agent 照样采信 | 多源交叉验证、忠实度评估 |
| **无限循环** | Agent 反复检索退不出来 | 最大步数限制、循环检测 |
| **评测缺失** | 缺乏专用 Agentic RAG 基准 | RAGAS 扩展中，学术社区跟进 |
| **多 Agent 协调** | 角色间信息传递可能失真 | 标准化消息格式、共享记忆 |

---

## 2024-2026 趋势

1. **Pipeline → Agent 范式加速**：越来越多生产系统从固定 Pipeline 迁移到 Agentic 架构
2. **GraphRAG 崛起**：微软 GraphRAG（32.8k Stars）知识图谱 + RAG，全局摘要 + 局部检索双模式
3. **LangGraph + LangSmith 端到端**：LangChain 从 Library 向 Platform 转型
4. **RAGAS 成为标准**：从研究项目成长为行业事实标准
5. **多模态 Agentic RAG**：检索范围从文本扩展到图片、视频、音频
6. **小模型 Agent 化**：Tiny-Critic RAG 用 <1B 评估模型替代大模型
7. **AutoGen 生态分裂**：微软维护模式，核心团队转向 AG2 分支
8. **CrewAI 商业化加速**：多 Agent 框架商业化的排头兵

---

## 信息来源

- GitHub 星数：各项目主页（2026.05 浏览器实时访问）
- 论文：arXiv.org 搜索 "agentic retrieval augmented generation"
- 框架文档：LangGraph、LlamaIndex、CrewAI、DSPy、GraphRAG 官方文档
- 评估：RAGAS 官方文档

> [!note] 置信度说明
> ✅ 框架星数和论文信息为公开发布的客观数据 | 💬 趋势判断含分析师观点 | ❓ 论文总量为 arXiv 搜索结果，统计口径可能有偏差

---

## 相关页面

- [[oscar-research-methodology]] — 本报告的调研方法论基础
- [[user-pain-points]] — 用户痛点验证方法论
