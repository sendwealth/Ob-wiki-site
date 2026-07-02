---
title: ADK Agent ↔ Multica HTTP Runtime 集成方案
created: 2026-05-14
updated: 2026-05-14
type: concept
tags: [adk, multica, runtime, a2a, http, architecture]
status: draft
---

# ADK Agent ↔ Multica HTTP Runtime 集成方案

> 将 ADK Agent 以 HTTP 服务形态接入 Multica runtime 体系，无需 CLI 包装。
> 关联 [[adk-python]]、[[multica]]、[[multica-runtime-discovery]]

## 一、现状分析

### 1.1 Multica Runtime 模型

```
┌──────────────┐    exec.LookPath     ┌──────────────┐
│  Multica     │ ──────────────────►  │  Agent CLI   │
│  Daemon      │    发现 CLI 二进制    │  (claude等)   │
│  (Go 进程)   │                      │              │
│              │    注册到服务端        └──────┬───────┘
│              │ ──────────────────►         │
│              │    POST /api/daemon/register│ shell out
│              │                             │
│              │    心跳保活                   ▼
│              │ ◄──────────────────► 执行任务
│              │    WS / HTTP heartbeat  (fork+exec)
│              │
│              │    轮询领取任务
│              │ ──────────────────►
│              │    POST /runtimes/{id}/tasks/claim
└──────────────┘
```

**核心约束**：
- Daemon 通过 `exec.LookPath` 探测 CLI 二进制，注册到服务端
- 任务执行：`fork + exec` 子进程，通过**环境变量**传递上下文
- 心跳：WS（首选）或 HTTP（fallback）
- 生命周期：`claim → start → progress → complete/fail`
- 结果上报：`output`（文本）、`branch_name`（git）、`session_id`（会话恢复）

### 1.2 ADK Agent 模型

```
┌──────────────┐    Runner.run_async()    ┌──────────────┐
│  FastAPI     │ ─────────────────────►   │  ADK Agent   │
│  Server      │     异步执行              │  (Python     │
│  (uvicorn)   │                          │   对象)      │
│              │    A2A 协议暴露            │              │
│              │ ◄──────────────────────  └──────────────┘
│              │    to_a2a(agent)
│              │
│              │    HTTP API
│              │ ◄──────────────────► 外部调用者
└──────────────┘
```

**核心能力**：
- `Runner` 在进程内驱动 Agent 执行
- `to_a2a(agent)` 暴露为 A2A 服务（Agent Card + Task 协议）
- `adk api_server` 提供 HTTP API
- 会话/记忆/工具 全部在进程内管理

### 1.3 差距分析

| 维度 | Multica 期望 | ADK 提供 | 差距 |
|------|-------------|---------|------|
| 发现方式 | CLI 二进制 (`exec.LookPath`) | Python 包 | 无 CLI 入口 |
| 任务接收 | 环境变量 + stdin | HTTP API / A2A Task | 协议不匹配 |
| 执行方式 | fork+exec 子进程 | 进程内 async | 模型不匹配 |
| 结果返回 | stdout + 退出码 | Event stream | 格式不匹配 |
| 生命周期 | Daemon 管理 | 自管理 | 管辖权不匹配 |

## 二、设计目标

1. **零侵入 ADK**：不修改 `google-adk` 包源码
2. **最小改 Multica**：在 Daemon 侧扩展，不改服务端核心 API
3. **协议标准化**：基于 A2A 协议，为未来接入更多 Agent 框架铺路
4. **对等 CLI runtime**：HTTP runtime 与 CLI runtime 拥有同等的任务生命周期管理能力

## 三、架构设计

### 3.1 总体架构

