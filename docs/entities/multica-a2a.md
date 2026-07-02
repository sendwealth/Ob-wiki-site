---
title: Multica A2A Protocol
created: 2026-05-14
updated: 2026-06-28
type: entity
tags: [multica, a2a, agent, protocol, feature]
sources: ["PR #2613", "Issue #2605"]
confidence: high
---

# Multica A2A Protocol

> Multica daemon 的 A2A 协议支持正在 PR review 中（[#2613](https://github.com/multica-ai/multica/pull/2613)），尚未合并到 main。以下为设计方案和实现状态。

---

## 一、为什么需要 A2A

之前 Multica 只支持**本地 CLI Agent**（Claude Code、Codex、Copilot 等）。Daemon 在用户机器上 spawn 一个进程，解析 stdout。

问题：
- 自研 Agent、内部 Agent、云端 Agent 无法接入
- 用户必须本地安装每个 Agent 的 CLI
- 不符合 Linux Foundation / Google 推出的 A2A 开放标准

A2A 协议让 Multica 能连接**任何实现了 A2A 规范的 Agent 服务**，无论它跑在哪里。

## 二、架构

```
用户机器                         Agent 服务（任意位置）
┌──────────────────┐            ┌───────────────────┐
│  Multica Daemon  │            │  A2A Agent         │
│                  │  JSON-RPC  │                    │
│  a2a-agents.yaml │──────────→│  /.well-known/     │
│  配置 Agent URL  │  2.0 over  │  agent-card.json   │
│                  │  HTTP/SSE  │                    │
│  发现 → 注册     │            │  POST /            │
│  分发 → 传输结果  │            │  SendMessage       │
│                  │            │  SendStreamingMsg  │
└──────────────────┘            │  CancelTask        │
         │                      └───────────────────┘
         │ 注册 runtime
         ↓
┌──────────────────┐
│  Multica Server  │  ← UI 显示 Agent 为 runtime
│  (api.multica.ai)│  ← 任务分发走 daemon
└──────────────────┘
```

Daemon 是中间层：它向 Server 注册 A2A Agent 为 runtime，收到任务后通过 JSON-RPC 转发给 Agent 服务。

## 三、发现机制（三种模式）

### 3.1 配置文件发现

创建 `~/.multica/a2a-agents.yaml`（或 `~/.multica/profiles/<name>/a2a-agents.yaml`）：

```yaml
agents:
  - name: "code-reviewer"
    url: "http://127.0.0.1:8900"
  - name: "research-agent"
    url: "https://agents.example.com/research"
    auth:
      scheme: "openid-connect"
      token_env: "RESEARCH_AGENT_TOKEN"
```

Daemon 启动时对每个 URL `GET /.well-known/agent-card.json`，验证 Agent 在线。

### 3.2 本地端口扫描

自动扫描 `localhost:8900-8910`，发现本地运行的 A2A Agent。无需配置。

### 3.3 注册中心轮询

企业部署可配置中央注册中心：

```yaml
registry:
  url: "https://registry.example.com/agents"
  token_env: "REGISTRY_TOKEN"
  poll_interval: 300
```

Daemon 每 300s 轮询一次，发现新 Agent 自动注册。

## 四、Agent Card

A2A Agent 必须暴露 `GET /.well-known/agent-card.json`，最小示例：

```json
{
  "name": "my-agent",
  "version": "1.0.0",
  "capabilities": { "streaming": true },
  "skills": [
    { "id": "echo", "name": "Echo", "description": "Echoes input" }
  ]
}
```

Multica 读取的字段：`name`、`version`、`capabilities.streaming`、`skills`。

## 五、任务分发

### 5.1 阻塞模式（SendMessage）

Agent Card 无 `streaming: true` 时使用。一次 HTTP 请求-响应：

```json
→ POST /
{
  "jsonrpc": "2.0",
  "id": "task-id",
  "method": "SendMessage",
  "params": {
    "message": {
      "role": "ROLE_USER",
      "parts": [{"text": "Fix the login bug"}]
    }
  }
}

← 200 OK
{
  "jsonrpc": "2.0",
  "id": "task-id",
  "result": {
    "task": {
      "id": "agent-task-id",
      "status": {
        "state": "TASK_STATE_COMPLETED",
        "message": {"role": "agent", "parts": [{"text": "Done!"}]}
      }
    }
  }
}
```

### 5.2 流式模式（SendStreamingMessage + SSE）

Agent Card 有 `streaming: true` 时使用。Daemon 发 `Accept: text/event-stream`，读 SSE 事件流：

```
→ POST / (Accept: text/event-stream)

← data: {"result": {"task": {"status": {"state": "TASK_STATE_WORKING", ...}}}}
← data: {"result": {"task": {"status": {"state": "TASK_STATE_WORKING", ...}}}}
← data: {"result": {"task": {"status": {"state": "TASK_STATE_COMPLETED", ...}}}}
```

WORKING 状态触发 `ReportProgress`，COMPLETED 结束流。

### 5.3 取消（CancelTask）

Daemon context 取消时自动发 CancelTask：

```json
→ POST /
{
  "method": "CancelTask",
  "params": {"id": "task-id", "reason": "cancelled by daemon"}
}
```

## 六、状态映射

| A2A 状态 | Multica 动作 |
|---|---|
| `TASK_STATE_COMPLETED` | `completed`，带输出文本 |
| `TASK_STATE_FAILED` / `TASK_STATE_REJECTED` | `blocked`，带错误信息 |
| `TASK_STATE_CANCELED` | `cancelled` |
| `TASK_STATE_INPUT_REQUIRED` | `blocked` |
| `TASK_STATE_AUTH_REQUIRED` | `blocked` |
| `TASK_STATE_WORKING`（SSE） | `ReportProgress` 更新 |

## 七、认证透传

三种 scheme：

| Scheme | Header | 格式 |
|---|---|---|
| `bearer`（默认） | `Authorization` | `Bearer <token>` |
| `api-key` | 自定义 `header` 字段 | 直接放 token，不加 Bearer 前缀 |
| `openid-connect` | 自定义 `header` 字段 | `Bearer <token>` |

Token 从环境变量读取（`token_env` 字段）。

## 八、健康探测

每个 A2A Agent 启动一个后台 goroutine，每 30s `GET /.well-known/agent-card.json` 做存活检查。失败记 warn 日志，不影响任务分发。

## 九、代码变更

PR: [#2613](https://github.com/multica-ai/multica/pull/2613)，Closes: [#2605](https://github.com/multica-ai/multica/issues/2605)

### 文件清单

| 文件 | 类型 | 说明 |
|---|---|---|
| `server/internal/daemon/a2a.go` | 新增 | A2A 核心实现（配置、发现、分发、认证、健康探测、端口扫描、注册中心） |
| `server/internal/daemon/a2a_test.go` | 新增 | 49 个单元测试 |
| `server/internal/daemon/a2a_integration_test.go` | 新增 | 6 个集成测试（完整生命周期） |
| `server/internal/daemon/types.go` | 修改 | `AgentEntry` 新增 `A2AAuth` 字段 |
| `server/internal/daemon/config.go` | 修改 | 注册中心配置透传 |
| `server/internal/daemon/daemon.go` | 修改 | 线程安全 agent 访问、A2A 感知的 runtime 注册 |

### 生产加固（Code Review 修复）

| 问题 | 严重度 | 修复 |
|---|---|---|
| A2A agent 在 runtime 注册时被静默丢弃 | P0 | `detectAgentVersion` 对 A2A agent 跳过，用 Agent Card version |
| `d.cfg.Agents` map 数据竞争 | P0 | `agentsMu sync.RWMutex` + 线程安全访问器 |
| SSE scanner.Err() 未检查 | P1 | 循环后加 error log |
| HTTP client 每次请求新建（无连接池） | P1 | 提取共享 `a2aHTTPClient` |
| SSRF 风险（YAML URL 未校验） | P1 | `validateA2AURL()` 拒绝非 http(s) scheme |

## 十、向后兼容性

**完全兼容。** A2A 是纯增量路径：

- 没有 `a2a-agents.yaml` → `loadA2AConfig` 返回 nil → 所有 A2A 代码不执行
- CLI agent 的 `Mode` 字段默认空字符串，走原有 `else` 分支
- `agentsMu` 读写锁在无竞争时 RLock 几乎零开销
- 现有 CLI agent 路径（spawn 进程 → 解析 stdout）一行没改

## 十一、当前状态

- **PR**: [#2613](https://github.com/multica-ai/multica/pull/2613)（review 中，未合并）
- **实现**: Phase 1/2/3 全部完成，Code Review 发现的 6 个问题已修复
- **测试**: 49 个单元测试 + 6 个集成测试，全部通过 `-race`
- **端到端验证**: 用 mock A2A agent 在本地验证了完整流程（发现 → 注册 → 分发 → 完成）

---

## 最新动态（截至 2026-06-28）

> [!note] A2A 支持从"实验特性"转为"生产能力"
> 2026 年 Multica 的 A2A 集成已落地为生产特性，与 Runtime 发现机制（[[multica-runtime-discovery]]）共同构成 Multica 的 agent 接入底座。详见 [[multica]] 最新动态。

### 生态信号
- A2A 协议本身在 2026 年成为行业热点（Google ADK 2.0 原生支持、[[zed]] ACP 获 JetBrains 背书），Multica 的早期 A2A 押注获得验证
- 与 [[adk-python]] 2.0 GA 的 collaborative agents 形成互补：ADK 提供多 agent 构建，Multica A2A 提供跨 agent 调度
- 端到端验证流程（发现 → 注册 → 分发 → 完成）已稳定

### 仍待观察
- A2A agent 的实际生态规模（多少外部 agent 接入）
- 与 MCP 的协同（A2A 跨 agent，MCP 单 agent 工具扩展）

## 相关链接

- [[multica]] — Multica 项目总览
- [[multica-runtime-discovery]] — Runtime 发现机制
