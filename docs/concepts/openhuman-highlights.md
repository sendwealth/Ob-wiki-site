# OpenHuman 项目亮点深度解析

> 源自 [tinyhumansai/openhuman](https://github.com/tinyhumansai/openhuman) 源码挖掘，2026-05-19

---

## 1. TokenJuice — LLM 上下文压缩引擎

**位置**: `src/openhuman/tokenjuice/`

这是项目中最具独创性的模块之一。在所有工具输出（git、npm、cargo、docker）进入 LLM 上下文窗口之前，先经过 TokenJuice 压缩。

**核心设计**：

- **三层规则叠加**（优先级递增）：
  1. 内置规则 — `include_str!` 编译时嵌入的 JSON
  2. 用户规则 — `~/.config/tokenjuice/rules/`
  3. 项目规则 — `.tokenjuice/rules/`（相对 cwd）
- 同 ID 规则高优先级覆盖低优先级
- 短输出（<240 字符）直接透传，不做压缩
- 效果示例：`"On branch main\n\tmodified: src/lib.rs\n"` → `"M: src/lib.rs"`

**可学习之处**：
- 把 LLM token 消耗当作系统工程问题来解决，而不是简单裁剪
- 规则可配置可扩展，用户/项目级别可以覆盖默认行为
- 纯库设计（无 RPC/CLI），职责边界清晰

---

## 2. Native Request/Response Bus — 零序列化进程内通信

**位置**: `src/core/event_bus/native_request.rs`

不同于 JSON-RPC 的序列化路径，这是一条 Rust 类型直通的 in-process 通信通道。

**核心设计**：

```
注册: register_native_global::<Request, Response>(method, handler)
调用: request_native_global(method, request) -> Response
```

- **零序列化** — trait objects、`mpsc::Sender`、oneshot channel 直接传递
- **同步注册 + 异步调用** — 注册用 `std::sync::RwLock`（可在 `Once` 块中使用），调用走 async
- **锁不跨 await** — 读锁 clone Arc 后立即释放，慢 handler 不阻塞其他 dispatch
- **测试友好** — 同 method 重复注册即覆盖；或构造独立 `NativeRegistry` 隔离

**可学习之处**：
- 同一进程内跨模块通信不需要序列化，这是性能优化的典范
- 同步/异步分离设计让启动代码和运行时代码各得其所
- 测试隔离策略（覆盖式 mock）简洁有效

---

## 3. Controller Registry — 声明式 RPC 注册表

**位置**: `src/core/all.rs` + 各域的 `schemas.rs`

所有域功能通过统一的 controller 注册表暴露给 CLI 和 JSON-RPC，而不是在 `cli.rs` / `jsonrpc.rs` 里写 if-else 分支。

**核心设计**：

```rust
// 每个域的 schemas.rs 声明
pub fn all_controller_schemas() -> Vec<ControllerSchema> { ... }
pub fn all_registered_controllers() -> Vec<RegisteredController> { ... }

// all.rs 统一收集 + 启动时验证
static REGISTRY: OnceLock<Vec<RegisteredController>> = OnceLock::new();
// 自动检测重复和遗漏
validate_registry(&registered, &declared)?;
```

- **声明式** — 每个域只负责声明自己的 controller，不用知道传输层细节
- **编译时安全** — `OnceLock` 保证只初始化一次，`validate_registry` panic on 重复/遗漏
- **内部 controller 分离** — `INTERNAL_REGISTRY` 存放仅供可信调用者使用的方法
- **方法名约定** — `openhuman.<namespace>_<function>`，自动从 schema 生成

**可学习之处**：
- 消除中心化的 if-else 分发逻辑，改用注册表模式
- 声明 schema + 注册 handler 的分离让文档自动生成成为可能
- 启动时验证（fail fast）比运行时发现错误好得多

---

## 4. Memory Tree — 分层记忆压缩 + Obsidian Wiki

**位置**: `src/openhuman/memory/`

灵感来自 Karpathy 的 [obsidian-wiki workflow](https://x.com/karpathy/status/2039805659525644595)。

**核心架构**：

```
原始数据 → Auto-fetch 拉取 → 分块(Chunker) → LLM 提取实体/关系
    → 向量嵌入 → SQLite 存储 → 分层摘要树
    → Obsidian 兼容 .md 文件输出
```

**分层摘要树**（Memory Tree）：
- 日/周/月层级压缩，每层 ≤3k token Markdown
- Agent 启动时自动预加载 7 天全局摘要到会话上下文
- 定期刷新（`REFRESH_INTERVAL`），长对话也能保持记忆新鲜
- 失败不致命 — 返回空字符串，Agent 照常工作

**Ingestion Pipeline**：
- 解析 → 元数据丰富 → 向量化 → 知识图谱关系提取
- 队列化处理（`IngestionQueue`），单例执行
- 提取实体（`ExtractedEntity`）和关系（`ExtractedRelation`）

**可学习之处**：
- 分层摘要 + 定期刷新的策略，解决了 LLM 长期记忆的核心问题
- Obsidian 兼容输出让用户可以直接浏览和编辑 Agent 的"记忆"
- 容错设计：空工作区、配置缺失、提取失败都优雅降级

---

## 5. Intelligent Model Routing — 智能模型路由

**位置**: `src/openhuman/routing/`

根据任务复杂度自动选择本地或远程 LLM 后端。

**路由策略**：

| 任务类别 | 本地健康 | 目标 |
|----------|----------|------|
| Lightweight | yes | local |
| Lightweight | no | remote |
| Medium | yes | local/remote (hint-driven) |
| Medium | no | remote |
| Heavy | either | remote |

- 本地失败自动 fallback 到远程，并发射遥测事件
- 本地模型健康检查（`LocalHealthChecker`）
- 质量检测（`is_low_quality`）过滤低质量输出
- 支持 Ollama 本地部署

**可学习之处**：
- 把模型选择从硬编码提升为策略驱动的路由层
- fallback + 遥测的组合让成本优化可观测
- 本地优先的策略节省 API 费用，同时保证可用性

---

## 6. Scheduler Gate — 协作式节流

**位置**: `src/openhuman/scheduler_gate/`

一个进程级单例，保护本地 RAM 不被并发 LLM 调用耗尽。

**核心设计**：

- **信号采样** — 一个后台任务每 30s 刷新 `Signals` 并重算 `Policy`
- **Semaphore 门控** — `LLM_SLOTS = 1`，同时只允许一个本地 LLM 调用
- **协作式等待** — `wait_for_capacity()` 让 worker 阻塞直到有容量
- **测试隔离** — 每个 tokio runtime 独立的 semaphore，避免并行测试互相干扰

**可学习之处**：
- Semaphore + 策略模式的组合，简洁但有效的资源保护
- 测试环境与生产环境的不同实现（`cfg(test)`），避免并行测试竞争
- 明确文档化设计决策（为什么 LLM_SLOTS = 1）

---

## 7. In-Process Core Lifecycle — 进程内核心生命周期

**位置**: `app/src-tauri/src/core_process.rs`

核心不再作为 sidecar 进程运行，而是作为 tokio task 嵌入 Tauri 宿主内。

**关键设计**：

- **生命周期绑定** — Cmd+Q 时核心随 GUI 一起死，不会泄漏孤儿进程
- **Stale-listener 检测** — 端口被占用时，先探测 `GET /` 判断是否是旧 OpenHuman 核心
- **PID 重试验证** — force-kill 前重新验证 PID 未变，防止 PID 复用误杀
- **每启动生成 Bearer Token** — 256-bit 随机 hex，通过 `OPENHUMAN_CORE_TOKEN` 环境变量传递
- **可选外部附加** — `OPENHUMAN_CORE_REUSE_EXISTING=1` 允许连接外部调试实例

**可学习之处**：
- in-process 架构消除了 sidecar 的所有进程管理问题
- stale-listener 检测 + PID 验证是防御性编程的优秀实践
- 每次启动生成新 token，避免 token 泄露的长期风险

---

## 8. RPC Legacy Alias Rewriting — 向后兼容的优雅方案

**位置**: `src/core/dispatch.rs` + `src/core/legacy_aliases.rs`

前后端双写策略实现方法名重命名的平滑过渡：

```
前端 normalizeRpcMethod → 改写出站请求（已更新的客户端）
核心 resolve_legacy     → 改写入站请求（未更新的客户端）
```

- 前端改写 + 后端改写，双重保障，无论客户端版本如何都能正确路由
- debug 级别日志，保持热路径安静
- 聚合可见性留给可观测层，不分发层

**可学习之处**：
- API 重命名不用 break 旧客户端，双写策略优雅实用
- 分层日志策略：分发层 debug，聚合在可观测层

---

## 9. Capability Catalog — 隐私透明的功能目录

**位置**: `src/openhuman/about_app/catalog.rs`

每个功能都声明了数据流向和隐私属性：

```rust
struct CapabilityPrivacy {
    leaves_device: bool,       // 数据是否离开设备
    data_kind: PrivacyDataKind, // 数据类型 (Raw/Derived/Credentials/Diagnostics/Metadata)
    destinations: &[&str],      // 数据去向 (OpenHuman backend / GitHub Releases / Composio / Hugging Face)
}
```

- 用户可以精确知道每个功能的数据去向
- 区分 "原始数据留在本地" vs "凭证发送到第三方" 等不同场景
- Composio 直连模式正确标记为 `leaves_device: true`，目标为 `backend.composio.dev`

**可学习之处**：
- 隐私不是附加说明，而是功能声明的一部分
- 用类型系统表达隐私属性，而不是文档注释
- 正确区分第一方和第三方数据接收方

---

## 10. Composio 集成 — 后端代理的第三方工具接入

**位置**: `src/openhuman/composio/`

通过 Composio 接入 1000+ OAuth 集成（Gmail、Notion、GitHub、Slack...），但核心不直接调用 Composio API。

**架构**：

```
Composio webhook → 后端 HMAC 验证 → 后端通过 Socket.IO 推送
→ 核心解析 → DomainEvent::ComposioTriggerReceived → 订阅者处理
```

- 核心永远不持有 API key，所有调用经后端代理
- HMAC 验证在服务端完成，核心只需响应事件
- Agent 工具 + RPC 控制器 + 事件订阅三层暴露

**可学习之处**：
- 安全边界清晰：核心不触碰第三方凭证
- Webhook → 事件总线的解耦让新集成只需加订阅者
- 后端代理模式让计费/限流/审计集中管理

---

## 总结：项目级设计哲学

| 原则 | 体现 |
|------|------|
| **声明式优于命令式** | Controller Registry, Capability Catalog |
| **零序列化优化** | Native Request/Response Bus |
| **容错降级** | Memory Tree 空结果返回空串，Scheduler Gate 失败阻塞 |
| **本地优先** | Model Routing 本地优先 + 远程 fallback |
| **隐私内建** | 每个功能的数据流向都是结构化声明 |
| **进程内架构** | 消除 sidecar，核心嵌入 Tauri 宿主 |
| **可扩展规则** | TokenJuice 三层叠加，Controller Registry 域自注册 |
