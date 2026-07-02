---
title: Browser-Use 技术架构深度解析
created: 2026-05-18
updated: 2026-05-18
type: concept
tags: [ai, agent, python, browser, cdp, event-bus, architecture, async, pydantic, dom]
sources:
  - ~/Projects/browser-use
  - https://github.com/browser-use/browser-use
confidence: high
related:
  - "[[openhuman-architecture]]"
  - "[[langflow-architecture]]"
  - "[[gstack-browser-architecture]]"
  - "[[context-mode]]"
---

# Browser-Use 技术架构深度解析

> Browser-Use 是一个 async Python >=3.11 库，用 **LLM + CDP (Chrome DevTools Protocol)** 实现 AI 浏览器自动化。核心循环：解析页面 DOM → LLM 决策 → CDP 执行动作 → 循环直到任务完成。架构特点：事件驱动 + Watchdog 服务群 + Pydantic v2 全贯穿。

## 1. 整体架构：Agent 驱动的事件系统

```
┌──────────────────────────────────────────────────────────┐
│                    Agent (orchestrator)                    │
│  任务接收 · LLM循环 · 状态管理 · 历史记录 · GIF生成        │
├──────────┬───────────┬──────────────┬─────────────────────┤
│MessageMgr│  Tools    │  DomService  │    FileSystem       │
│ Prompt构建│ 动作注册表 │ DOM/AX树解析  │   文件读写          │
├──────────┴───────────┴──────────────┴─────────────────────┤
│              BrowserSession (浏览器生命周期)                │
│  CDP连接 · 多Tab管理 · EventBus分发 · Profile配置          │
├──────────────────────────────────────────────────────────┤
│              Watchdog 服务群 (bubus EventBus)              │
│  DOM · Downloads · Popups · Security · Crash · Captcha    │
├──────────────────────────────────────────────────────────┤
│              cdp-use (CDP typed client)                    │
│  WebSocket连接 · 自动生成的类型接口 · Session池             │
└──────────────────────────────────────────────────────────┘
```

**关键决策**：所有浏览器操作通过 `bubus` EventBus 分发，而非直接函数调用。Watchdog 监听事件并执行具体 CDP 操作。这实现了 Agent/Tools 层与浏览器底层完全解耦。

---

## 2. Agent：核心编排器

`browser_use/agent/service.py` — 整个系统的主入口。

### 2.1 Agent 循环

```
获取浏览器状态 (DOM + 截图)
        ↓
构建消息 (MessageManager)
        ↓
调用 LLM → AgentOutput
  ├── thinking          (内部推理)
  ├── evaluation_previous_goal  (上一步评估)
  ├── memory            (跨步骤长期记忆)
  ├── next_goal         (下一步意图)
  └── action[]          (动作列表，每步最多5个)
        ↓
通过 Tools 执行动作 → ActionResult[]
        ↓
记录到 AgentHistory
        ↓
循环直到 is_done 或 max_steps
```

### 2.2 AgentOutput 的 Brain 结构

LLM 的结构化输出遵循 `AgentBrain` 模型：

| 字段 | 类型 | 用途 |
|------|------|------|
| `thinking` | `str \| None` | 内部推理，不暴露给用户 |
| `evaluation_previous_goal` | `str` | 评估上一步是否成功 |
| `memory` | `str` | 跨步骤持久记忆 |
| `next_goal` | `str` | 描述下一步要做什么 |
| `plan_update` | `list[str] \| None` | 动态计划更新 |

### 2.3 状态管理

`AgentState` 跟踪完整执行状态：

```python
class AgentState(BaseModel):
    agent_id: str = Field(default_factory=uuid7str)
    n_steps: int = 1
    consecutive_failures: int = 0
    last_result: list[ActionResult] | None = None
    plan: list[PlanItem] | None = None
    paused: bool = False
    stopped: bool = False
    loop_detector: ActionLoopDetector = Field(default_factory=ActionLoopDetector)
```

**循环检测**：`ActionLoopDetector` 用滚动窗口（默认20步）+ 动作哈希检测重复行为，触发"页面未变化"警告。

### 2.4 配置项

`AgentSettings` 关键参数：

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `max_steps` | 100 | 最大步数 |
| `max_failures` | 5 | 连续失败上限 |
| `max_actions_per_step` | 5 | 每步最大动作数 |
| `use_thinking` | `True` | 启用内部推理 |
| `flash_mode` | `False` | 快速模式（禁用评估和推理） |
| `use_judge` | `True` | 启用 LLM 判断验证 |
| `step_timeout` | 180s | 单步超时 |

---

## 3. BrowserSession：事件驱动浏览器管理