```
                    Multica 现有体系
┌─────────────────────────────────────────────────────────┐
│                                                         │
│  ┌─────────┐   ┌──────────┐   ┌──────────────────────┐ │
│  │ Multica │   │  Daemon  │   │  Server (Go)         │ │
│  │ CLI     │   │  (Go)    │   │  - /api/daemon/*     │ │
│  │         │   │          │   │  - task lifecycle    │ │
│  └─────────┘   └────┬─────┘   └──────────────────────┘ │
│                     │                                   │
│     ┌───────────────┼───────────────┐                   │
│     │               │               │                   │
│     ▼ CLI           ▼ HTTP (新增)    │                   │
│ ┌─────────┐   ┌──────────────┐      │                   │
│ │ claude  │   │ ADK Agent    │      │                   │
│ │ codex   │   │ HTTP Runtime │      │                   │
│ │ copilot │   │ (本方案)      │      │                   │
│ │ ...     │   └──────┬───────┘      │                   │
│ └─────────┘          │              │                   │
│                      │ A2A / HTTP   │                   │
│              ┌───────▼────────┐     │                   │
│              │ ADK Agent      │     │                   │
│              │ Service Pool   │     │                   │
│              │ ┌────────────┐ │     │                   │
│              │ │ Agent A    │ │     │                   │
│              │ │ (gemini)   │ │     │                   │
│              │ ├────────────┤ │     │                   │
│              │ │ Agent B    │ │     │                   │
│              │ │ (claude)   │ │     │                   │
│              │ └────────────┘ │     │                   │
│              └────────────────┘     │                   │
└─────────────────────────────────────────────────────────┘
```

### 3.2 核心组件

#### 组件 1：ADK Agent HTTP Runtime（Python 侧）

一个独立的 Python 服务进程，充当 ADK Agent 与 Multica Daemon 之间的桥梁。

```
adk-http-runtime/
├── __main__.py           # 入口：启动 HTTP 服务
├── runtime_server.py     # FastAPI 服务，暴露 Daemon 协议
├── agent_manager.py      # Agent 生命周期管理
├── task_executor.py      # 任务执行引擎
├── config.py             # 配置（agent 定义、端口等）
└── multica_client.py     # 与 Multica Daemon 通信的客户端
```

#### 组件 2：Multica Daemon HTTP Runtime 扩展（Go 侧）

在 Daemon 中新增 HTTP runtime 模式，与现有 CLI runtime 并行。

```
daemon/
├── config.go              # 新增 HTTP agent 探测
├── http_runtime.go        # HTTP runtime 执行器（新增）
├── http_runtime_test.go
└── daemon.go              # runTask 路由分发修改
```

### 3.3 交互序列

```
ADK HTTP Runtime                Multica Daemon              Multica Server
     │                               │                          │
     │  ① 启动，暴露 /health          │                          │
     │◄──────────────────────────────┤                          │
     │  ② Daemon 探测 HTTP agent     │                          │
     │  GET /health                  │                          │
     │──────────────────────────────►│                          │
     │  ③ 获取 Agent Card            │                          │
     │  GET /agent/card              │                          │
     │──────────────────────────────►│                          │
     │                               │  ④ 注册 runtime          │
     │                               │  POST /api/daemon/register
     │                               │─────────────────────────►│
     │                               │  ⑤ 返回 runtime_id       │
     │                               │◄─────────────────────────│
     │                               │                          │
     │                               │  ⑥ 心跳保活               │
     │                               │◄─── WS heartbeat ───────►│
     │                               │                          │
     │                               │  ⑦ 领取任务               │
     │                               │  POST /runtimes/{id}/tasks/claim
     │                               │─────────────────────────►│
     │                               │  ⑧ 返回 Task              │
     │                               │◄─────────────────────────│
     │                               │                          │
     │  ⑨ 分发任务（HTTP）            │                          │
     │  POST /tasks/execute          │                          │
     │◄──────────────────────────────│                          │
     │  ⑩ 返回 Event Stream          │                          │
     │──────────────────────────────►│                          │
     │                               │  ⑪ 上报结果               │
     │                               │  POST /tasks/{id}/complete
     │                               │─────────────────────────►│
```

## 四、详细设计

### 4.1 发现与注册

#### 4.1.1 ADK 侧：Agent Card 暴露

ADK HTTP Runtime 启动后暴露标准化端点：

```python
# runtime_server.py
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class AgentCard(BaseModel):
    name: str
    version: str
    provider: str               # "adk"
    models: list[str]           # 支持的模型列表
    capabilities: list[str]     # ["text", "code", "tools"]
    tools: list[str]            # 可用工具列表
    max_concurrent_tasks: int   # 最大并发数

@app.get("/health")
async def health():
    return {"status": "ok", "uptime": ...}

@app.get("/agent/card")
async def agent_card():
    return AgentCard(
        name="adk-agent",
        version=__version__,
        provider="adk",
        models=["gemini-2.5-flash", "gemini-2.5-pro", "claude-sonnet-4-6"],
        capabilities=["text", "code", "tools"],
        tools=agent_manager.available_tools(),
        max_concurrent_tasks=4,
    )
```

#### 4.1.2 Multica 侧：HTTP Agent 探测

