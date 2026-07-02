---
title: Multica Runtime 发现机制
created: 2026-05-14
updated: 2026-05-14
type: concept
tags: [ai, agent, platform, project]
sources: [~/Projects/multica]
confidence: high
---

# Multica Runtime 发现机制

> Multica 的 runtime 是本地 daemon（守护进程）自动探测并注册到服务端的。任何在 `$PATH` 上能被 `exec.LookPath` 找到的 agent CLI 都会被当作 runtime 发现。

---

## 一、发现流程总览

```
Daemon 启动
    ↓
扫描 $PATH 上的 Agent CLI 二进制文件
    ↓
对每个找到的 CLI：检测版本 → 检查最低版本要求
    ↓
POST /api/daemon/register → 服务端 UpsertAgentRuntime
    ↓
心跳保活（WS 或 HTTP）→ 更新 last_seen_at
    ↓
服务端根据 last_seen_at 计算健康状态
```

## 二、本地 CLI 探测

Daemon 启动时（`server/internal/daemon/config.go`），逐一调用 `exec.LookPath()` 扫描 `$PATH`：

| Provider | 默认二进制名 | 环境变量覆盖 |
|---|---|---|
| claude | `claude` | `MULTICA_CLAUDE_PATH` |
| codex | `codex` | `MULTICA_CODEX_PATH` |
| opencode | `opencode` | `MULTICA_OPENCODE_PATH` |
| openclaw | `openclaw` | `MULTICA_OPENCLAW_PATH` |
| hermes | `hermes` | `MULTICA_HERMES_PATH` |
| gemini | `gemini` | `MULTICA_GEMINI_PATH` |
| pi | `pi` | `MULTICA_PI_PATH` |
| cursor | `cursor-agent` | `MULTICA_CURSOR_PATH` |
| copilot | `copilot` | `MULTICA_COPILOT_PATH` |
| kimi | `kimi` | `MULTICA_KIMI_PATH` |
| kiro | `kiro-cli` | `MULTICA_KIRO_PATH` |

每种 provider 都可以通过 `MULTICA_*_PATH` 环境变量指定自定义路径。找到的 CLI 加入 `Config.Agents` map（key 为 provider 名称）。**至少要找到一个**，否则 daemon 启动失败：

```
no agent CLI found: install claude, codex, copilot, opencode, openclaw,
hermes, gemini, pi, cursor-agent, kimi, or kiro-cli and ensure it is on PATH
```

### 版本检测

每个找到的 CLI 还需通过 `detectAgentVersion()` 获取版本号，再经 `checkAgentMinVersion()` 校验最低版本要求。版本过老的 agent 会被跳过（warn 日志），不影响其他 agent 注册。

## 三、向服务端注册

Daemon 对每个有效 agent 调用 `registerRuntimesForWorkspace()`：

1. 组装 runtime 信息：`name`（首字母大写 + 设备名）、`type`（provider）、`version`、`status=online`
2. POST 到 `POST /api/daemon/register`

### 注册请求体

```json
{
  "workspace_id": "uuid",
  "daemon_id": "persistent-uuid",
  "legacy_daemon_ids": ["old-hostname-id"],
  "device_name": "My MacBook",
  "cli_version": "0.1.13",
  "launched_by": "desktop",
  "timezone": "Asia/Shanghai",
  "runtimes": [
    { "name": "Claude (My MacBook)", "type": "claude", "version": "1.0.0", "status": "online" },
    { "name": "Codex (My MacBook)", "type": "codex", "version": "0.1.0", "status": "online" }
  ]
}
```

### 服务端处理

`DaemonRegister` handler（`server/internal/handler/daemon.go`）对每个 runtime 调用 `UpsertAgentRuntime` —— 按 `(workspace_id, daemon_id, provider)` 做 upsert：

- **新 runtime** → INSERT，设置 owner、timezone、metadata
- **已有 runtime** → UPDATE status=online、last_seen_at，保留用户覆盖的 timezone
- **Legacy daemon_id 匹配** → 自动合并旧行到新行，agent 绑定和任务不丢失

每个 runtime 在数据库中存储：