`browser_use/browser/session.py` — 整个系统最复杂的组件。

### 3.1 CDP 层次

```
BrowserSession
├── CDPClient (WebSocket连接)
│   ├── CDPSession → Target (page)
│   ├── CDPSession → Target (iframe)
│   └── CDPSession → Target (worker)
├── SessionManager (session池管理)
└── TimeoutWrappedCDPClient (超时包装)
```

- `Target` — 浏览器实体（page/iframe/worker），每个有 `target_id` 和 `url`
- `CDPSession` — 与 Target 的通信通道，包含 `cdp_client` + `session_id`
- 使用 `cdp-use` 库提供类型安全的 CDP 接口

### 3.2 事件分发模式

Agent/Tools 层不直接调用 CDP，而是通过 EventBus 分发高层事件：

```python
# 发出事件
result = await browser_session.event_bus.dispatch(
    NavigateToUrlEvent(url="https://example.com")
)

# 对应的 Watchdog 监听并执行
class DOMWatchdog(BaseWatchdog):
    async def on_NavigateToUrlEvent(self, event):
        # 执行 CDP 导航、等待加载、更新 DOM
```

**事件分类**：

| 类别 | 典型事件 | 超时 |
|------|---------|------|
| 浏览器生命周期 | `BrowserConnectedEvent`, `BrowserStoppedEvent` | 30s |
| Tab 管理 | `TabCreatedEvent`, `TabClosedEvent`, `SwitchTabEvent` | 3-30s |
| 导航 | `NavigateToUrlEvent`, `GoBackEvent` | 30s |
| 元素交互 | `ClickElementEvent`, `TypeTextEvent`, `ScrollEvent` | 15s |
| DOM | `TabUpdatedEvent` | 30s |
| 文件 | `DownloadStartedEvent`, `DownloadCompletedEvent` | 300s |
| 存储 | `SetCookiesEvent`, `GetCookiesEvent` | 30s |

所有超时可通过环境变量 `TIMEOUT_<EventName>` 覆盖。

---

## 4. Watchdog 服务群

### 4.1 基类设计

`BaseWatchdog` 提供完整的生命周期管理基础设施：

```python
class BaseWatchdog(BaseModel):
    LISTENS_TO: ClassVar[list[type[BaseEvent]]] = []  # 声明监听
    EMITS: ClassVar[list[type[BaseEvent]]] = []        # 声明发出

    event_bus: EventBus = Field()
    browser_session: BrowserSession = Field()
```

核心能力：
- **自动注册**：通过 `on_EventTypeName` 命名约定自动绑定事件处理器
- **CDP 错误恢复**：handler 内部捕获 CDP 断连，自动重建 session
- **去重保护**：阻止同一 watchdog 重复注册
- **超时守卫**：每个 action 有全局超时上限（默认180s），防止 CDP WebSocket 挂死

### 4.2 Watchdog 清单

| Watchdog | 文件 | 职责 |
|----------|------|------|
| `DOMWatchdog` | `dom_watchdog.py` | DOM 快照、截图、元素高亮 |
| `DownloadsWatchdog` | `downloads_watchdog.py` | PDF 自动下载、文件管理 |
| `PopupsWatchdog` | — | JS 对话框、弹窗处理 |
| `SecurityWatchdog` | — | 域名限制、安全策略 |
| `CrashWatchdog` | `crash_watchdog.py` | 浏览器崩溃检测与恢复 |
| `CaptchaWatchdog` | `captcha_watchdog.py` | 验证码检测 |
| `AboutBlankWatchdog` | `aboutblank_watchdog.py` | 空白页重定向 |
| `DefaultActionWatchdog` | `default_action_watchdog.py` | 默认动作处理 |
| `HARRecordingWatchdog` | `har_recording_watchdog.py` | HAR 网络录制 |
| `LocalBrowserWatchdog` | `local_browser_watchdog.py` | 本地浏览器生命周期 |
| `PermissionsWatchdog` | `permissions_watchdog.py` | 浏览器权限管理 |
| `StorageStateWatchdog` | `storage_state_watchdog.py` | Cookie/localStorage 持久化 |

**共享状态规则**：Watchdog 间的共享状态放在 `BrowserSession` 上而非 watchdog 自身。共享方法同样如此。这避免了 watchdog 间的隐式耦合。

### 4.3 新增 Watchdog 流程

```
1. 创建 browser_use/browser/watchdogs/my_watchdog.py
2. 继承 BaseWatchdog，声明 LISTENS_TO 和 EMITS
3. 实现 on_XxxEvent 方法
4. 在 BrowserSession._setup_watchdogs() 中注册
```

---

## 5. DomService：页面理解引擎

