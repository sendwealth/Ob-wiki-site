---
title: Multica ACP 工作流程详解
date: 2026-05-20
tags: [multica, acp, agent, protocol, architecture]
---

# Multica ACP 工作流程详解

## 概述

Multica 作为 ACP 客户端，通过 JSON-RPC 2.0 协议与支持 ACP 的 Agent（Hermes、Kimi、Kiro）进行通信。本文详细说明 Multica 如何使用 ACP 协议驱动 Agent 执行任务。

## 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│                    Multica Daemon                           │
│  ┌───────────────────────────────────────────────────────┐  │
│  │              hermesBackend / kimiBackend              │  │
│  │              / kiroBackend (实现 Backend 接口)        │  │
│  └───────────────────────────────────────────────────────┘  │
│                           │                                 │
│                           ▼                                 │
│  ┌───────────────────────────────────────────────────────┐  │
│  │                  hermesClient                         │  │
│  │         (ACP JSON-RPC 2.0 传输层实现)                 │  │
│  │  • 请求/响应管理 (pending map)                        │  │
│  │  • 通知处理 (session/update)                          │  │
│  │  • 工具权限自动批准                                   │  │
│  └───────────────────────────────────────────────────────┘  │
│              │ stdin/stdout                │                │
└──────────────┼─────────────────────────────┼────────────────┘
               │                             │
               ▼                             ▼
    ┌──────────────────┐         ┌──────────────────┐
    │  hermes acp      │         │   kimi acp       │
    │  (Agent 进程)    │         │   kiro-cli acp   │
    └──────────────────┘         └──────────────────┘
```

## 核心组件

### 1. Backend 接口

所有 Agent 后端实现统一的 `Backend` 接口：

```go
type Backend interface {
    Execute(ctx context.Context, prompt string, opts ExecOptions) (*Session, error)
}
```

**ExecOptions 包含：**
- `Cwd` - 工作目录
- `Model` - 模型名称
- `SystemPrompt` - 系统提示词
- `MaxTurns` - 最大轮次
- `Timeout` - 超时时间
- `ResumeSessionID` - 恢复会话 ID
- `CustomArgs` - 自定义参数
- `McpConfig` - MCP 配置
- `ThinkingLevel` - 思考级别

### 2. hermesClient (ACP 传输层)

`hermesClient` 是 ACP 协议的核心实现，负责：
- JSON-RPC 2.0 请求/响应管理
- stdin/stdout 管道通信
- 会话更新通知处理
- 工具权限自动批准

**关键数据结构：**

```go
type hermesClient struct {
    stdin        io.Writer
    writeMu      sync.Mutex          // 序列化 stdin 写入
    mu           sync.Mutex
    nextID       int                 // JSON-RPC 请求 ID
    pending      map[int]*pendingRPC // 待处理的 RPC 请求
    sessionID    string              // 当前会话 ID
    onMessage    func(Message)       // 消息回调
    onPromptDone func(hermesPromptResult) // 提示完成回调
    acceptNotification func(string) bool  // 通知过滤器
    pendingTools map[string]*pendingToolCall // 待处理的工具调用
}
```

## 完整工作流程

### 阶段 1: 进程启动

```go
// 1. 构建命令
hermesArgs := append([]string{"acp"}, filterCustomArgs(...)...)
cmd := exec.CommandContext(runCtx, execPath, hermesArgs...)

// 2. 设置环境变量
env = append(env, "HERMES_YOLO_MODE=1")  // 自动批准工具权限
cmd.Env = buildEnv(b.cfg.Env)

// 3. 创建管道
stdout, _ := cmd.StdoutPipe()  // 读取 Agent 输出
stdin, _ := cmd.StdinPipe()    // 发送命令到 Agent
stderr, _ := cmd.StderrPipe()  // 错误日志

// 4. 启动进程
cmd.Start()
```

### 阶段 2: 初始化握手 (initialize)

Multica 发送 `initialize` 请求建立协议连接：

**请求：**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "method": "initialize",
  "params": {
    "protocolVersion": 1,
    "clientInfo": {
      "name": "multica-agent-sdk",
      "version": "0.2.0"
    },
    "clientCapabilities": {}
  }
}
```

**响应：**
```json
{
  "jsonrpc": "2.0",
  "id": 1,
  "result": {
    "protocolVersion": 1,
    "serverInfo": {
      "name": "hermes",
      "version": "1.0.0"
    },
    "capabilities": {
      "loadSession": true,
      "models": ["claude-3-5-sonnet-20241022"]
    }
  }
}
```

### 阶段 3: 会话创建/恢复

#### 3.1 创建新会话 (session/new)

**请求：**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "session/new",
  "params": {
    "cwd": "/path/to/project",
    "model": "claude-3-5-sonnet-20241022"
  }
}
```

**响应：**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "result": {
    "sessionId": "sess_abc123",
    "model": "claude-3-5-sonnet-20241022"
  }
}
```

#### 3.2 恢复已有会话 (session/load)

