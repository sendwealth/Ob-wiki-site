---
title: A2A × Multica 发现机制方案设计
created: 2026-05-14
updated: 2026-05-14
type: concept
tags: [a2a, multica, discovery, runtime, architecture]
status: draft
---

# A2A × Multica 发现机制方案设计

> 用 A2A Agent Card 协议替代 `exec.LookPath` CLI 探测，让任何 A2A 兼容 Agent（不限于 CLI 形态）都能被 Multica 发现、注册、调度。
> 关联 [[a2a-protocol]]、[[multica]]、[[multica-runtime-discovery]]、[[adk-multica-http-runtime]]

## 一、问题陈述

### 1.1 现状

Multica Daemon 通过 `exec.LookPath` 在 `$PATH` 上探测 CLI 二进制：

```go
claudePath := envOrDefault("MULTICA_CLAUDE_PATH", "claude")
if _, err := exec.LookPath(claudePath); err == nil {
    agents["claude"] = AgentEntry{Path: claudePath}
}
```

**局限**：
- 只能发现本地安装的 CLI 工具
- Agent 必须是可执行二进制（Python 包、远程服务不适用）
- 每个 provider 需要硬编码探测逻辑
- 无法获取 Agent 的能力描述（只有 CLI 路径）
- 无法发现跨网络的 Agent

### 1.2 目标

用 A2A Agent Card 替代 CLI 探测，实现：

| 能力 | 当前（CLI） | 目标（A2A） |
|------|-----------|------------|
| 发现范围 | 本地 $PATH | 本地 + 网络 + 注册中心 |
| Agent 形态 | CLI 二进制 | 任意（HTTP/gRPC/进程） |
| 能力描述 | 无（仅 provider 名） | Agent Card（技能、模型、认证） |
| 扩展性 | 硬编码每种 provider | 声明式，零代码新增 Agent |
| 任务协议 | 环境变量 + stdout | A2A SendMessage / Task |

## 二、核心概念映射

### 2.1 A2A ↔ Multica 术语对照

| A2A 概念 | Multica 对应 | 映射方式 |
|----------|-------------|---------|
| Agent Card | Runtime 注册信息 | Card → register payload |
| Skill | Agent Skill | skill.id → skill.name |
| SendMessage | task dispatch | prompt → Message.parts |
| Task (COMPLETED) | task:completed | status 映射 |
| Task (FAILED) | task:failed | status 映射 |
| Task (INPUT_REQUIRED) | task:progress (human-in-loop) | 中断态 → 进度上报 |
| Artifact | task output | artifact.parts → output |
| Part (TextPart) | task message | text → message content |
| Part (DataPart) | task usage | data → usage report |
| Context | workspace + session | contextId = workspaceID |
| streaming (SSE) | task:message 实时流 | SSE event → WS message |
| securitySchemes | runtime credentials | OIDC → daemon token |

### 2.2 Task 状态映射

```
A2A Task State              Multica Task Status     Action
─────────────────────────────────────────────────────────────
SUBMITTED                →  dispatched              ReportProgress("starting")
WORKING                  →  running                 ReportProgress("working")
INPUT_REQUIRED           →  running                 ReportProgress("waiting for input")
AUTH_REQUIRED            →  running                 ReportProgress("auth required")
COMPLETED                →  completed               CompleteTask(output)
FAILED                   →  failed                  FailTask(error)
CANCELED                 →  cancelled               (discard result)
REJECTED                 →  failed                  FailTask("rejected")
```

## 三、发现架构