`browser_use/dom/service.py` — 将原始 DOM 转化为 LLM 可理解的结构。

### 5.1 两阶段提取

```
CDP Accessibility.getFullAXTree
        ↓
EnhancedAXNode 树 (语义化)
        ↓
CDP DOMSnapshot.captureSnapshot
        ↓
EnhancedDOMTreeNode 树 (样式+布局)
        ↓
合并 → ClickableElementDetector → SerializedDOMState
```

**为什么用 AX 树而非原始 DOM？** AX (Accessibility) 树已经过浏览器语义化处理，按钮、链接、输入框等有明确的角色标注，比原始 HTML 更适合 LLM 理解。

### 5.2 输出结构

`SerializedDOMState` 包含：
- **可点击元素列表** — 带 index 编号，供 LLM 引用（如 "click element 5"）
- **元素边界框** — 用于高亮和坐标点击
- **页面文本内容** — 用于 LLM 上下文
- **iframe 处理** — 递归进入 iframe 提取（限制深度和数量）

### 5.3 iframe 策略

```python
max_iframes: int = 100       # 最多处理 iframe 数
max_iframe_depth: int = 5    # 最大递归深度
viewport_threshold: int = 1000  # 视口阈值，隐藏 viewport 外元素
```

---

## 6. Tools：动作注册表

`browser_use/tools/service.py` — 将 LLM 输出映射为浏览器事件。

### 6.1 内置动作

| 动作 | 事件 | 说明 |
|------|------|------|
| `click_element` | `ClickElementEvent` | 按 index 点击元素 |
| `click_coordinate` | `ClickCoordinateEvent` | 按坐标点击 |
| `input_text` | `TypeTextEvent` | 输入文本 |
| `navigate_to` | `NavigateToUrlEvent` | 导航到 URL |
| `scroll` | `ScrollEvent` | 滚动页面 |
| `switch_tab` | `SwitchTabEvent` | 切换 Tab |
| `close_tab` | `CloseTabEvent` | 关闭 Tab |
| `go_back` | `GoBackEvent` | 浏览器后退 |
| `send_keys` | `SendKeysEvent` | 发送按键 |
| `upload_file` | `UploadFileEvent` | 上传文件 |
| `extract` | — | 提取页面内容（可选 LLM 二次处理） |
| `done` | — | 标记任务完成 |
| `screenshot` | — | 截图 |
| `search_page` | — | 页面内搜索 |
| `save_as_pdf` | — | 保存为 PDF |

### 6.2 自定义动作注册

通过 `Registry` 类扩展：

```python
from browser_use import Controller

controller = Controller()

@controller.action("自定义动作描述")
async def my_custom_action(params: MyParamModel, browser_session: BrowserSession):
    # 执行自定义逻辑
    return ActionResult(extracted_content="结果")
```

### 6.3 动作超时

全局动作超时 180s（高于最长的内置超时 120s 的 extract 动作），可通过 `BROWSER_USE_ACTION_TIMEOUT_S` 环境变量或 `tools.act(action_timeout=...)` 覆盖。

---

## 7. LLM 集成

### 7.1 统一接口

所有 LLM 供应商通过 `BaseChatModel` 统一接口：

```python
from browser_use import ChatGoogle, ChatOpenAI, ChatAnthropic

agent = Agent(
    task="搜索天气",
    llm=ChatGoogle(model="gemini-2.5-pro"),
)
```

**支持的供应商**：

| 供应商 | 类 | 备注 |
|--------|------|------|
| OpenAI | `ChatOpenAI` | GPT-4o 等 |
| Anthropic | `ChatAnthropic` | Claude 系列 |
| Google | `ChatGoogle` | Gemini 系列 |
| Groq | `ChatGroq` | 快速推理 |
| Ollama | `ChatOllama` | 本地模型 |
| Azure | `ChatAzureOpenAI` | Azure 托管 |
| BrowserUse | `ChatBrowserUse` | 自有模型 |
| OCI | `ChatOCIRaw` | Oracle Cloud |
| Vercel | `ChatVercel` | Vercel AI Gateway |

### 7.2 Schema 优化

`tools/registry/service.py` 中的 `optimize_schema()` 函数对 JSON Schema 做精简，减少 token 消耗：移除 description 中的冗余文本、压缩 enum 定义等。

---

## 8. 事件总线：bubus