**请求：**
```json
{
  "jsonrpc": "2.0",
  "id": 2,
  "method": "session/load",
  "params": {
    "sessionId": "sess_abc123",
    "cwd": "/path/to/project"
  }
}
```

### 阶段 4: 发送提示 (session/prompt)

**请求：**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "method": "session/prompt",
  "params": {
    "sessionId": "sess_abc123",
    "prompt": [
      {
        "type": "text",
        "text": "修复 bug：登录页面无法提交"
      }
    ]
  }
}
```

**响应：**
```json
{
  "jsonrpc": "2.0",
  "id": 3,
  "result": {
    "stopReason": "end_turn",
    "usage": {
      "inputTokens": 1234,
      "outputTokens": 567,
      "cachedReadTokens": 890
    }
  }
}
```

### 阶段 5: 流式更新 (session/update 通知)

Agent 在执行过程中通过 `session/update` 通知发送实时更新（**无需响应**）：

#### 5.1 Agent 思考内容

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "sessionId": "sess_abc123",
    "update": {
      "type": "agent_thought_chunk",
      "content": [
        {
          "type": "text",
          "text": "我需要先查看登录表单的代码..."
        }
      ]
    }
  }
}
```

#### 5.2 Agent 消息内容

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "sessionId": "sess_abc123",
    "update": {
      "type": "agent_message_chunk",
      "content": [
        {
          "type": "text",
          "text": "我发现问题在于表单验证逻辑..."
        }
      ]
    }
  }
}
```

#### 5.3 工具调用开始

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "sessionId": "sess_abc123",
    "update": {
      "type": "tool_call",
      "id": "tool_001",
      "name": "read_file",
      "input": {
        "path": "/path/to/login.tsx"
      }
    }
  }
}
```

#### 5.4 工具调用更新 (Kimi 流式参数)

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "sessionId": "sess_abc123",
    "update": {
      "type": "tool_call_update",
      "id": "tool_001",
      "content": [
        {
          "type": "text",
          "text": "{\"path\": \"/path/to/login.tsx\"}"
        }
      ]
    }
  }
}
```

#### 5.5 工具执行结果

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "sessionId": "sess_abc123",
    "update": {
      "type": "tool_result",
      "toolCallId": "tool_001",
      "content": [
        {
          "type": "text",
          "text": "export function LoginForm() { ... }"
        }
      ],
      "isError": false
    }
  }
}
```

#### 5.6 Token 使用统计

```json
{
  "jsonrpc": "2.0",
  "method": "session/update",
  "params": {
    "sessionId": "sess_abc123",
    "update": {
      "type": "usage_update",
      "model": "claude-3-5-sonnet-20241022",
      "inputTokens": 1234,
      "outputTokens": 567,
      "cachedReadTokens": 890
    }
  }
}
```

### 阶段 6: 工具权限自动批准

当 Agent 请求工具权限时（Kimi 会发送此请求），Multica 自动批准：

**Agent → Multica 请求：**
```json
{
  "jsonrpc": "2.0",
  "id": 100,
  "method": "session/request_permission",
  "params": {
    "sessionId": "sess_abc123",
    "action": {
      "type": "tool_use",
      "tool": "bash",
      "input": {
        "command": "npm test"
      }
    }
  }
}
```

**Multica → Agent 响应：**
```json
{
  "jsonrpc": "2.0",
  "id": 100,
  "result": {
    "decision": "approve_for_session"
  }
}
```

> **注意：** `approve_for_session` 表示本会话内后续相同操作自动批准，避免重复请求。

## 消息处理机制

### 1. 请求/响应模式

```go
func (c *hermesClient) request(ctx context.Context, method string, params any) (json.RawMessage, error) {
    // 1. 生成唯一请求 ID
    c.mu.Lock()
    c.nextID++
    id := c.nextID
    ch := make(chan rpcResult, 1)
    c.pending[id] = &pendingRPC{method: method, ch: ch}
    c.mu.Unlock()

    // 2. 构建 JSON-RPC 请求
    req := map[string]any{
        "jsonrpc": "2.0",
        "id":      id,
        "method":  method,
        "params":  params,
    }
    data, _ := json.Marshal(req)
    data = append(data, '\n')

    // 3. 写入 stdin
    c.writeLine(data)

    // 4. 等待响应
    select {
    case res := <-ch:
        if res.err != nil {
            return nil, res.err
        }
        return res.result, nil
    case <-ctx.Done():
        return nil, ctx.Err()
    }
}
```

### 2. 通知处理

```go
func (c *hermesClient) handleNotification(raw map[string]json.RawMessage) {
    var method string
    json.Unmarshal(raw["method"], &method)

    if method != "session/update" && method != "session/notification" {
        return
    }

    var params struct {
        SessionID string          `json:"sessionId"`
        Update    json.RawMessage `json:"update"`
    }
    json.Unmarshal(raw["params"], &params)

    var update struct {
        Type string `json:"type"`
    }
    json.Unmarshal(params.Update, &update)

    // 根据更新类型分发处理
    switch update.Type {
    case "agent_message_chunk":
        c.handleAgentMessage(params.Update)
    case "agent_thought_chunk":
        c.handleAgentThought(params.Update)
    case "tool_call":
        c.handleToolCallStart(params.Update)
    case "tool_call_update":
        c.handleToolCallUpdate(params.Update)
    case "tool_result":
        c.handleToolResult(params.Update)
    case "usage_update":
        c.handleUsageUpdate(params.Update)
    }
}
```

