---
title: dsh-superagent
created: 2026-11-16
updated: 2026-11-16
type: entity
tags: [ai, project, mvp, knowledge-management]
sources: [本地仓库 /home/rowan/Projects/dsh-superagent-prototype, docs/000-008, 论文 "Exploring Super-agent Design: Towards a More Autonomous Agent System"]
confidence: high
---

# dsh-superagent

> DeepSeek Harness 团队开源的**研究原型**（MIT，非官方产品）：面向单个 GitHub 仓库的主动式编码 agent，打包为 [[deepseek-harness]]（DSH）bundle。监听 GitHub（可选飞书），在被授权的人请求工作时开 Ticket → 在独立 DSH Session 和目录中执行 → 回原对话交付（如 PR），Web 面板只展示需要人介入的事项。核心理念：**"Take as little human attention as possible, and give as much value as possible"**。

---

## 核心理念（docs/000-philosophy）

一切设计以"注意力成本"为唯一度量：每条消息、通知、设置、面板元素都必须交付超过其注意力成本的价值，否则被删除。

对 agent 的要求：
- **只在被要求或规则允许时行动**：请求必须直接指向 agent 且来自允许名单；无人请求的工作需要团队书面规则，且初始只"记录将做什么"不实际执行
- **只在人必须行动或能用上结果时说话**：确认一次请求 → 静默工作 → 有结果/需决策/无法完成时再写
- **一次只问一个具体问题**，结构化表单直达本人而非埋在长报告里
- **按影响停而非按努力停**：本地改动推进到可评审；需设计决策则带着清晰问题停下
- **诚实汇报**：草稿标记未完成，失败报失败，不用绕过限制来避免提问

对设计的约束：概念少（业务需求成为现有概念的属性或 prompt 文本，不新增概念）、设置少（能用默认值就用默认值）、面板只显示等待人的事项、文档按序阅读不前置概念。对运营者的责任要求：小范围起步、为低噪声调优、**不得用它刷量**（群发 PR/广播视为滥用）。

## 领域模型（docs/001）

| 概念 | 含义 |
| --- | --- |
| Source | 外部事件来源：GitHub、飞书，插件式（trigger/channel/read/poll 拆分） |
| Trigger | 一次外部事件（issue、评论、消息），幂等存储一次 |
| Thread | 外部线程（issue、PR、会话）；Ticket 跟随的 Thread 关闭决定 Ticket 结束 |
| Eval | 主会话（MasterAssessor）评估 Trigger 是否接受：accept / stop / ignore / unavailable |
| Ticket | 接受后的工作项，带 Mandate（授权范围）、Subscription（订阅的 Thread） |
| Assignment | 一次执行尝试，由 Executor 在独立会话 `worker-<ticket id>` 中跑 |
| Mandate | 该 Ticket 被授权做什么；消息/评论/引用文档只是决策输入，不能改变权限 |

## 架构（src/，TypeScript + pnpm + tsdown + vitest）

```
Source 插件 (github / feishu) ──SourceContext──┐
Session 工具 ──────────────────────────────┤   ▼
管理路由 (HTTP) ────────────────────────────┤ Engine ──┬─ Repositories → Store
                                             │        ├─ Policy（授权规则）
                                             │        ├─ SourceRegistry
                                             │        ├─ MasterAssessor（主会话评估）
                                             │        ├─ DshExecutor（worker 执行）
                                             │        └─ Outbox（回执+reply effect）
                        Settings ──policyChanged──▶ Engine
                        Assessor/Executor/Sessions/Outbox ──▶ Effects ──▶ Store
```