### 3.1 总体架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Multica Daemon                          │
│                                                                 │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐ │
│  │ CLI Scanner  │  │ A2A Scanner  │  │  A2A Task Bridge     │ │
│  │ (现有，保留)  │  │  (新增)      │  │  (新增)              │ │
│  │              │  │              │  │                      │ │
│  │ exec.LookPath│  │ Agent Card   │  │ Multica Task        │ │
│  │ × 11 prov.   │  │ Discovery    │  │   ↓                 │ │
│  │              │  │              │  │ A2A SendMessage      │ │
│  └──────┬───────┘  └──────┬───────┘  │   ↓                 │ │
│         │                 │          │ A2A Task Status      │ │
│         │                 │          │   ↓                  │ │
│         │                 │          │ Multica Callback     │ │
│         │                 │          └──────────────────────┘ │
│         ▼                 ▼                                   │
│  ┌──────────────────────────────┐                             │
│  │    Unified Agent Registry    │                             │
│  │  map[string]AgentEntry       │                             │
│  │  + map[string]AgentCard      │                             │
│  └──────────────┬───────────────┘                             │
│                 │                                              │
│                 ▼                                              │
│  ┌──────────────────────────────┐                             │
│  │    registerRuntimesForWS     │  → Server (不变)           │
│  └──────────────────────────────┘                             │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 三种发现模式

#### Mode 1：配置文件声明（主要方式）

```yaml
# ~/.multica/a2a-agents.yaml
agents:
  - name: "adk-code-reviewer"
    url: "http://127.0.0.1:8900"
    # Daemon 启动时 GET /.well-known/agent-card.json 获取 Agent Card

  - name: "adk-docs-writer"
    url: "http://127.0.0.1:8901"

  - name: "remote-research-agent"
    url: "https://agents.example.com/research"
    auth:
      scheme: "openid-connect"
      token_env: "RESEARCH_AGENT_TOKEN"

  - name: "local-llama-agent"
    url: "http://192.168.1.100:8080"
```

#### Mode 2：本地服务扫描（自动发现）

Daemon 扫描本地已知端口段，检测是否有 A2A Agent Card：

```go
// 扫描 8900-8910 端口段（ADK HTTP Runtime 默认端口范围）
for port := 8900; port <= 8910; port++ {
    url := fmt.Sprintf("http://127.0.0.1:%d/.well-known/agent-card.json", port)
    if card, err := fetchAgentCard(ctx, url); err == nil {
        agents[card.Name] = AgentEntry{
            Path:  fmt.Sprintf("http://127.0.0.1:%d", port),
            Mode:  "a2a",
            Card:  card,
        }
    }
}
```

#### Mode 3：注册中心（企业/多租户）

```yaml
# ~/.multica/a2a-agents.yaml
registry:
  url: "https://agent-registry.example.com/v1/agents"
  poll_interval: "5m"
```

Daemon 定期从注册中心拉取可用的 Agent Card 列表。

### 3.3 发现流程

```
Daemon 启动
    │
    ├── 1. CLI Scanner（现有逻辑，不变）
    │   exec.LookPath × 11 providers
    │   → agents["claude"] = {Path: "claude", Mode: "cli"}
    │   → agents["codex"]  = {Path: "codex", Mode: "cli"}
    │   ...
    │
    ├── 2. A2A Config Scanner（新增）
    │   读取 ~/.multica/a2a-agents.yaml
    │   for each agent:
    │     GET {url}/.well-known/agent-card.json
    │     → agents["adk-code-reviewer"] = {Path: url, Mode: "a2a", Card: card}
    │
    ├── 3. A2A Local Scanner（新增，可选）
    │   扫描 localhost:8900-8910
    │   for each responding port:
    │     GET /.well-known/agent-card.json
    │     → agents[card.Name] = {Path: url, Mode: "a2a", Card: card}
    │
    └── 4. 汇总 → registerRuntimesForWorkspace()
        （与现有逻辑合并，注册到 Server）
```

## 四、数据模型扩展

### 4.1 Go 侧类型扩展