### 3. 并发安全

- **writeMu**: 序列化 stdin 写入，防止多个 goroutine 同时写入导致 JSON 帧交错
- **mu**: 保护 `pending` map 和 `nextID` 的并发访问
- **usageMu**: 保护 token 使用统计的累加操作

## 错误处理

### 1. 提供商错误嗅探

Multica 监听 stderr 输出，捕获 LLM 提供商的错误信息：

```go
providerErr := newACPProviderErrorSniffer("hermes")
stderr, _ := cmd.StderrPipe()
stderrSink := io.MultiWriter(newLogWriter(logger, "[hermes:stderr] "), providerErr)
go io.Copy(stderrSink, stderr)
```

**捕获的错误类型：**
- API 密钥过期
- 速率限制 (429)
- 上游服务错误 (5xx)
- Token 配额耗尽

### 2. 超时处理

```go
timeout := opts.Timeout
if timeout == 0 {
    timeout = 20 * time.Minute
}
runCtx, cancel := context.WithTimeout(ctx, timeout)

_, err := c.request(runCtx, "session/prompt", params)
if err != nil {
    if runCtx.Err() == context.DeadlineExceeded {
        finalStatus = "timeout"
        finalError = fmt.Sprintf("hermes timed out after %s", timeout)
    }
}
```

### 3. 会话恢复失败处理

```go
if opts.ResumeSessionID != "" {
    result, err := c.request(runCtx, "session/load", params)
    if err != nil {
        // 会话加载失败，回退到创建新会话
        logger.Warn("session/load failed, falling back to session/new", "error", err)
        result, err = c.request(runCtx, "session/new", params)
    }
}
```

## 特殊处理

### 1. 历史重放过滤

恢复会话时，Agent 会重新发送历史消息。Multica 使用 `streamingCurrentTurn` 标志过滤历史内容：

```go
var streamingCurrentTurn atomic.Bool

acceptNotification: func(updateType string) bool {
    // 只接受当前轮次的更新
    return streamingCurrentTurn.Load()
}

// 发送 session/prompt 后才开始接受通知
streamingCurrentTurn.Store(true)
c.request(runCtx, "session/prompt", params)
```

### 2. 工具名称规范化

不同 Agent 的工具名称格式不同，Multica 统一规范化：

```go
// Hermes: "Bash" → "bash"
// Kimi: "bash_20241022" → "bash"
func hermesToolNameFromTitle(title string) string {
    lower := strings.ToLower(title)
    // 移除版本后缀
    if idx := strings.Index(lower, "_"); idx > 0 {
        return lower[:idx]
    }
    return lower
}
```

### 3. 工具参数累积 (Kimi)

Kimi 通过多个 `tool_call_update` 流式发送工具参数，Multica 累积完整参数：

```go
type pendingToolCall struct {
    id       string
    name     string
    argsText string  // 累积的参数文本
    emitted  bool    // 是否已发送 MessageToolUse
}

func (c *hermesClient) handleToolCallUpdate(data json.RawMessage) {
    // 累积参数
    pending.argsText += textContent

    // 参数完整后解析并发送
    if isComplete(pending.argsText) {
        var input map[string]any
        json.Unmarshal([]byte(pending.argsText), &input)
        c.onMessage(Message{
            Type:  MessageToolUse,
            Tool:  pending.name,
            Input: input,
        })
        pending.emitted = true
    }
}
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
    scanner := bufio.NewScanner(stdout)
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

## 代码复用

Hermes、Kimi、Kiro 三个 Agent 共享同一个 `hermesClient` 实现：

```go
// hermes.go
type hermesBackend struct {
    cfg Config
}

// kimi.go
type kimiBackend struct {
    cfg Config
}

// kiro.go
type kiroBackend struct {
    cfg Config
}

// 三者都使用相同的 hermesClient 进行 ACP 通信
// 只在启动命令和工具名称规范化上有差异
```

## 总结

Multica 的 ACP 集成展示了一个完整的 JSON-RPC 2.0 客户端实现：

1. **标准化通信**: 通过 stdin/stdout 管道进行 JSON-RPC 2.0 通信
2. **异步处理**: 请求/响应和通知分离，支持流式更新
3. **并发安全**: 多 goroutine 协作，使用互斥锁保护共享状态
4. **错误恢复**: 会话恢复、超时处理、提供商错误捕获
5. **代码复用**: 单一 ACP 客户端实现支持多个 Agent

这种架构使得 Multica 可以轻松集成任何支持 ACP 协议的 Agent，只需实现特定的启动逻辑和工具名称映射即可。

## 相关文档

- [[acp-protocol]] - ACP 协议规范
- [[a2a-protocol]] - A2A 协议对比
- [[mcp-protocol]] - MCP 协议对比