在 `config.go` 的 `DefaultConfig()` 中新增 HTTP 探测：

```go
// config.go — 在 CLI 探测之后新增

// 探测本地 ADK HTTP Runtime
adkHTTPURL := envOrDefault("MULTICA_ADK_HTTP_URL", "http://127.0.0.1:8900")
if resp, err := http.Get(adkHTTPURL + "/health"); err == nil {
    resp.Body.Close()
    if resp.StatusCode == 200 {
        agents["adk"] = AgentEntry{
            Path:  adkHTTPURL,     // URL 替代 CLI 路径
            Model: strings.TrimSpace(os.Getenv("MULTICA_ADK_MODEL")),
            Mode:  "http",         // 新增字段，标识运行模式
        }
    }
}
```

`AgentEntry` 扩展：

```go
type AgentEntry struct {
    Path  string       // CLI 路径 或 HTTP URL
    Model string       // 模型覆盖
    Mode  string       // "cli"（默认）或 "http"
}
```

#### 4.1.3 版本检测

```go
// 对 HTTP runtime，通过 /agent/card 获取版本
func DetectVersionHTTP(ctx context.Context, url string) (string, error) {
    req, _ := http.NewRequestWithContext(ctx, "GET", url+"/agent/card", nil)
    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return "", err
    }
    defer resp.Body.Close()
    var card struct {
        Version string `json:"version"`
    }
    json.NewDecoder(resp.Body).Decode(&card)
    return card.Version, nil
}
```

在 `daemon.go` 的 `registerRuntimesForWorkspace` 中路由：

```go
for name, entry := range d.cfg.Agents {
    var version string
    var err error

    switch entry.Mode {
    case "http":
        version, err = DetectVersionHTTP(ctx, entry.Path)
    default:
        version, err = detectAgentVersion(ctx, entry.Path)
    }

    if err != nil {
        d.logger.Warn("skip registering runtime", "name", name, "error", err)
        continue
    }
    // ... 后续注册逻辑不变
}
```

### 4.2 任务执行

#### 4.2.1 Daemon 侧：runTask 路由

修改 `daemon.go` 的 `runTask` 函数，根据 `entry.Mode` 选择执行路径：

```go
func (d *Daemon) runTask(ctx context.Context, task Task, provider string,
    slot int, taskLog *slog.Logger) (TaskResult, error) {

    entry, ok := d.cfg.Agents[provider]
    if !ok {
        return TaskResult{}, fmt.Errorf("no agent for %q", provider)
    }

    switch entry.Mode {
    case "http":
        return d.runHTTPTask(ctx, task, entry, slot, taskLog)
    default:
        return d.runCLITask(ctx, task, entry, provider, slot, taskLog)
    }
}
```

现有 CLI 执行逻辑提取到 `runCLITask`，新增 `runHTTPTask`。

#### 4.2.2 Daemon 侧：runHTTPTask

```go
// http_runtime.go

type TaskExecuteRequest struct {
    TaskID       string            `json:"task_id"`
    Prompt       string            `json:"prompt"`
    AgentName    string            `json:"agent_name"`
    Instructions string            `json:"instructions"`
    Skills       []SkillData       `json:"skills"`
    Repos        []RepoData        `json:"repos"`
    Env          map[string]string `json:"env"`
    Model        string            `json:"model,omitempty"`
}

type TaskExecuteResponse struct {
    Status     string           `json:"status"`
    Output     string           `json:"output"`
    BranchName string           `json:"branch_name,omitempty"`
    SessionID  string           `json:"session_id,omitempty"`
    Usage      []TaskUsageEntry `json:"usage,omitempty"`
}

func (d *Daemon) runHTTPTask(ctx context.Context, task Task,
    entry AgentEntry, slot int, taskLog *slog.Logger) (TaskResult, error) {

    prompt := BuildPrompt(task, "adk")

    reqBody := TaskExecuteRequest{
        TaskID:       task.ID,
        Prompt:       prompt,
        AgentName:    agentName(task),
        Instructions: agentInstructions(task),
        Skills:       agentSkills(task),
        Repos:        task.Repos,
        Env:          buildTaskEnv(task, slot),
        Model:        entry.Model,
    }

    body, _ := json.Marshal(reqBody)
    req, _ := http.NewRequestWithContext(ctx, "POST",
        entry.Path+"/tasks/execute", bytes.NewReader(body))
    req.Header.Set("Content-Type", "application/json")

    taskLog.Info("dispatching task to HTTP runtime", "url", entry.Path)

    resp, err := http.DefaultClient.Do(req)
    if err != nil {
        return TaskResult{}, fmt.Errorf("http task execute: %w", err)
    }
    defer resp.Body.Close()

    if resp.StatusCode != 200 {
        body, _ := io.ReadAll(resp.Body)
        return TaskResult{}, fmt.Errorf("http task failed (%d): %s",
            resp.StatusCode, string(body))
    }

    var result TaskExecuteResponse
    if err := json.NewDecoder(resp.Body).Decode(&result); err != nil {
        return TaskResult{}, fmt.Errorf("decode response: %w", err)
    }

    return TaskResult{
        Status:     result.Status,
        Comment:    result.Output,
        BranchName: result.BranchName,
        SessionID:  result.SessionID,
        Usage:      result.Usage,
    }, nil
}
```