```go
// config.go

type AgentEntry struct {
    Path  string             `json:"path"`   // CLI 路径 或 HTTP URL
    Model string             `json:"model"`  // 模型覆盖
    Mode  string             `json:"mode"`   // "cli" | "a2a"
    Card  *A2AAgentCard      `json:"card"`   // A2A Agent Card（Mode=a2a 时）
    Auth  *A2AAuthConfig     `json:"auth"`   // A2A 认证配置
}

type A2AAuthConfig struct {
    Scheme   string `json:"scheme"`    // "openid-connect" | "api-key" | ""
    TokenEnv string `json:"token_env"` // 环境变量名，存放 auth token
    Header   string `json:"header"`    // "Authorization" | "X-API-Key"
}

// 从 A2A Agent Card 提取的关键信息
type A2AAgentCard struct {
    Name            string              `json:"name"`
    Description     string              `json:"description"`
    Version         string              `json:"version"`
    Provider        *A2AProvider        `json:"provider,omitempty"`
    Capabilities    A2ACapabilities     `json:"capabilities"`
    Skills          []A2ASkill          `json:"skills"`
    SecuritySchemes map[string]any      `json:"securitySchemes,omitempty"`
    Interfaces      []A2AInterface      `json:"supportedInterfaces"`
    // raw card 保留，用于透传
    Raw             json.RawMessage     `json:"-"`
}

type A2AInterface struct {
    URL              string `json:"url"`
    ProtocolBinding  string `json:"protocolBinding"`  // "JSONRPC" | "GRPC" | "HTTP+JSON"
    ProtocolVersion  string `json:"protocolVersion"`  // "1.0"
}

type A2ACapabilities struct {
    Streaming              bool `json:"streaming"`
    PushNotifications      bool `json:"pushNotifications"`
    StateTransitionHistory bool `json:"stateTransitionHistory"`
}

type A2ASkill struct {
    ID          string   `json:"id"`
    Name        string   `json:"name"`
    Description string   `json:"description"`
    Examples    []string `json:"examples,omitempty"`
}

type A2AProvider struct {
    Organization string `json:"organization"`
    URL          string `json:"url"`
}
```

### 4.2 Agent Card → Multica Runtime 注册映射

```go
// http_runtime.go

func cardToRuntimePayload(card *A2AAgentCard, deviceName string) map[string]string {
    displayName := card.Name
    if deviceName != "" {
        displayName = fmt.Sprintf("%s (%s)", displayName, deviceName)
    }
    return map[string]string{
        "name":    displayName,
        "type":    "a2a:" + card.Name,      // provider 前缀标识来源
        "version": card.Version,
        "status":  "online",
    }
}

func cardToAgentSkills(card *A2AAgentCard) []SkillData {
    skills := make([]SkillData, 0, len(card.Skills))
    for _, s := range card.Skills {
        skills = append(skills, SkillData{
            Name:    s.ID,
            Content: fmt.Sprintf("# %s\n%s", s.Name, s.Description),
        })
    }
    return skills
}
```

### 4.3 Multica Agent 配置映射

用户在 Multica UI 中创建 Agent 时，可以从 Agent Card 自动填充：

| Multica 字段 | Agent Card 来源 |
|-------------|----------------|
| `name` | `card.name` |
| `instructions` | `card.description` + 用户自定义 |
| `skills` | `card.skills[].id` → 预置技能列表 |
| `model` | 用户选择（Card 可能列出支持的模型） |
| `max_concurrent_tasks` | 用户配置 |

## 五、任务执行桥接

### 5.1 核心桥接器

```go
// a2a_bridge.go

type A2ABridge struct {
    client  *http.Client
    logger  *slog.Logger
}

// Multica Task → A2A SendMessage 请求
func (b *A2ABridge) dispatchTask(
    ctx context.Context,
    task Task,
    card *A2AAgentCard,
    entry AgentEntry,
) (TaskResult, error) {

    // 1. 选择最优 Interface（优先 JSONRPC，fallback HTTP+JSON）
    iface := b.selectInterface(card)

    // 2. 构建 A2A SendMessage 请求
    a2aReq := b.buildSendMessageRequest(task, entry)

    // 3. 根据能力选择调用模式
    if card.Capabilities.Streaming {
        return b.dispatchStreaming(ctx, iface.URL, a2aReq, task, entry)
    }
    return b.dispatchBlocking(ctx, iface.URL, a2aReq, task, entry)
}
```

### 5.2 Prompt → A2A Message 转换

