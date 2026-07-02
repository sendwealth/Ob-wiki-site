---
title: Multica Loop Agent 实践
created: 2026-06-24
updated: 2026-06-24
type: concept
tags: [ai-engineering, agent, loop-engineering, multica, feedback-loop, autopilot, project-management]
sources: [agent-world 项目实战]
confidence: high
---

# Multica Loop Agent 实践

> 基于 [[loop-engineering]] 理论，在 [[multica]] 平台上为 [[agent-world]] 项目实现的全闭环 AI 编排系统。一个 Autopilot 完成感知→验证→检查停滞→分配→反馈五阶段，零碎片、零断裂。

## 问题背景

agent-world 项目 v1.1.0（Phase 5），43 个 agent/* 分支已 squash-merge，CI green，723 个历史 issue done。但在 Multica 上运行的三旧 Autopilot 存在严重断裂：

- **「每日复盘」**：定时扫描项目创建 issue，但**已暂停 22 天**
- **「开发小队」**：定时分配 issue 给成员，每 **10 分钟**触发，但**无验收、无反馈**
- **「开发&review」**：唯一包含 todo→in_review→done 回退逻辑的，但**已暂停 37 天**

> [!warning] 闭环断了两环
> 只有「分配+执行」在转，「验证+反馈」全部断开。三个 Autopilot 是碎片，不是闭环。

## 核心约束

| 约束 | 值 | 原因 |
|------|----|------|
| 模型并发上限 | **2** | LLM 免费层 rate limit |
| 触发频率 | **每 30 分钟** | 每次只处理 1 个 issue，避免并发冲突 |
| 最大 in_progress | **2 个** | 与并发上限匹配 |
| 每轮处理量 | **1 个 issue** | 不批量操作，不超发 |
| 分配前置条件 | **先验证 in_review** | 闭环不跳过验证阶段 |

## 闭环架构

```
┌──────────────────────────────────────────────┐
│  Loop Agent — 全闭环 Autopilot                 │
│  执行者: 架构师（编排者）                        │
│  触发: cron */30 * * * * (Asia/Shanghai)        │
│  模式: run_only                                 │
│  项目: agent-world (8dbe367e)                    │
├──────────────────────────────────────────────┤
│                                              │
│  ┌ Phase 1 感知 ──────────────────┐           │
│  │ 读取 backlog/in_progress/in_review           │
│  │ 按优先级排序: high > medium > low            │
│  └──────────────────────────────────┘           │
│                    ↓                           │
│  ┌ Phase 2 验证 ──────────────────┐  ← 优先执行 │
│  │ 检查 in_review 状态:                       │
│  │  ✅ 测试通过/CI green → done + merge       │
│  │  ❌ 测试失败/CI red   → 回退 todo + 反馈    │
│  │  ⏰ 停滞 24h 无变化    → @负责人催促          │
│  └──────────────────────────────────┘           │
│                    ↓                           │
│  ┌ Phase 3 检查停滞 ───────────────┐            │
│  │ 检查 in_progress 状态:                      │
│  │  💤 成员未工作          → @提醒              │
│  │  ⏰ 停滞 48h 无变化      → 回退 todo         │
│  └──────────────────────────────────┘           │
│                    ↓                           │
│  ┌ Phase 4 分配 ──────────────────┐            │
│  │ 仅当 in_progress < 2 时执行                    │
│  │ 从 backlog 选最高优先级 issue                 │
│  │ 按专长分配:                               │
│  │   Rust/Docker/CI  → 后端工程师              │
│  │   Python/LLM      → 全栈工程师              │
│  │   React/Dashboard  → 前端工程师              │
│  │ 标记 in_progress + 提取验收标准到评论          │
│  └──────────────────────────────────┘           │
│                    ↓                           │
│  ┌ Phase 5 反馈 ──────────────────┐            │
│  │ 本轮总结 + 退回原因记录                      │
│  │ 统计完成率 / 退回率                         │
│  └──────────────────────────────────┘           │
│                    ↓                           │
│            （每 30 分钟重复循环）                  │
└──────────────────────────────────────────────┘
```

## 实施步骤

### 1. 清理旧 Autopilot

| Autopilot | 操作 |
|-----------|------|
| 每日复盘 (8a4554fe) | 删除 — 观察反馈环已合并到 Phase 5 |
| 开发小队 (7644e756) | 暂停重命名为 "old-paused" — 分配逻辑已合并到 Phase 4 |
| 开发&review (20a3cd45) | 暂停重命名为 "old-paused" — 验证逻辑已合并到 Phase 2 |

### 2. 创建全闭环 Autopilot

```bash
multica autopilot create \
  --title "Loop Agent - agent-world 全闭环" \
  --agent 7a773682-0ac2-4201-aaaa-5a605dc3d9d5 \  # 架构师
  --mode run_only \
  --project 8dbe367e-3992-4804-9521-37bec6da19ff \  # agent-world
  --output json