#### 4.2.3 ADK 侧：任务执行端点

```python
# task_executor.py
from google.adk.agents import Agent
from google.adk.runners import InMemoryRunner
from google.genai import types
import asyncio

class TaskExecutor:
    def __init__(self, config: RuntimeConfig):
        self.config = config
        self._runner_cache: dict[str, InMemoryRunner] = {}

    def _create_agent(self, model: str, instructions: str, skills: list) -> Agent:
        tools = self._resolve_tools(skills)
        return Agent(
            name="multica_worker",
            model=model or self.config.default_model,
            instruction=instructions or self.config.default_instruction,
            tools=tools,
        )

    async def execute(self, request: TaskExecuteRequest) -> TaskExecuteResponse:
        agent = self._create_agent(
            model=request.model,
            instructions=request.instructions,
            skills=request.skills,
        )
        runner = InMemoryRunner(agent=agent)

        session = await runner.session_service.create_session(
            app_name="multica",
            user_id="daemon",
        )

        output_parts = []
        usage_entries = []

        async for event in runner.run_async(
            session=session,
            user_id="daemon",
            new_message=types.Content(
                parts=[types.Part(text=request.prompt)]
            ),
        ):
            if event.content and event.content.parts:
                for part in event.content.parts:
                    if part.text:
                        output_parts.append(part.text)

            # 收集 usage
            if event.usage_metadata:
                usage_entries.append(TaskUsageEntry(
                    provider="adk",
                    model=request.model or self.config.default_model,
                    input_tokens=event.usage_metadata.prompt_token_count or 0,
                    output_tokens=event.usage_metadata.candidates_token_count or 0,
                    cache_read_tokens=event.usage_metadata.cached_content_token_count or 0,
                ))

        return TaskExecuteResponse(
            status="completed",
            output="\n".join(output_parts),
            session_id=session.id,
            usage=usage_entries,
        )
```

### 4.3 流式执行（进阶）

基础方案是同步等待完成。进阶方案支持 SSE 流式上报：

```
Daemon                              ADK Runtime
  │                                     │
  │  POST /tasks/execute                │
  │  Accept: text/event-stream          │
  │────────────────────────────────────►│
  │                                     │
  │  SSE: event: progress               │
  │  data: {"step": 1, "msg": "..."}    │
  │◄────────────────────────────────────│
  │                                     │
  │  SSE: event: message                │
  │  data: {"content": "I'll fix..."}   │
  │◄────────────────────────────────────│
  │                                     │
  │  SSE: event: usage                  │
  │  data: {"tokens": {...}}            │
  │◄────────────────────────────────────│
  │                                     │
  │  SSE: event: result                 │
  │  data: {"status": "completed", ...} │
  │◄────────────────────────────────────│
```

ADK 侧实现：

```python
from fastapi.responses import StreamingResponse

@app.post("/tasks/execute")
async def execute_task(request: TaskExecuteRequest):
    async def event_stream():
        executor = TaskExecutor(config)
        async for event in executor.execute_streaming(request):
            yield f"event: {event.type}\ndata: {event.json()}\n\n"
    return StreamingResponse(event_stream(), media_type="text/event-stream")
```

Daemon 侧通过 SSE client 消费流，实时调用 `ReportProgress`：

```go
func (d *Daemon) runHTTPTask(ctx context.Context, ...) (TaskResult, error) {
    // ... 构建 request ...

    resp, err := http.DefaultClient.Do(req)
    // 读取 SSE stream
    scanner := bufio.NewScanner(resp.Body)
    for scanner.Scan() {
        line := scanner.Text()
        if strings.HasPrefix(line, "event: progress") {
            // 解析 data 行，调用 ReportProgress
        } else if strings.HasPrefix(line, "event: result") {
            // 解析最终结果
        }
    }
}
```