```go
func (b *A2ABridge) buildSendMessageRequest(task Task, entry AgentEntry) map[string]any {
    prompt := BuildPrompt(task, "a2a")

    // 构建 A2A Message parts
    parts := []map[string]any{
        {"text": prompt},
    }

    // 如果有 Agent 自定义指令，作为额外 context part
    if task.Agent != nil && task.Agent.Instructions != "" {
        parts = append(parts, map[string]any{
            "data": map[string]any{
                "instructions": task.Agent.Instructions,
                "agent_name":   task.Agent.Name,
            },
            "mediaType": "application/json",
        })
    }

    return map[string]any{
        "message": map[string]any{
            "role":  "user",
            "parts": parts,
        },
        "configuration": map[string]any{
            "return_immediately": false,  // 阻塞模式（简化）
        },
    }
}
```

### 5.3 阻塞模式执行

```go
func (b *A2ABridge) dispatchBlocking(
    ctx context.Context,
    baseURL string,
    reqBody map[string]any,
    task Task,
    entry AgentEntry,
) (TaskResult, error) {

    // A2A JSON-RPC 请求
    jsonrpcReq := map[string]any{
        "jsonrpc": "2.0",
        "id":      task.ID,
        "method":  "SendMessage",
        "params":  reqBody,
    }

    body, _ := json.Marshal(jsonrpcReq)
    req, _ := http.NewRequestWithContext(ctx, "POST", baseURL, bytes.NewReader(body))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("A2A-Version", "1.0")
    b.setAuthHeaders(req, entry)

    resp, err := b.client.Do(req)
    if err != nil {
        return TaskResult{}, fmt.Errorf("a2a send message: %w", err)
    }
    defer resp.Body.Close()

    var jsonrpcResp struct {
        Result struct {
            Task *A2ATask `json:"task"`
        } `json:"result"`
        Error *struct {
            Code    int    `json:"code"`
            Message string `json:"message"`
        } `json:"error"`
    }
    if err := json.NewDecoder(resp.Body).Decode(&jsonrpcResp); err != nil {
        return TaskResult{}, fmt.Errorf("decode a2a response: %w", err)
    }
    if jsonrpcResp.Error != nil {
        return TaskResult{}, fmt.Errorf("a2a error %d: %s",
            jsonrpcResp.Error.Code, jsonrpcResp.Error.Message)
    }

    return b.convertTaskResult(jsonrpcResp.Result.Task)
}
```

### 5.4 流式模式执行

```go
func (b *A2ABridge) dispatchStreaming(
    ctx context.Context,
    baseURL string,
    reqBody map[string]any,
    task Task,
    entry AgentEntry,
) (TaskResult, error) {

    jsonrpcReq := map[string]any{
        "jsonrpc": "2.0",
        "id":      task.ID,
        "method":  "SendStreamingMessage",
        "params":  reqBody,
    }

    body, _ := json.Marshal(jsonrpcReq)
    req, _ := http.NewRequestWithContext(ctx, "POST", baseURL, bytes.NewReader(body))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("Accept", "text/event-stream")
    req.Header.Set("A2A-Version", "1.0")
    b.setAuthHeaders(req, entry)

    resp, err := b.client.Do(req)
    if err != nil {
        return TaskResult{}, err
    }
    defer resp.Body.Close()

    var finalResult TaskResult
    scanner := bufio.NewScanner(resp.Body)

    for scanner.Scan() {
        line := scanner.Text()

        // 解析 SSE
        if strings.HasPrefix(line, "data:") {
            var event map[string]any
            json.Unmarshal([]byte(strings.TrimPrefix(line, "data:")), &event)

            switch {
            case event["taskStatusUpdate"] != nil:
                // 上报 Multica 进度
                status := event["taskStatusUpdate"].(map[string]any)
                state := status["state"].(string)
                _ = d.client.ReportProgress(ctx, task.ID,
                    fmt.Sprintf("Agent state: %s", state), 1, 2)

            case event["artifactUpdate"] != nil:
                // 收集输出
                artifact := event["artifactUpdate"].(map[string]any)
                // 累积 artifact parts...
            }
        }

        // 检查 context 取消
        select {
        case <-ctx.Done():
            return TaskResult{}, ctx.Err()
        default:
        }
    }

    return finalResult, nil
}
```