```

### 3. 通过 REST API 添加 Cron 触发器

CLI 的 `autopilot create` 不会自动创建 schedule trigger，需要通过 API 添加：

```bash
curl -X POST "https://api.multica.ai/api/autopilots/<id>/triggers?workspace_id=<ws>" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"kind":"schedule","cron_expression":"*/30 * * * *","timezone":"Asia/Shanghai","enabled":true}'
```

> [!warning] CLI 限制
> Multica CLI 的 `autopilot create/update` 不支持 `--description-file`，中文内容需用 `pipes.quote()` 处理后传给 `--description`。触发器创建也需 REST API（CLI 无 schedule 创建命令）。

### 4. 配置 Agent 并发

所有执行者 agent 的 `max_concurrent_tasks` 从 6 调整为 **2**：

```bash
multica agent update <agent-id> --max-concurrent-tasks 2
```

### 5. 归档空壳 Agent

删除/归档 5 个无指令的占位 agent（test、UX Designer empty、Performance Engineer、Solution Architect、Security Engineer）。

## 关键设计决策

### 为什么是「一个 Autopilot」而非三个？

三个独立 Autopilot 的根本问题是**状态断裂**：

- 「分配」不知道「验证」的结果
- 「复盘」不知道「开发」的进度
- 每个 Autopilot 重复读取 issues，浪费 Token

合并为一个后，架构师在**单次执行中完整感知全局状态**，按优先级决定本轮做什么（先验证再分配），自然形成闭环。

### 为什么 30 分钟而非 10 分钟？

- 模型并发上限 2，每个 issue 的 LLM 调用 ≈ 2-5 分钟
- 10 分钟间隔会导致新旧任务重叠，超过并发限制
- 30 分钟确保上一轮完成后才启动下一轮
- 每日 48 次 × 单次 1 issue = 日吞吐 ~48 个 issue 阶段推进

### 为什么不是事件驱动？

Multica Autopilot 的 trigger 只支持 `schedule` 和 `webhook`。webhook 触发需要外部服务（如 CI webhook → Multica API），当前架构未配置。schedule 更简单可靠。

## 小队配置

| 角色 | Agent ID | 专长 | 分配方向 |
|------|----------|------|---------|
| 架构师（编排者） | `7a773682` | 系统架构、任务编排、质量把关 | Loop Agent 执行者 |
| 后端工程师 | `b28329c9` | Rust, API, Docker, 经济系统 | world-engine 相关 |
| 全栈工程师 | `caa25b9b` | Python, Agent 运行时, LLM | agent-runtime 相关 |
| 前端工程师 | `e5b02ab3` | React, TypeScript, Dashboard | dashboard 相关 |

## 与 Loop Engineering 理论的映射

| Loop Engineering 要素 | 本实践实现 |
|----------------------|-----------|
| 结构化状态机 | Issue 状态 (backlog → in_progress → in_review → done) + 退回机制 |
| 自动化反馈回路 | Phase 2 验证（检查评论 → done 或回退 todo + 具体反馈） |
| 可观测性与容错 | Phase 3 停滞检测（24h/48h 超时），Phase 5 反馈总结 |
| 循环边界与终止条件 | 每 30 分钟一个 cycle，all done 时自然空闲 |
| 评估-反馈模块 | in_review 评论检查 = 规则评估 + 语义评估（架构师 LLM） |

## 验证 Checklist

- [ ] Autopilot active 且 trigger cron `*/30 * * * *` enabled
- [ ] 所有执行者 agent `max_concurrent_tasks = 2`
- [ ] 旧 Autopilot 已暂停或删除
- [ ] 第一轮触发后：检查是否优先处理 in_review（而非直接分配 backlog）
- [ ] 分配时不超过 2 个 in_progress
- [ ] 退回 issue 时评论区有具体原因

## 改进方向

1. **事件驱动触发** — CI webhook → Multica API，issue 状态变更时即时触发（而非等 30 分钟）
2. **自动化验收** — Autopilot 触发 `cargo test`/`pytest`，用测试结果代替人工评论检查
3. **多项目复用** — 将描述参数化（项目 ID、成员映射），支持一键创建新项目的 Loop Agent
4. **退回率监控** — Phase 5 的反馈数据写入指标，持续优化分配策略

## 相关页面

- [[loop-engineering]] — Loop Engineering 理论基础：状态机 + 反馈回路 + 可观测性
- [[agent-world]] — agent-world 项目：Rust 世界引擎 + Python Agent + Next.js Dashboard
- [[multica]] — Multica 平台：AI 原生任务管理 + Autopilot 编排
- [[multica-technical-highlights]] — Multica 技术架构：多租户、Agent 沙箱、运行时发现
- [[claude-code-workflow]] — Claude Code Workflow：确定性多 agent 编排，含 loop 模式
- [[agno-demo-os]] — Agno 四层评估体系 + 自动改进循环（对比参考）