### 4.4 取消任务

Daemon 已有 `watchTaskCancellation` 机制（轮询服务端任务状态）。对于 HTTP runtime：

```go
// 通过 context cancellation 传播取消信号
// 方案 1：直接取消 HTTP request context（断开连接）
// 方案 2：显式调用取消端点

func (d *Daemon) runHTTPTask(...) {
    runCtx, runCancel := context.WithCancel(ctx)
    defer runCancel()

    // watchTaskCancellation 已有，它会 cancel runCtx
    // 当 runCtx 被取消，HTTP request 自动中断
    // ADK Runtime 侧检测到连接断开，停止 Agent 执行

    req, _ := http.NewRequestWithContext(runCtx, "POST", ...)
}
```

ADK 侧：

```python
@app.post("/tasks/execute")
async def execute_task(request: Request):
    # FastAPI 自动检测断开连接
    body = await request.json()
    try:
        result = await executor.execute(body)
        return result
    except asyncio.CancelledError:
        # 客户端断开 → 清理 Agent 执行
        return TaskExecuteResponse(status="cancelled")
```

### 4.5 心跳与恢复

**关键设计决策**：HTTP runtime 的心跳仍然由 Multica Daemon 管理。

```
┌──────────┐                        ┌──────────┐
│  Daemon  │ ◄── WS heartbeat ────► │  Server  │
│          │                        │          │
│          │ ── GET /health ──────► │          │
│          │    探测 HTTP runtime    │  ADK     │
│          │    （独立于服务端心跳）   │  Runtime │
└──────────┘                        └──────────┘
```

Daemon 对 HTTP runtime 独立进行健康探测：

```go
// http_runtime.go

func (d *Daemon) probeHTTPRuntimes(ctx context.Context) {
    ticker := time.NewTicker(30 * time.Second)
    defer ticker.Stop()

    for {
        select {
        case <-ctx.Done():
            return
        case <-ticker.C:
            d.mu.Lock()
            for name, entry := range d.cfg.Agents {
                if entry.Mode != "http" {
                    continue
                }
                resp, err := http.Get(entry.Path + "/health")
                if err != nil || resp.StatusCode != 200 {
                    d.logger.Warn("HTTP runtime unhealthy", "name", name)
                    // 可选：触发重新注册或标记为 offline
                }
                if resp != nil {
                    resp.Body.Close()
                }
            }
            d.mu.Unlock()
        }
    }
}
```

### 4.6 多 Agent 支持

一个 ADK HTTP Runtime 实例可以托管多个 Agent：

```python
# config.yaml
agents:
  code-reviewer:
    model: gemini-2.5-pro
    instruction: "You are a code reviewer..."
    tools: [google_search]

  task-worker:
    model: gemini-2.5-flash
    instruction: "You execute tasks..."
    tools: [bash_tool, google_search]

  docs-writer:
    model: claude-sonnet-4-6
    instruction: "You write documentation..."
```

每个 Agent 注册为独立的 Multica runtime（同一 daemon，不同 runtime_id）。

## 五、文件变更清单

### 5.1 Multica（Go）变更

| 文件 | 变更类型 | 说明 |
|------|---------|------|
| `internal/daemon/config.go` | 修改 | 新增 HTTP agent 探测，`AgentEntry` 增加 `Mode` 字段 |
| `internal/daemon/http_runtime.go` | **新增** | `runHTTPTask`、`DetectVersionHTTP`、`probeHTTPRuntimes` |
| `internal/daemon/daemon.go` | 修改 | `runTask` 路由到 `runCLITask` / `runHTTPTask` |
| `internal/daemon/types.go` | 修改 | `AgentEntry` 增加 `Mode` |

### 5.2 新增 Python 包（adk-multica-runtime）

| 文件 | 说明 |
|------|------|
| `pyproject.toml` | 依赖 `google-adk`、`fastapi`、`uvicorn` |
| `src/adk_multica_runtime/__main__.py` | CLI 入口 |
| `src/adk_multica_runtime/server.py` | FastAPI 服务 |
| `src/adk_multica_runtime/executor.py` | 任务执行（Runner 封装） |
| `src/adk_multica_runtime/config.py` | YAML 配置加载 |