| 字段 | 说明 |
|---|---|
| `workspace_id` | 所属工作空间 |
| `daemon_id` | 来源 daemon 的持久 UUID |
| `name` | 显示名（如 "Claude (My MacBook)"） |
| `runtime_mode` | 固定为 `local`（当前仅支持本地 daemon） |
| `provider` | agent 类型（claude/codex/...） |
| `status` | online / offline |
| `device_info` | 设备名 + 版本 |
| `timezone` | 时区（用于 token 用量按本地日聚合） |
| `visibility` | private（默认）/ public |
| `last_seen_at` | 最后心跳时间 |

## 四、心跳保活

注册成功后，daemon 为每个 runtime 启动定期心跳，双通道冗余：

### WebSocket 心跳（首选）

通过持久 WS 连接发送心跳，轻量且能实时接收服务端指令（model list 请求、local skill 请求等）。

### HTTP 心跳（fallback）

`POST /api/daemon/heartbeat`，当 WS 不可用或静默时自动接管：

```
Daemon → POST /api/daemon/heartbeat
         { "runtime_id": "uuid" }
         ↓
服务端 → 更新 last_seen_at
         → 检查 pending 指令（model list、update、local skills）
         → 返回 ack
```

心跳间隔可配置，WS 和 HTTP 互斥 —— WS 最近 ack 过的 runtime 跳过 HTTP 心跳。

## 五、健康状态计算

前端根据 `last_seen_at` 将 runtime 分为四档（`packages/core/runtimes/types.ts`）：

| 状态 | 条件 | UI 颜色 | 含义 |
|---|---|---|---|
| `online` | 心跳阈值内 | 绿色 | 正常运行 |
| `recently_lost` | 离线 < 5 分钟 | 琥珀色 | 可能短暂中断 |
| `offline` | 离线 5 分钟 ~ 7 天 | 灰色 | 已离线 |
| `about_to_gc` | 距 7 天 GC 阈值 < 1 天 | 暗色 | 即将被服务端清理 |

前端通过 `derive-health.ts` 从原始 `status` + `last_seen_at` 计算出 `RuntimeHealth` 枚举，驱动列表、卡片和 tooltip 展示。

## 六、Runtime 恢复机制

如果服务端删除了 runtime 行（如 GC 清理或用户手动删除），daemon 会自动恢复：

```
心跳 → 收到 404 "runtime not found"
    ↓
handleRuntimeGone(runtimeID)
    ↓
removeStaleRuntime() — 从本地状态清除
    ↓
reregisterWorkspaceAfterRuntimeGone() — 重新注册
    ↓
新 runtime ID 写入本地状态，恢复心跳
```

恢复有防抖（coalesce）机制：同一 workspace 在短时间内多次 runtime 丢失只会触发一次重新注册，避免并发 stampede。

## 七、API 路由

| 路由 | 方法 | 说明 |
|---|---|---|
| `/api/daemon/register` | POST | Daemon 注册 runtimes |
| `/api/daemon/deregister` | POST | Daemon 下线注销 |
| `/api/daemon/heartbeat` | POST | HTTP 心跳 |
| `/api/daemon/ws` | GET | WebSocket 连接 |
| `/api/runtimes` | GET | 列出 workspace 下所有 runtimes |
| `/api/runtimes/{id}` | PATCH | 更新 runtime（名称、时区、可见性） |
| `/api/runtimes/{id}` | DELETE | 删除 runtime |
| `/api/runtimes/{id}/usage` | GET | Token 用量（按天聚合） |

---

## 关键源码文件

| 文件 | 职责 |
|---|---|
| `server/internal/daemon/config.go` | CLI 探测、Config 构建 |
| `server/internal/daemon/daemon.go` | 注册、心跳、runtime 恢复 |
| `server/internal/daemon/client.go` | HTTP client（register/heartbeat/deregister） |
| `server/internal/handler/daemon.go` | 服务端 register/heartbeat handler |
| `server/internal/handler/runtime.go` | 用户侧 runtime CRUD |
| `packages/core/runtimes/types.ts` | RuntimeHealth 枚举 |
| `packages/core/runtimes/derive-health.ts` | 健康状态计算 |
| `packages/core/runtimes/queries.ts` | 前端 runtime 查询 |

---

## 相关链接

- [[multica]] — Multica 整体架构
- [[heuristic-learning]] — coding agent 学习范式
- [[context-mode]] — AI 编码 Agent 上下文优化