Browser-Use 使用 [bubus](https://github.com/browser-use/bubus) 作为事件总线（本地可编辑依赖）。

### 8.1 核心概念

```python
from bubus import BaseEvent, EventBus

class MyEvent(BaseEvent):
    url: str
    event_timeout: float | None = 15.0

# 注册处理器
event_bus.on(MyEvent, handler)

# 分发并等待结果
result = await event_bus.dispatch(MyEvent(url="https://..."))
```

### 8.2 与 OpenHuman 事件总线对比

| | Browser-Use (bubus) | [[openhuman-architecture|OpenHuman]] (tokio broadcast) |
|---|---|---|
| 语言 | Python async | Rust tokio |
| 模式 | 单一 dispatch/on | 双面：broadcast + native request/response |
| 序列化 | Pydantic 模型 | 零序列化（Arc 直传） |
| 类型安全 | Python type hints | Rust 编译时 |
| 超时 | 每事件可配 | handler 内管理 |

共通点：都是**事件驱动解耦**，新增功能不改框架代码。差异在于 Python 的动态性允许更灵活的事件定义，Rust 的编译时保证更严格。

---

## 9. MCP 集成

Browser-Use 支持两种 MCP 模式：

### 9.1 作为 MCP Server

```bash
uvx browser-use[cli] --mcp
```

暴露浏览器自动化工具给 Claude Desktop 等 MCP 客户端。

### 9.2 作为 MCP Client

Agent 可连接外部 MCP 服务器（文件系统、GitHub 等）扩展能力：

```python
agent = Agent(
    task="...",
    llm=...,
    mcp_servers=["filesystem:///path"],
)
```

连接管理在 `browser_use/mcp/client.py`。

---

## 10. 代码风格与约定

### 10.1 文件组织

| 模式 | 说明 | 示例 |
|------|------|------|
| `service.py` | 主逻辑 | `agent/service.py`, `dom/service.py` |
| `views.py` | Pydantic 数据模型 | `agent/views.py`, `browser/views.py` |
| `events.py` | 事件定义 | `browser/events.py` |
| `profile.py` | 配置 | `browser/profile.py` |
| `watchdogs/` | Watchdog 子目录 | `browser/watchdogs/dom_watchdog.py` |

### 10.2 关键约定

| 约定 | 实现 |
|------|------|
| **缩进** | tabs（不是 spaces） |
| **类型** | `str \| None` 而非 `Optional[str]`，`list[str]` 而非 `List[str]` |
| **ID 生成** | `uuid7str`（时间排序）而非 UUID4 |
| **日志** | 所有日志方法以 `_log_` 前缀 |
| **验证** | `Annotated[..., AfterValidator(...)]` 内联验证 |
| **断言** | 运行时 `assert` 强制约束 |
| **懒加载** | `__init__.py` 用 `__getattr__` 延迟重型导入 |

### 10.3 测试规则

- **禁止 mock**（LLM 除外）
- 用 `pytest-httpserver` 代替真实 URL
- 现代 pytest-asyncio（无需 `@pytest.mark.asyncio`）
- 通过测试移入 `tests/ci/` 目录

---

## 11. 技术栈总结

| 层 | 技术 | 用途 |
|----|------|------|
| 核心 | Python >=3.11 (async) | 主语言 |
| 数据模型 | Pydantic v2 | 类型安全、验证、序列化 |
| 浏览器控制 | CDP (cdp-use) | 类型安全的 Chrome DevTools Protocol |
| 事件总线 | bubus | 进程内事件分发 |
| LLM | OpenAI / Anthropic / Google / ... | 多供应商决策引擎 |
| 包管理 | uv | 依赖管理 |
| 类型检查 | pyright | 静态分析 |
| 代码风格 | ruff | lint + format |
| MCP | mcp SDK | 双向协议集成 |
| CLI | click + textual | 命令行和 TUI |

---

## 核心启示

> **Browser-Use 的架构哲学是"事件驱动解耦 + LLM 结构化输出"。**
>
> Agent 不直接操作浏览器，而是通过 EventBus 分发高层事件，Watchdog 服务群监听并执行具体的 CDP 操作。这种设计使得：
> 1. **新增浏览器能力只需加 Watchdog** — 不改 Agent 或 Tools 代码
> 2. **Watchdog 间零耦合** — 共享状态集中在 BrowserSession，通信走事件
> 3. **LLM 输出完全结构化** — `AgentOutput` 的 brain 模型强制 LLM 输出 thinking/eval/memory/goal，而非自由文本
>
> 与 [[openhuman-architecture|OpenHuman]] 的 Rust 事件总线对比：两者都选择事件驱动解耦，但 Browser-Use 用 Python 的动态性换取了更快的迭代速度，代价是缺少编译时保障。与 [[gstack-browser-architecture|gstack 浏览器架构]] 对比：gstack 用 Bun + Playwright daemon + Ref 系统，Browser-Use 用原生 CDP + Pydantic 模型，前者偏向开发体验，后者偏向 AI agent 的精确控制。
