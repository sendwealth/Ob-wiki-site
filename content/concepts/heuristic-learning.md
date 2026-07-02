---
title: Heuristic Learning (HL) — 超越梯度的学习范式
created: 2026-05-10
updated: 2026-05-10
type: concept
tags: [ai, reinforcement-learning, agentic-ai, paradigm]
source: https://github.com/Trinkle23897/learning-beyond-gradients
author: Jiayi Weng (翁家轶，EnvPool创建者)
---

# Heuristic Learning (HL) — 超越梯度的学习范式

> 来源：[Learning Beyond Gradients](https://trinkle23897.github.io/learning-beyond-gradients/) (2026.05)，284 stars，Apache 2.0

## 一句话总结

不用梯度/神经网络训练策略，而是让 **coding agent（Codex CLI等）直接迭代修改程序代码**，在多个 RL benchmark 上达到或超越 Deep RL 水平。

## 核心定义

**Heuristic Learning (HL)** 的学习循环：
- 状态 → 动作 → 反馈 → 更新
- 但更新的对象是**软件代码结构**，不是 NN 参数
- 反馈被 coding agent 消费（奖励、测试、日志、视频回放、人类反馈）
- 没有反向传播；agent 直接编辑策略、检测器、测试、配置、记忆

**Heuristic System (HS)** 是被维护的软件制品，包含：
1. 程序化策略（规则、状态机、控制器、MPC）
2. 状态表示（显式变量、检测器、缓存）
3. 反馈通道（多源：奖励、测试、日志、回放）
4. 实验记录与回放
5. 更新机制（coding agent 直接编辑）

## 关键实验结果

纯程序化策略，零梯度训练：

| 环境 | HL 成绩 | 意义 |
|------|---------|------|
| Atari Breakout | 864（理论最大值） | 完美分数，~500行Python |
| MuJoCo Ant | 6000+ | 达到 Deep RL 水平 |
| MuJoCo HalfCheetah | 11836.7 | 达到 Deep RL 水平 |
| VizDoom D3 Battle | mean=557.0 (10 seeds) | 竞争力强，纯cv2/NumPy |
| Atari57 全量 | 342条搜索轨迹 | HNS中位数远超PPO baseline |

Breakout 策略用了：RAM读取 + 视觉检测 + 轨迹反射预测 + 隧道策略 + 卡死检测。

## HL vs Deep RL 对比

| 维度 | Deep RL | Heuristic Learning |
|------|---------|-------------------|
| 策略 | NN 参数 | 代码（规则/状态机/MPC） |
| 状态 | 观测张量 | 显式变量、检测器 |
| 反馈 | 固定奖励标量 | 多通道（测试、日志、回放、人类） |
| 更新 | 梯度下降 | coding agent 直接改代码 |
| 记忆 | 回放缓冲区 | 实验记录、摘要、版本diff |

## HL 的五个核心特性

1. **可解释性** — 策略就是代码，可翻译成自然语言
2. **样本效率** — 一次代码修改直接跳到新策略（无需百万步采样）
3. **可回归测试** — 旧能力变成测试用例，防止能力退化
4. **可控过拟合** — 工程化正则化手段
5. **抗灾难性遗忘** — 旧能力固化在规则和测试中

## 为什么以前不行？为什么现在可以？

以前人类维护启发式策略的成本太高。Coding agent（Codex CLI、Claude Code）改变了成本曲线 — 类比工业革命中纺纱机取代手工。

## 耦合复杂度 (Coupling Complexity)

描述 coding agent 能维护的策略复杂度上限：

**代码侧约束**：模块边界、接口稳定性、测试覆盖、可观测性、回滚成本
**Agent 侧约束**：模型能力、上下文长度、记忆质量、工具质量、迭代速度

## 未来展望：System 1 + System 2 + HL

作者提出机器人场景的三层架构：
- **浅层专用 NN**: 快速感知/分类（System 1）
- **HL**: 新数据处理、规则、测试、安全边界、局部恢复
- **LLM agent**: System 2，给 HL 反馈，定期提取 HL 生成的数据

## 与"AI多智能体协作"方向的关系

- HL 本质是 "AI编程智能体替代人类做策略维护"，是多智能体协作的具体落地
- Coupling Complexity 概念对多智能体系统的任务分解有参考价值
- Atari57 实验用了 unattended Codex CLI 批量跑57个游戏，是成熟的 agent 自动化工作流
- 持续学习（Continual Learning）通过工程手段实现，而非依赖算法

## 社区反应

2天内284 stars，6个 issue 均正面。有人联系到 karpathy/autoresearch。被认为有 robotics 方向的重大潜力。

## 引用

```bibtex
@misc{weng2026learning_beyond_gradients,
  title = {Learning Beyond Gradients},
  author = {Weng, Jiayi},
  year = {2026}, month = may,
  howpublished = {\url{https://trinkle23897.github.io/learning-beyond-gradients/}},
  note = {Blog post}
}
```
