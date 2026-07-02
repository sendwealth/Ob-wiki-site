---
title: Multica 如何使用 ACP 连接 Agent
date: 2026-05-20
tags: [multica, acp, agent, integration, architecture]
---

# Multica 如何使用 ACP 连接 Agent

## 概述

Multica 通过 **ACP (Agent Client Protocol)** 协议与多种 Agent 进行标准化通信。核心通信方式是 **JSON-RPC 2.0 over stdin/stdout**。

## 支持的 Agent

| Agent      | 提供商              | 启动命令           |
| ---------- | ---------------- | -------------- |
| **Hermes** | Anthropic Claude | `hermes acp`   |
| **Kimi**   | 月之暗面             | `kimi acp`     |
| **Kiro**   | 自研               | `kiro-cli acp` |

所有 Agent 共享同一套 ACP 通信协议，只在启动参数和工具名称映射上有差异。

## 架构设计

```
┌─────────────────────────────────────────────┐
│           Multica Daemon                    │
│  ┌───────────────────────────────────────┐  │
│  │  hermesBackend / kimiBackend          │  │
│  │  / kiroBackend (Backend 接口)         │  │
│  └───────────────────────────────────────┘  │
│                    │                        │
│                    ▼                        │
│  ┌───────────────────────────────────────┐  │
│  │         hermesClient                  │  │
│  │    (ACP JSON-RPC 2.0 传输层)         │  │
│  │  • 请求/响应管理                      │  │
│  │  • 通知处理                           │  │
│  │  • 工具权限自动批准                   │  │
│  └───────────────────────────────────────┘  │
│         │ stdin/stdout │                    │
└─────────┼──────────────┼────────────────────┘
          │              │
          ▼              ▼
   ┌──────────┐   ┌──────────┐
   │  hermes  │   │   kimi   │
   │   acp    │   │   acp    │
   └──────────┘   └──────────┘
```

### 核心组件

1. **Backend 接口** - 统一的 Agent 后端抽象
2. **hermesClient** - ACP 协议实现（三个 Agent 共享）
3. **stdin/stdout 管道** - 进程间通信通道

## 完整工作流程（6 个阶段）

### 阶段 1: 进程启动

```go
// 启动 Agent 进程
cmd := exec.Command(agentPath, "acp", args...)
cmd.Stdin = stdinPipe   // Multica → Agent
cmd.Stdout = stdoutPipe // Agent → Multica
cmd.Stderr = stderrPipe // 错误日志
cmd.Start()
```

### 阶段 2: 初始化握手

**Multica → Agent:**
```json
{
  "jsonrpc": "2.0",
  "method": "initialize",
  "params": {
    "clientInfo": {"name": "multica", "version": "0.3.1"},
    "capabilities": {"tools": true, "mcp": true}
  }
}
```

**Agent → Multica:**
```json
{
  "result": {
    "serverInfo": {"name": "hermes", "version": "1.0.0"},
    "capabilities": {"loadSession": true, "models": [...]}
  }
}
```

### 阶段 3: 会话管理

#### 创建新会话
```json
{
  "method": "session/new",
  "params": {
    "cwd": "/path/to/project",
    "model": "claude-3-5-sonnet-20241022"
  }
}
// 返回: {"sessionId": "sess_abc123"}
```

#### 恢复已有会话
```json
{
  "method": "session/load",
  "params": {"resumeSessionId": "sess_abc123"}
}
```

### 阶段 4: 发送提示

```json
{
  "method": "session/prompt",
  "params": {
    "sessionId": "sess_abc123",
    "prompt": "用户的任务描述"
  }
}
```

### 阶段 5: 流式更新（关键）

Agent 通过 **通知（Notification）** 实时推送进度：

```json
// 1. Agent 思考内容
{"method": "session/update", "params": {
  "type": "agent_thought_chunk",
  "content": "我需要先读取配置文件..."
}}

// 2. Agent 消息
{"method": "session/update", "params": {
  "type": "agent_message_chunk",
  "content": "我发现了问题..."
}}

// 3. 工具调用开始
{"method": "session/update", "params": {
  "type": "tool_call",
  "id": "tool_001",
  "name": "read_file",
  "input": {"path": "config.json"}
}}

// 4. 工具执行结果
{"method": "session/update", "params": {
  "type": "tool_result",
  "id": "tool_001",
  "content": "文件内容..."
}}

// 5. Token 使用统计
{"method": "session/update", "params": {
  "type": "usage_update",
  "inputTokens": 1500,
  "outputTokens": 800
}}
```

### 阶段 6: 工具权限自动批准

```go
// Multica 自动批准所有工具调用
func (b *HermesBackend) AcceptNotification(notificationID string) error {
    return b.client.Call("notification/accept", map[string]any{
        "notificationId": notificationID,
    }, nil)
}
```

**环境变量控制：**
```bash
HERMES_YOLO_MODE=1  # 自动批准所有工具
```

## JSON-RPC 三种通信模式

| 模式 | 方向 | 是否需要响应 | 示例 |
|------|------|-------------|------|
| **请求/响应** | Client → Agent | ✅ 是 | `initialize`, `session/new`, `session/prompt` |
| **通知** | Agent → Client | ❌ 否 | `session/update` (流式进度) |
| **Client 方法** | Agent → Client | ✅ 是 | `notification/accept`, `tool/call` |

## 并发安全机制

```go
type hermesClient struct {
    mu            sync.Mutex              // 保护共享状态
    pendingRPC    map[uint64]chan rpcResponse  // 待处理的请求
    onMessage     func(notification)      // 消息回调
}

// 三个并发 goroutine
// 1. stdout 读取 → 解析 JSON-RPC 消息
// 2. stderr 读取 → 捕获错误日志
// 3. 主流程 → 驱动 ACP 生命周期
```