### 5.5 A2A Task → Multica TaskResult 转换

```go
type A2ATask struct {
    ID     string        `json:"id"`
    Status A2ATaskStatus `json:"status"`
    Artifacts []A2AArtifact `json:"artifacts,omitempty"`
    Usage  []A2AUsage    `json:"usage,omitempty"`
}

type A2ATaskStatus struct {
    State string `json:"state"` // COMPLETED, FAILED, etc.
}

func (b *A2ABridge) convertTaskResult(a2aTask *A2ATask) (TaskResult, error) {
    // 收集所有 artifact parts 作为 output
    var outputParts []string
    for _, art := range a2aTask.Artifacts {
        for _, part := range art.Parts {
            if part.Text != "" {
                outputParts = append(outputParts, part.Text)
            }
        }
    }

    result := TaskResult{
        Status:  "completed",
        Comment: strings.Join(outputParts, "\n"),
    }

    // 状态映射
    switch a2aTask.Status.State {
    case "COMPLETED":
        result.Status = "completed"
    case "FAILED":
        result.Status = "failed"
    case "CANCELED":
        result.Status = "cancelled"
    case "REJECTED":
        result.Status = "failed"
        result.FailureReason = "agent_rejected"
    case "INPUT_REQUIRED":
        // 中断态：Agent 需要输入，视为 blocked
        result.Status = "blocked"
    default:
        result.Status = "failed"
        result.FailureReason = "unexpected_state:" + a2aTask.Status.State
    }

    // Usage 转换
    for _, u := range a2aTask.Usage {
        result.Usage = append(result.Usage, TaskUsageEntry{
            Provider:        "a2a",
            Model:           u.Model,
            InputTokens:     u.InputTokens,
            OutputTokens:    u.OutputTokens,
            CacheReadTokens: u.CacheReadTokens,
        })
    }

    return result, nil
}
```

## 六、runTask 路由

### 6.1 入口修改

```go
// daemon.go

func (d *Daemon) runTask(ctx context.Context, task Task, provider string,
    slot int, taskLog *slog.Logger) (TaskResult, error) {

    entry, ok := d.cfg.Agents[provider]
    if !ok {
        return TaskResult{}, fmt.Errorf("no agent for %q", provider)
    }

    switch entry.Mode {
    case "a2a":
        return d.a2aBridge.dispatchTask(ctx, task, entry.Card, entry)
    case "http":
        return d.runHTTPTask(ctx, task, entry, slot, taskLog)
    default: // "cli"
        return d.runCLITask(ctx, task, entry, provider, slot, taskLog)
    }
}
```

### 6.2 A2A 模式不需要 execenv

关键区别：A2A 模式下，Daemon **不创建本地执行环境**。Agent Card 描述的 Agent 可能是远程服务，环境由 Agent 自身管理。

```go
// A2A 模式跳过的步骤：
// ❌ execenv.Prepare()       — 不创建本地 workdir
// ❌ execenv.InjectRuntimeConfig() — 不注入 meta skill
// ❌ exec.CommandContext()    — 不 fork 子进程
// ❌ stdout 解析             — 不解析 CLI 输出

// A2A 模式替代为：
// ✅ A2ABridge.dispatchTask() — 发送 A2A 请求
// ✅ SSE 流式接收             — 解析 A2A 事件
// ✅ TaskResult 转换          — 映射到 Multica 结果
```

但 repo checkout 信息仍需传递给 Agent：

```go
func (b *A2ABridge) buildSendMessageRequest(task Task, entry AgentEntry) map[string]any {
    // 将 repos 信息作为 DataPart 传入
    if len(task.Repos) > 0 {
        repoData := make([]map[string]string, 0, len(task.Repos))
        for _, r := range task.Repos {
            repoData = append(repoData, map[string]string{"url": r.URL})
        }
        parts = append(parts, map[string]any{
            "data":      map[string]any{"repos": repoData},
            "mediaType": "application/json",
        })
    }
    // ...
}
```

