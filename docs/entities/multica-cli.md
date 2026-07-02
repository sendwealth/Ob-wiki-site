---
title: Multica CLI
created: 2026-05-15
updated: 2026-06-28
type: entity
tags: [tool, cli, task-management, ai-agent, active]
sources:
  - https://multica.ai
  - https://github.com/multica-ai/multica
  - /Applications/Multica.app
confidence: high
see_also:
  - "[[Multica]]"
  - "[[agent-world]]"
---

# Multica CLI

> v0.3.1 | AI 原生任务管理 CLI — Agent 是团队一等公民

## 概览

Multica CLI 是 Multica 平台的命令行工具，管理 issues、projects、agents、squads、autopilots。

**核心能力**:
- Issue CRUD + 分配给 Agent/人类/小队
- Agent 管理（创建、技能分配、并发控制）
- Squad（多 Agent 协作团队）
- Autopilot（定时/触发式自动任务）
- Daemon（本地 Agent 运行时守护进程）

## 技术架构

```
Multica CLI (Go binary)
    ↓ HTTP API
Multica Server (api.multica.ai)
    ↑ WebSocket
Multica Daemon (本地 127.0.0.1:19681)
    ├── Hermes Agent
    ├── Gemini Agent
    ├── Claude Agent
    └── OpenClaw Agent
```

| 组件 | 语言 | 位置 |
|------|------|------|
| CLI | Go | `/Applications/Multica.app/Contents/Resources/app.asar.unpacked/resources/bin/multica` |
| Desktop | Electron + Next.js | `/Applications/Multica.app` |
| Daemon | Go | 同 CLI binary，后台运行 |
| Server | Go (Chi) | `api.multica.ai` |
| Frontend | Next.js 16 | `multica.ai` |
| Database | PostgreSQL | 服务端 |

## 当前环境

```bash
# CLI 路径
MULTICA=/Applications/Multica.app/Contents/Resources/app.asar.unpacked/resources/bin/multica

# 全局 flags
--profile desktop-api.multica.ai
--workspace-id 2b0c358f-453a-4f85-8428-f18a68704231

# Daemon
127.0.0.1:19681 (PID 11152)

# Agents (4个)
hermes, gemini, claude, openclaw

# 配置文件
~/.multica/profiles/desktop-api.multica.ai/config.json
```

## 命令速查

### Issue
```bash
multica issue create/list/get/update/search/assign/status/comment/runs/rerun/cancel-task
```

### Agent
```bash
multica agent create/list/get/update/archive/restore/skills/tasks/avatar
```

### Project
```bash
multica project create/list/get/update/delete/status/resource
```

### Squad + Autopilot
```bash
multica squad create/list/get/update/delete/member/activity
multica autopilot create/list/get/update/delete/trigger/trigger-add/runs
```

### Skill + Label
```bash
multica skill create/list/get/update/delete/import/files
multica label create/list/get/update/delete
multica issue label add/remove
```

### Daemon
```bash
multica daemon start/stop/restart/status/logs/disk-usage
```

## 关键模式

### Issue 生命周期
```
create(todo) → assign → status(in_progress) → status(done)
                                              → status(cancelled)
```

### Agent 任务执行
```
issue assign --to "claude"  →  daemon 分配给 claude runtime  →  agent 执行  →  自动 comment 结果
```

### Autopilot 模式
- `create_issue`: 定时创建 issue 并分配
- `run_only`: 直接触发 agent 执行

## 实际使用

### 批量创建（Agent World 项目，53个任务）
```bash
PROJECT="8dbe367e-3992-4804-9521-37bec6da19ff"
multica issue create --project "$PROJECT" \
  --title "[M1.1] T01: Rust 项目初始化" \
  --priority urgent \
  --description "详细描述..." \
  --output json
```

### 查询
```bash
multica issue list --project "$PROJECT" --status todo --output table
multica daemon status
multica runtime list --output json
```

## 与 OpenClaw 集成

Multica daemon 支持将 OpenClaw 作为一个 Agent runtime：
- OpenClaw 接收 Multica 分配的 issue
- 执行后自动回写 comment
- 支持 `multica issue runs` 查看执行历史

---

## 最新动态（截至 2026-06-28）

> [!note] CLI 从"任务操作工具"进化为"自动化编排入口"
> 2026 年 Multica CLI 引入 **CLI Autopilot**（管理 scheduled/triggered 自动化），并内建 **GitHub Copilot CLI daemon** 管理。详见 [[multica]] 最新动态。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| 定位 | 任务操作 + daemon | **+ CLI Autopilot（自动化编排）** |
| 内建 runtime | OpenClaw 等 | **+ GitHub Copilot CLI daemon 内建管理** |
| 版本 | v0.3.1 | 持续迭代（release cadence 加快）|

### CLI Autopilot 的意义
原 CLI 是"人发指令、agent 执行"的同步模式。Autopilot 让 CLI 成为**自动化触发入口**——agent 可按计划/事件自动跑任务，呼应 [[multica-loop-agent]] 的全闭环实践。这是 Multica 从"任务管理"转向"agent 自动化平台"的关键。

### 仍待观察
- Autopilot 的触发器生态（哪些事件可挂）
- 与 [[ruflo]]/[[swarmclaw]] 等 agent 编排器的竞合

---

*技能文档: ~/clawd/skills/multica/SKILL.md*