- **Runtime**（组合根）：锁状态目录、开 Store、注册路由、跑 Setup、启动 Passes
- **Engine**（src/core/engine.ts）：Trigger/Thread/Decision/Ticket/Assignment 的**唯一写入方**；全部同步方法、单事务命令，端口在事务内入队、提交后由适配器执行。内部分五个单向依赖的 Part：`Intake → Evals → Tickets → Assignments → Replies`
- **角色隔离**：Sources / MainSession / People / Settings / Executor 各拿到 Engine 的 `Pick` 子集接口，防止越权调用
- **Passes**：每 2 秒一轮——先处理到期 effects，再 `Engine.evaluateDue`
- **Notices**：领域事件 → 主会话消息；问题立即转发，普通进度记在 Ticket 上
- **DshExecutor**：worker 用 `dsh-superagent-worker` preset（无审批跑命令，前台 shell 5 秒后转后台 job 以便能接收新消息）；主会话用更小工具集的 `dsh-superagent-router`

## 数据流（一次请求的生命周期）

1. Source 收到事件 → 生成 Trigger，Engine `receive()` 幂等存储
2. 已订阅 Thread 的消息直接送达对应 Ticket（绕过门禁、不授新权）
3. 其余进入 Eval：门禁查发送者 × Policy（允许名单 / admission 表 / bot 白名单只能产生推断候选）
4. 主会话 Decision `accept` → 原子创建 Ticket + Mandate + 首个 Assignment + Subscription + 确认消息
5. Executor 在 `worker-<ticket id>` 会话独立目录执行；按 Ticket stage 状态机推进（awaiting answer/review、blocked/failed、working、waiting）
6. Executor Report（progress/waiting/ready/blocked/failed/dropped）；后台 job 每轮后最多 30 分钟
7. Thread 关闭 → `followsDone` → Ticket 结束（merged/closed）；Worker 没接住的 follow-up 释放回新 Eval
8. 回复经 Outbox：acknowledgement / answer / result / attention，Source 关闭时消息等待

## 设计取舍

| 取舍 | 理由 |
| --- | --- |
| 同步单事务 Engine + 事务后 effects | 命令原子性靠 Store 事务，外部副作用（发消息）延后到提交后，崩溃可恢复 |
| 门禁在 host 强制而非靠 prompt | 消息内容永远不能改权限（防注入提权），Policy 是唯一事实源 |
| worker shell 5 秒转后台 job | 长命令不再阻塞 worker 接收人的新消息 |
| Executor 拥有 follow-up 期间主会话只能 stop | 避免两个 agent 对同一条消息做出冲突决策 |
| 面板只列等待人的事项 | "健康状态不占空间"——注意力预算原则的直接体现 |
| 研究原型定位 | 与论文《Exploring Super-agent Design》所述内部版本不完全一致，部分设计是未来方向未实现 |

## 技术栈

| 层 | 技术 |
| --- | --- |
| 语言/构建 | TypeScript ESM, tsdown, pnpm |
| 测试 | vitest（`pnpm check` = typecheck + test + build） |
| Agent 运行时 | DeepSeek Harness（Session/preset/subagent/后台 job） |
| 面板 | React TSX 客户端（overview/ticket/thread/eval 视图） |
| 事件源 | GitHub（trigger/channel/read/poll）、飞书（可选） |

## 与相关页面的关系

- 建立在 [[deepseek-harness]] 之上：DSH 提供 Session、preset、subagent、事件日志等运行时原语，dsh-superagent 是其上的应用层 bundle
- 与 [[superagent]] 长时域智能体架构同属"自主 agent 编排"方向，但 dsh-superagent 反其道强调**最小注意力占用**而非最大自主性
- 授权设计（消息不能改权限、Mandate 限定范围）是 agent 安全中提示注入防护的工程化实践

## 评价

原型最有价值的不是代码本身，而是把"注意力经济学"做成可执行约束：门禁、单事务领域模型、角色化 Engine 接口、只显示待人工事项的面板，全部服务于"少打扰人、多交付价值"。作为研究代码，作者明言有 bug、风格不一致，采纳前需审查。

## 参考

- 论文：*Exploring Super-agent Design: Towards a More Autonomous Agent System*（部分设计未在此原型实现）
- 本地仓库 `docs/000`~`008`：哲学 → 领域 → 授权 → 执行 → Prompt → 面板 → 部署 → 架构 → Cookbook