## 七、健康探测与心跳

### 7.1 A2A 健康探测

A2A 协议没有原生心跳，但 Agent Card 端点可用作健康探测：

```go
// a2a_health.go

func (d *Daemon) probeA2ARuntimes(ctx context.Context) {
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            for name, entry := range d.cfg.Agents {
                if entry.Mode != "a2a" || entry.Card == nil {
                    continue
                }

                // 获取 Agent Card 作为健康检查
                cardURL := strings.TrimRight(entry.Path, "/") +
                    "/.well-known/agent-card.json"

                req, _ := http.NewRequestWithContext(ctx, "GET", cardURL, nil)
                resp, err := http.DefaultClient.Do(req)

                if err != nil || resp.StatusCode != 200 {
                    d.logger.Warn("A2A agent unhealthy",
                        "name", name, "error", err)
                    // 标记为 offline，触发服务端心跳失败流程
                    continue
                }
                resp.Body.Close()

                // 可选：检查 Card 版本是否变更，触发重新注册
                // ...
            }
        }
    }
}
```

### 7.2 服务端心跳保持不变

Daemon ↔ Server 的心跳协议完全不变（WS/HTTP），对 Server 来说 A2A runtime 与 CLI runtime 无差异。

```
Daemon ── heartbeat ──► Server    （现有协议，不变）
  │                        │
  └── probe A2A agent ──► Agent Card URL  （新增，独立于服务端心跳）
```

## 八、认证传递

### 8.1 场景分析

```
                    ┌─────────────┐
  Multica Server    │             │
       │            │  Daemon     │
       │ auth token │             │
       ▼            │  ┌────────┐│
  Daemon ──────────►│  │A2A     ││
       uses token   │  │Bridge  ││
       for Server   │  └───┬────┘│
                    │      │     │
                    │      │ A2A │ ← 需要 Agent 自身的认证
                    │      ▼     │
                    │  A2A Agent │
                    └─────────────┘
```

三层认证：
1. **Daemon ↔ Server**：现有 Multica token（不变）
2. **Daemon ↔ A2A Agent**：Agent Card 中声明的 securitySchemes
3. **A2A Agent ↔ LLM**：Agent 自身管理（Daemon 不涉及）

### 8.2 配置方式

```yaml
# ~/.multica/a2a-agents.yaml
agents:
  - name: "adk-agent"
    url: "http://127.0.0.1:8900"
    # 无需认证（本地 Agent）

  - name: "remote-agent"
    url: "https://agents.example.com/research"
    auth:
      scheme: "openid-connect"
      token_env: "RESEARCH_AGENT_TOKEN"  # 从环境变量读取 token
```

### 8.3 请求注入

```go
func (b *A2ABridge) setAuthHeaders(req *http.Request, entry AgentEntry) {
    if entry.Auth == nil || entry.Auth.TokenEnv == "" {
        return
    }
    token := os.Getenv(entry.Auth.TokenEnv)
    if token == "" {
        return
    }
    header := entry.Auth.Header
    if header == "" {
        header = "Authorization"
    }
    if strings.HasPrefix(token, "Bearer ") || strings.HasPrefix(token, "Basic ") {
        req.Header.Set(header, token)
    } else {
        req.Header.Set(header, "Bearer "+token)
    }
}
```

## 九、文件变更清单

### 9.1 Multica（Go）变更

| 文件 | 类型 | 说明 |
|------|------|------|
| `internal/daemon/config.go` | 修改 | 新增 A2A config scanner、扩展 `AgentEntry` |
| `internal/daemon/types.go` | 修改 | 新增 `A2AAgentCard`、`A2AAuthConfig` 等类型 |
| `internal/daemon/a2a_bridge.go` | **新增** | A2A Task Bridge（dispatch、streaming、convert） |
| `internal/daemon/a2a_health.go` | **新增** | A2A Agent Card 健康探测 |
| `internal/daemon/daemon.go` | 修改 | `runTask` 路由到 `a2a` 模式 |
| `cmd/multica/cmd_daemon.go` | 修改 | 启动时触发 A2A scanner |