### 5.3 不变的部分

- **Multica Server API**：`/api/daemon/*` 全部不变
- **任务生命周期**：`claim → start → progress → complete/fail` 不变
- **心跳协议**：Daemon ↔ Server 的 WS/HTTP 心跳不变
- **前端**：无变更

## 六、配置示例

### 6.1 启动 ADK HTTP Runtime

```yaml
# adk-runtime.yaml
server:
  host: "127.0.0.1"
  port: 8900

runtime:
  name: "adk-local"
  max_concurrent_tasks: 4

agents:
  - name: "code-agent"
    model: "gemini-2.5-flash"
    instruction: |
      You are a coding assistant managed by Multica.
      Execute tasks as instructed.
    tools:
      - google_search
```

```bash
# 启动
adk-multica-runtime --config adk-runtime.yaml
```

### 6.2 Multica Daemon 配置

```bash
# 环境变量方式
export MULTICA_ADK_HTTP_URL="http://127.0.0.1:8900"
export MULTICA_ADK_MODEL="gemini-2.5-flash"

# 或者在 .multica/config.toml 中
[agents.adk]
mode = "http"
url = "http://127.0.0.1:8900"
model = "gemini-2.5-flash"
```

## 七、与 A2A 的关系

本方案**不直接使用 A2A 协议**作为 Daemon ↔ Runtime 通信协议，原因：

| 维度 | Multica Daemon 协议 | A2A 协议 |
|------|-------------------|---------|
| 定位 | Daemon ↔ Agent 执行 | Agent ↔ Agent 互操作 |
| 任务模型 | claim + env + stdout | Task Send/Get/Subscribe |
| 状态模型 | 服务端权威 | 分布式 |
| 复杂度 | 低（HTTP POST） | 中（Agent Card + 多端点） |

但保留了 A2A 作为**未来演进方向**：

```
Phase 1（本方案）：HTTP Runtime Bridge
  Daemon ──HTTP──► adk-multica-runtime ──Runner──► Agent

Phase 2：A2A Native
  Daemon ──A2A Client──► ADK Agent (to_a2a)

Phase 3：Mesh 模式
  Multica ──A2A──► ADK Agent A ──A2A──► ADK Agent B
```

Phase 2 需要 Multica Daemon 实现完整的 A2A Client，工作量较大。Phase 1 可作为 MVP 快速落地，Phase 2 在 Phase 1 稳定后平滑演进。

## 八、实施计划

### Phase 1：MVP（1-2 天）

- [ ] `adk-multica-runtime` Python 包：health + agent/card + tasks/execute
- [ ] `AgentEntry.Mode` 字段 + `config.go` HTTP 探测
- [ ] `http_runtime.go`：`runHTTPTask` 同步模式
- [ ] 集成测试：启动 ADK Runtime → Daemon 注册 → 下发任务 → 验证结果

### Phase 2：流式 + 取消（1 天）

- [ ] SSE 流式执行
- [ ] 取消传播（context cancellation → 连接断开）
- [ ] Daemon 侧 `probeHTTPRuntimes` 健康探测

### Phase 3：多 Agent + 生产化（2-3 天）

- [ ] 多 Agent 配置（一个 Runtime 实例 → 多个 Multica runtime_id）
- [ ] 认证传递（Daemon token → ADK Runtime → LLM API key）
- [ ] 优雅关闭（SIGTERM → 排干正在执行的任务）
- [ ] Docker 化部署

## 九、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| HTTP 调用延迟高于本地 CLI | 中 | 低 | ADK Runtime 本地部署，延迟 < 1ms |
| 长任务超时（HTTP timeout） | 中 | 中 | 分阶段上报 progress，daemon 侧调大超时 |
| Agent 执行内存泄漏 | 低 | 中 | 每个任务独立 Runner，任务结束清理 |
| Daemon 重启丢失 HTTP runtime | 低 | 中 | HTTP Runtime 自身持久运行，Daemon 重启后重新探测注册 |
| SSL/TLS（远程 Runtime） | 低 | 低 | Phase 1 仅本地，远程部署时加 HTTPS |

## 相关链接

- [[adk-python]] — Google ADK 架构分析
- [[multica]] — Multica 平台架构
- [[multica-runtime-discovery]] — Multica Runtime 发现机制
- ADK A2A 模块：`src/google/adk/a2a/`
- Multica Daemon：`server/internal/daemon/`