## 错误处理

### 1. 提供商错误嗅探
```go
// 监听 stderr，检测认证错误
if strings.Contains(line, "AuthenticationError") {
    return ErrProviderAuth
}
if strings.Contains(line, "rate_limit_error") {
    return ErrRateLimit
}
```

### 2. 超时处理
```go
ctx, cancel := context.WithTimeout(ctx, opts.Timeout)
defer cancel()

select {
case <-ctx.Done():
    return nil, fmt.Errorf("timeout")
case result := <-responseChan:
    return result, nil
}
```

### 3. 会话恢复失败
```go
// 如果恢复失败，自动创建新会话
if err := c.request(ctx, "session/load", params, &result); err != nil {
    return c.request(ctx, "session/new", params, &result)
}
```

## 支持新 Agent 的要求

### Agent 侧需要实现

#### 必须实现的方法
1. `initialize` - 初始化握手
2. `session/new` - 创建会话
3. `session/prompt` - 接收提示

#### 必须发送的通知
1. `session/update` - 流式进度更新
   - `agent_thought_chunk` - 思考内容
   - `agent_message_chunk` - 消息内容
   - `tool_call` - 工具调用
   - `tool_result` - 工具结果
   - `usage_update` - Token 统计

#### 通信协议要求
- JSON-RPC 2.0 格式
- stdin/stdout 管道通信
- 每行一个完整 JSON 对象（换行符分隔）

### Multica 侧需要做

#### 1. 添加 Backend 实现
```go
// server/internal/agent/backend/newagent.go
type newAgentBackend struct {
    cfg Config
}

func (b *newAgentBackend) Execute(ctx context.Context, prompt string, opts ExecOptions) (*Session, error) {
    // 复用 hermesClient
    client := newHermesClient(stdin, stdout, ...)
    return client.Execute(ctx, prompt, opts)
}
```

#### 2. 注册到 config.go
```go
var launchHeaders = map[string]string{
    "claude":     "claude (stream-json)",
    "codex":      "codex app-server",
    "hermes":     "hermes acp",
    "kimi":       "kimi acp",
    "kiro":       "kiro-cli acp",
    "new-agent":  "new-agent acp",  // 新增
}
```

#### 3. 实现特定处理逻辑（可选）
- 工具名称规范化（如果 Agent 使用非标准工具名）
- 参数累积（如 Kimi 的流式参数）
- 历史重放过滤

## 与其他协议的关系

| 协议 | 作用域 | Multica 使用 | 说明 |
|------|--------|-------------|------|
| **ACP** | 编辑器 ↔ Agent | ✅ 主要通信协议 | 管理 Agent 生命周期和任务执行 |
| **MCP** | Agent ↔ 工具 | ✅ 透传给 Agent | Agent 通过 MCP 访问外部工具 |
| **A2A** | Agent ↔ Agent | ❌ 未使用 | 未来可能用于 Agent 协作 |

### ACP 的 MCP 透传能力

```json
// Multica 在 initialize 时声明 MCP 能力
{
  "clientCapabilities": {
    "mcp": {
      "servers": {
        "filesystem": {"command": "mcp-server-filesystem"},
        "github": {"command": "mcp-server-github"}
      }
    }
  }
}

// Agent 可以通过 MCP 调用这些工具
// Multica 负责启动 MCP 服务器并转发请求
```

## 代码复用

Hermes、Kimi、Kiro 三个 Agent **共享同一个 `hermesClient` 实现**：

```go
// hermes.go
type hermesBackend struct { cfg Config }

// kimi.go
type kimiBackend struct { cfg Config }

// kiro.go
type kiroBackend struct { cfg Config }

// 三者都使用相同的 hermesClient 进行 ACP 通信
// 只在以下方面有差异：
// 1. 启动命令 (hermes acp / kimi acp / kiro-cli acp)
// 2. 工具名称规范化 (normalizeToolName)
// 3. 特定参数处理 (如 Kimi 的流式参数累积)
```

## 性能优化

### 1. 缓冲区优化
```go
scanner := bufio.NewScanner(stdout)
// 设置 10MB 缓冲区，处理大型输出
scanner.Buffer(make([]byte, 0, 1024*1024), 10*1024*1024)
```

### 2. 管道并发读取
```go
// stdout 读取 goroutine
go func() {
    for scanner.Scan() {
        c.handleLine(scanner.Text())
    }
}()

// stderr 读取 goroutine
go func() {
    io.Copy(stderrSink, stderr)
}()

// 主 goroutine 驱动 ACP 生命周期
go func() {
    c.request(ctx, "initialize", ...)
    c.request(ctx, "session/new", ...)
    c.request(ctx, "session/prompt", ...)
}()
```

## 总结

Multica 的 ACP 集成展示了一个完整的 JSON-RPC 2.0 客户端实现：

1. **标准化通信** - 通过 stdin/stdout 管道进行 JSON-RPC 2.0 通信
2. **异步处理** - 请求/响应和通知分离，支持流式更新
3. **并发安全** - 多 goroutine 协作，使用互斥锁保护共享状态
4. **错误恢复** - 会话恢复、超时处理、提供商错误捕获
5. **代码复用** - 单一 ACP 客户端实现支持多个 Agent
6. **易扩展** - 新 Agent 只需实现 ACP 规范即可接入

这种架构使得 Multica 可以轻松集成任何支持 ACP 协议的 Agent，只需实现特定的启动逻辑和工具名称映射即可。

## 相关文档

- [[acp-protocol]] - ACP 协议深度技术参考
- [[multica-acp-workflow]] - Multica ACP 工作流程详解（完整代码级分析）
- [[a2a-protocol]] - A2A 协议对比
- [[multica]] - Multica 项目架构