### 9.2 新增配置文件

| 文件 | 说明 |
|------|------|
| `~/.multica/a2a-agents.yaml` | A2A Agent 声明式配置 |

### 9.3 不变的部分

- Multica Server API（`/api/daemon/*` 全部不变）
- Daemon ↔ Server 心跳协议不变
- CLI Scanner 完全保留，与 A2A Scanner 并行
- 前端不变
- 任务 claim/start/complete/fail 回调不变

## 十、与之前方案的关系

```
方案演进：

Path 1 (CLI wrapper)          Path 2 (HTTP Bridge)          Path 3 (A2A Discovery)
─────────────────          ─────────────────           ──────────────────
最简单，adk CLI             自定义 HTTP 协议              标准化 A2A 协议
侵入 ADK                    自定义端点                   标准端点
无能力描述                  自定义格式                   Agent Card 声明能力
仅限 ADK                    仅限 ADK                    任何 A2A 兼容 Agent
Hardcoded                   自定义                      标准
─────────────────────────────────────────────────────────────────────────
复杂度: 低                    中                          中高
通用性: 低                    中                          高
长期价值: 低                  中                          高
```

本方案（A2A Discovery）取代了之前的 [[adk-multica-http-runtime]] 中的自定义 HTTP 协议设计，改用标准化的 A2A 协议。ADK Agent 只需通过 `to_a2a()` 暴露为 A2A 服务，即可被 Multica 发现。

## 十一、实施计划

### Phase 1：A2A Scanner + 阻塞模式（2-3 天）

- [ ] `types.go`：新增 A2A 相关类型
- [ ] `config.go`：A2A config scanner（读取 YAML + fetch Agent Card）
- [ ] `a2a_bridge.go`：阻塞模式 dispatch + TaskResult 转换
- [ ] `daemon.go`：runTask 路由到 a2a 模式
- [ ] 集成测试：ADK Agent → A2A 暴露 → Daemon 发现 → 任务调度

### Phase 2：流式 + 健康 + 取消（1-2 天）

- [ ] `a2a_bridge.go`：SSE 流式模式（实时进度上报）
- [ ] `a2a_health.go`：Agent Card 健康探测
- [ ] 取消传播（context cancellation → 关闭 SSE 连接）
- [ ] INPUT_REQUIRED 处理（上报 progress，等待用户输入）

### Phase 3：认证 + 多 Interface + 生产化（2-3 天）

- [ ] `a2a_bridge.go`：Interface 选择（JSONRPC / gRPC / HTTP+JSON）
- [ ] 认证传递（securitySchemes → auth header 注入）
- [ ] Local Scanner（端口扫描自动发现）
- [ ] Agent Card 版本变更检测（触发重新注册）
- [ ] 优雅关闭 + 错误恢复

## 十二、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| A2A Agent 不支持阻塞模式 | 低 | 中 | 降级到 return_immediately + 轮询 GetTask |
| 流式 SSE 连接中断 | 中 | 中 | 回退到 GetTask 轮询，设置合理超时 |
| 远程 Agent 延迟高 | 中 | 低 | 本地 Agent 优先，远程仅用于特殊能力 |
| Agent Card 格式变更 | 低 | 低 | 保留 raw JSON，仅提取必要字段 |
| 与 CLI runtime 行为不一致 | 低 | 中 | 统一的 runTask 接口，共享 result 上报逻辑 |

## 相关链接

- [[a2a-protocol]] — A2A 协议完整技术参考
- [[multica]] — Multica 平台架构
- [[multica-runtime-discovery]] — Multica Runtime 发现机制（现有 CLI 方案）
- [[adk-python]] — Google ADK 架构（A2A `to_a2a()` 暴露）
- [[adk-multica-http-runtime]] — 之前的自定义 HTTP 方案（被本方案取代）
- A2A Spec: https://a2a-protocol.org/
- A2A GitHub: https://github.com/google/A2A
