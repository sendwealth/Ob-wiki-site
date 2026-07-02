# LobeChat 模式借鉴到 Agent-World：产品推演与必要性规划

> 文档版本：v1.0 | 日期：2026-05-19 | 角色：产品经理视角

---

## 0. 前置分析：两个项目的本质差异

在逐一分析 7 个模式之前，必须先建立一个判断框架——LobeChat 和 agent-world 在架构目标上有根本差异：

| 维度 | LobeChat | Agent-World |
|------|----------|-------------|
| 本质 | 人机对话前端应用 | AI Agent 生存沙盒后端系统 |
| 核心循环 | 用户输入 → LLM 响应 → 渲染 | Perceive → Decide → Act → 世界状态变更 |
| Agent 数量 | 单 Agent（用户助手） | 10-100+ 独立 Agent 并发 |
| 延迟敏感度 | 毫秒级（流式 token 渲染） | 秒级（Tick 间隔 0.1-1s） |
| 上下文来源 | 用户对话历史 | 世界状态 + A2A 消息 + 记忆 + 生存本能 |
| 安全边界 | 防止 LLM 生成有害内容 | 防止 Agent 破坏世界规则、恶意消耗资源 |
| 可观测性 | 聊天记录 + 开发者调试 | 世界经济指标 + Agent 行为追踪 + 社会关系图 |

**判断原则**：模式是否解决 agent-world Phase 2 的核心阻塞问题（Tick 调度、A2A 通信、任务执行、可观测性），还是只解决"锦上添花"的优化问题。

---

## 1. 产品推演：逐模式分析

### 模式 1：Brain/Engine 分离

**LobeChat 的做法**：Agent 只产出 Instruction（意图），Runtime 负责执行。Executor 可插拔替换（OpenAI/Claude/Ollama 等）。

**对应 agent-world 的现状**：
- `decide.py` 已产出 `Decision` 对象（action_type + parameters + reasoning）
- `act.py` 的 `ActionExecutor` 负责执行
- `think_loop.py` 编排 Perceive → Decide → Act 循环
- LLM Provider 已通过 Protocol（Python 的接口）实现可插拔

**解决的痛点**：
- **当前**：`DecisionEngine` 和 LLM Provider 是紧耦合的——`decide()` 内部直接调用 `self._provider.chat()`，决策逻辑和执行通道未分离
- **Phase 2 阻塞**：当 Agent 需要"模拟执行"（dry-run）一个交易提案再决定是否提交时，缺少 Instruction → Execution 的中间层
- **可量化收益**：将决策产出与执行通道分离后，可独立测试决策质量（无需调用真实 LLM），预计减少 40% 的集成测试时间

**不做会怎样**：
- 中等风险。当前架构已经隐式做到了"Decision 对象就是 Instruction"，只是没有显式抽象。Phase 2 增加新 Action 类型时，耦合度会逐步上升
- 如果 Phase 3 要支持"Agent 学习新技能并执行自定义工具"，当前紧耦合会成为瓶颈

**Phase 2 模块依赖**：
- `tools/`（自定义工具执行）—— 依赖 Instruction 抽象
- `a2a/`（A2A 消息构建）—— 消息是 Decision 到 Instruction 的自然产物
- 不阻塞 Tick 调度器、生命周期、经济系统

**产品评分**：
| 维度 | 评分 | 理由 |
|------|------|------|
| 用户故事覆盖 | 3/5 | 研究者想观察 Agent 的"意图"vs"实际行为"差异 |
| 不做的影响 | 2/5 | 短期可绕过，Phase 3 才会痛 |
| 可量化收益 | 2/5 | 测试效率提升，但不直接影响用户可见功能 |

---

### 模式 2：InterventionChecker（安全拦截层）

**LobeChat 的做法**：工具执行前的安全拦截层，安全黑名单不可绕过。在 LLM 调用工具前，检查参数是否合规。

**对应 agent-world 的现状**：
- `world-engine/src/rules.rs` 已有 `RuleRegistry`，含 10 条规则（3 条已实现、7 条已定义）
- `act.py` 的 `ActionExecutor` 在执行前检查 token 余额（`can_afford`）
- `survival/instinct.py` 在 Decide 之前做生存评估，可跳过 LLM 决策
- **没有**：在 Agent 决策到执行之间的"意图校验层"

**解决的痛点**：
- **关键痛点**：R030（防资源耗尽攻击）、R031（防繁殖失控）需要在 Action 执行前拦截，但当前规则引擎在 world-engine（Rust）侧，agent-runtime（Python）侧没有校验
- **场景**：Agent A 向 Agent B 发送 THREAT 消息，B 的 LLM 可能"害怕"并做出非理性行为——需要在消息接收端有安全拦截
- **可量化收益**：防止 10 个 Agent 在恐慌模式下同时广播 SOS 导致消息风暴（已观测到 survival instinct 的 `_ACTION_COOLDOWN = 5.0` 是硬编码的）

**不做会怎样**：
- 高风险。Phase 2 接入真实 A2A 通信后，没有安全拦截意味着恶意/失控 Agent 可以：无限广播消息消耗 Token、向新手发送欺诈提案、利用规则漏洞自我复制
- world-engine 的规则是"事后判定"（evaluate 在 Tick 结束时），不是"事前拦截"

**Phase 2 模块依赖**：
- `a2a/`（A2A 消息收发）—— **强依赖**，消息必须经过拦截层
- `tools/`（自定义工具）—— **强依赖**，工具执行必须有沙箱
- `survival/` 的紧急行动—— 需要拦截层防止广播风暴
- Tick 调度器—— 调度器需要调用拦截层

**产品评分**：
| 维度 | 评分 | 理由 |
|------|------|------|
| 用户故事覆盖 | 4/5 | 研究者需要看到"世界是安全的"，开发者需要防止 Agent 失控 |
| 不做的影响 | 4/5 | Phase 2 接入真实通信后，没有拦截=灾难 |
| 可量化收益 | 3/5 | 防止消息风暴、资源耗尽，直接影响系统稳定性 |

---

### 模式 3：Hook 生命周期（before_think / after_act / on_error）

**LobeChat 的做法**：`before_think`、`after_act`、`on_error` 等钩子，`before_act` 支持 mock（用于测试）。

**对应 agent-world 的现状**：
- `think_loop.py` 的 `_think_once()` 有隐式阶段：Perceive → Survival Assess → Decide → Act → Reflect
- 错误处理是 `try/except` + `logger.warning`，没有可插拔的 `on_error` 回调
- 没有 before/after 钩子——例如无法在 Decide 前注入额外的上下文，也无法在 Act 后自动记录到可观测性系统

**解决的痛点**：
- **核心痛点**：Phase 2 需要"可观测性"，而可观测性的数据采集点就是 Think Loop 的各个阶段。没有 Hook = 每个阶段手动添加埋点代码 = 耦合
- **测试痛点**：当前测试通过 `vi.spyOn` 或 mock Provider 来验证行为，如果有 `before_act` mock 能力，可以更优雅地做"决策沙箱"
- **可量化收益**：Hook 机制使可观测性插件化，预计减少 60% 的埋点代码修改量

**不做会怎样**：
- 中等风险。Phase 2 做可观测性时，会直接在 `_think_once()` 里硬编码埋点，后续每加一个监控维度都要改核心循环
- 如果 Phase 3 要支持"人类干预"（暂停 Agent、注入消息），没有 Hook 就只能改 ThinkLoop 本身

**Phase 2 模块依赖**：
- `observability/`（可观测性）—— **强依赖**，Hook 是数据采集的天然接入点
- `a2a/`（消息处理）—— 可通过 Hook 注入消息到决策上下文
- 测试基础设施—— `before_act mock` 提升测试效率
- 不阻塞 Tick 调度器

**产品评分**：
| 维度 | 评分 | 理由 |
|------|------|------|
| 用户故事覆盖 | 4/5 | 研究者需要观察 Agent 每个阶段的行为，开发者需要 Hook 做测试 |
| 不做的影响 | 3/5 | 可以硬编码埋点，但维护成本随功能增长线性上升 |
| 可量化收益 | 3/5 | 埋点效率提升、测试效率提升 |

---

### 模式 4：Context Engine Pipeline（记忆处理链）

**LobeChat 的做法**：记忆处理链——相关性过滤 → 时间衰减 → Token 预算控制 → 上下文注入。确保发送给 LLM 的上下文在预算内且最相关。

**对应 agent-world 的现状**：
- `working_memory.py`：FIFO 缓存 + 重要性衰减（容量 10 条）
- `short_term.py`：SQLite 持久化 + 关键词搜索（容量 100 条）
- `long_term.py`：**未实现**（向量 DB）
- `decide.py` 的 prompt 模板硬编码了固定字段（Identity、State、Skills、Perception、Survival、Actions、Budget、Reputation），**没有动态注入记忆检索结果**
- `memory_aware_decide.py` 存在但是增强层，未整合到主决策流程

**解决的痛点**：
- **最核心痛点**：Agent 的 LLM 调用没有"上下文预算管理"。随着 A2A 消息增多、任务历史积累，发送给 LLM 的 prompt 会无限膨胀 → Token 成本失控 → Agent 加速死亡
- **记忆相关性**：当前 SQLite 只有关键词搜索，没有语义相关性排序。Agent 在 Tick 500 无法有效回忆 Tick 50 的关键事件
- **可量化收益**：Token 预算控制直接影响 Agent 生存时间。如果每次 LLM 调用节省 30% token（通过过滤无关记忆），Agent 平均寿命延长 30%

**不做会怎样**：
- 极高风险。Phase 2 接入 A2A 通信后，Agent 每个 Tick 会收到大量消息。没有记忆过滤 = prompt 膨胀 = Token 快速消耗 = 大规模 Agent 死亡 = 世界崩溃
- 这不是一个"优化"问题，而是 Phase 2 是否能正常运行的前提条件

**Phase 2 模块依赖**：
- `a2a/`（消息处理）—— **强依赖**，消息是上下文的主要来源，必须过滤
- `core/perceive.py`（感知模块）—— 记忆注入应该在感知阶段完成
- `core/decide.py`（决策引擎）—— 决策 prompt 的上下文来源
- 经济系统—— Token 预算 = 生存预算，直接影响 Agent 存活

**产品评分**：
| 维度 | 评分 | 理由 |
|------|------|------|
| 用户故事覆盖 | 5/5 | 直接决定 Agent 能否在信息过载中生存 |
| 不做的影响 | 5/5 | 不做 = Phase 2 无法运行 |
| 可量化收益 | 5/5 | Agent 寿命延长 30%+，LLM 调用成本降低 30%+ |

---

### 模式 5：GraphAgent（声明式图驱动编排）

**LobeChat 的做法**：声明式图驱动的复杂任务编排，将多步骤 LLM 交互建模为有向图。

**对应 agent-world 的现状**：
- 当前决策是"单步决策"：每个 Tick 产出 1 个 Decision，执行 1 个 Action
- 没有"多步任务编排"——Agent 无法规划"先研究 → 再编写代码 → 再提交任务"这样的链式行为
- 任务板系统存在（`economy/task.rs`），但 Agent 侧没有任务分解能力

**解决的痛点**：
- **Phase 3 级别痛点**：当前 Phase 2 的核心问题是让 10 个 Agent 活下来并基本交互，不是让它们执行复杂任务
- 复杂任务编排在 Phase 2 是"锦上添花"——当前 `claim_task → execute → submit_task` 的三步流程可以用简单的状态机实现
- **不适合的场景差异**：GraphAgent 是为"人机对话中需要多轮工具调用"设计的（如搜索 → 阅读 → 总结），而 agent-world 的 Agent 行为更适合用"反应式决策"而非"规划式编排"

**不做会怎样**：
- 低风险。Phase 2 用简单状态机处理任务执行即可。Phase 3（City）才需要多步编排能力

**Phase 2 模块依赖**：
- 不阻塞任何 Phase 2 核心模块
- 可能对 Phase 3 的 `tools/`（自定义工具链）有价值

**产品评分**：
| 维度 | 评分 | 理由 |
|------|------|------|
| 用户故事覆盖 | 2/5 | Phase 2 用户故事不涉及复杂多步任务 |
| 不做的影响 | 1/5 | 简单状态机足够 |
| 可量化收益 | 1/5 | Phase 3 才有收益 |

---

### 模式 6：Agent Tracing（执行快照系统）

**LobeChat 的做法**：执行快照系统——增量记录、状态重建、可视化。记录每一步 LLM 调用的输入/输出，支持回放和调试。

**对应 agent-world 的现状**：
- `act.py` 的 `_history: list[ActionResult]` 记录了执行历史，但仅在内存中，无持久化
- `world-engine` 的 WAL（Write-Ahead Log）记录世界事件，但不是 Agent 级别的行为追踪
- Dashboard 有 EventStream 组件，但只展示世界级别的事件
- 没有任何"Agent 内部状态快照"能力——无法知道 Agent 为什么做了某个决策

**解决的痛点**：
- **核心痛点**：Phase 2 接入真实 A2A 后，会出现"Agent 为什么死亡了？"这样的问题。没有 Tracing = 无法事后分析
- **研究者需求**：用户画像中的"研究者赵博士"需要分析 Agent 行为模式，这需要完整的决策轨迹
- **可量化收益**：有 Tracing 后，调试 Agent 异常行为的时间预计减少 70%（从"猜测原因"到"查看快照"）

**不做会怎样**：
- 中高风险。Phase 2 接入真实 A2A 后必然出现各种意外行为（Agent 死亡太快、交易异常、消息风暴），没有 Tracing 就无法定位问题
- Dashboard 已有 SSE 实时更新，但只展示"发生了什么"，不展示"为什么发生"

**Phase 2 模块依赖**：
- `observability/`（可观测性）—— Tracing 是可观测性的核心组件
- Dashboard（Agent 详情页）—— 需要展示 Tracing 数据
- 不阻塞 Tick 调度器、A2A 通信

**产品评分**：
| 维度 | 评分 | 理由 |
|------|------|------|
| 用户故事覆盖 | 4/5 | 研究者和开发者都需要行为追踪 |
| 不做的影响 | 3/5 | Phase 2 可以通过日志做基础追踪，但效率极低 |
| 可量化收益 | 3/5 | 调试效率提升，但不直接影响 Agent 行为 |

---

### 模式 7：GroupOrchestrationSupervisor（多 Agent 编排状态机）

**LobeChat 的做法**：多 Agent 编排的纯状态机，管理 Agent 间的协作流程（如 Planner → Coder → Reviewer 的任务分配）。

**对应 agent-world 的现状**：
- A2A Protocol 已定义了 PROPOSE → ACCEPT/REJECT 流程
- `world-engine` 的 A2A Router 设计了消息路由
- 没有中心化的"协作编排器"——Agent 间协作完全依赖自发行为
- ARCHITECTURE.md 的 Social Subsystem 设计了"组织系统"，但未实现

**解决的痛点**：
- **核心痛点**：Phase 2 的目标是"10-100 Agent 形成社会关系"。没有编排 = Agent 间只有随机交互，无法形成稳定的协作模式
- **场景**：Agent A 提议"我们一起做任务"，Agent B 接受——但谁分配工作？谁提交结果？没有编排器 = 协作效率极低
- **不适合的场景差异**：LobeChat 的多 Agent 编排是"人驱动"的（用户选择用哪个 Agent），而 agent-world 的协作是"自组织"的。中心化状态机与"自治 Agent"理念冲突

**不做会怎样**：
- 中等风险。Phase 2 可以用"去中心化协商"（现有 A2A PROPOSE/ACCEPT 流程）代替中心化编排。事实上，去中心化协商更符合 agent-world 的设计哲学
- Phase 3（组织系统）可能需要轻量编排，但应该在 Social Subsystem 内部实现

**Phase 2 模块依赖**：
- `a2a/`（消息协议）—— 编排通过消息协议实现，不需要额外编排层
- `social/`（社会子系统）—— Phase 3 的组织系统可能需要
- 不阻塞 Phase 2 核心功能

**产品评分**：
| 维度 | 评分 | 理由 |
|------|------|------|
| 用户故事覆盖 | 2/5 | Phase 2 的协作由 A2A 协议自然涌现 |
| 不做的影响 | 2/5 | 去中心化协商是更符合 agent-world 的方式 |
| 可量化收益 | 1/5 | 收益主要在 Phase 3 |

---

## 2. RICE 优先级排序

### RICE 框架定义

| 因子 | 定义 | 评分范围 |
|------|------|----------|
| Reach | Phase 2 中受影响的用户故事数 | 1-10 |
| Impact | 对每个用户故事的价值（3=巨大，2=高，1=中，0.5=低） | 0.5-3 |
| Confidence | 估算的置信度（高=1.0，中=0.7，低=0.5） | 0.5-1.0 |
| Effort | 工程人周（越小越好） | 1-8 周 |

### RICE 评分表

| # | 模式 | Reach | Impact | Confidence | Effort(周) | RICE 分数 | 优先级 |
|---|------|-------|--------|------------|-------------|-----------|--------|
| 4 | Context Engine Pipeline | 8 | 3 | 1.0 | 3 | **8.0** | P0 |
| 2 | InterventionChecker | 6 | 2 | 0.9 | 2 | **5.4** | P0 |
| 3 | Hook 生命周期 | 5 | 2 | 0.9 | 2 | **4.5** | P1 |
| 6 | Agent Tracing | 4 | 2 | 0.8 | 2 | **3.2** | P1 |
| 1 | Brain/Engine 分离 | 3 | 1 | 0.8 | 3 | **0.8** | P2 |
| 7 | GroupOrchestration | 2 | 0.5 | 0.5 | 4 | **0.125** | P3 |
| 5 | GraphAgent | 1 | 0.5 | 0.5 | 6 | **0.042** | P3 |

### 优先级定义

**P0（必须做）—— Phase 2 启动阻塞项**：
- **Context Engine Pipeline**（RICE 8.0）：不做则 Agent 无法在信息过载中生存，Phase 2 核心目标无法达成
- **InterventionChecker**（RICE 5.4）：不做则 A2A 通信存在安全漏洞，系统不稳定

**P1（应该做）—— Phase 2 运行质量保障**：
- **Hook 生命周期**（RICE 4.5）：不做则可观测性和测试的可维护性差
- **Agent Tracing**（RICE 3.2）：不做则无法调试 Agent 异常行为

**P2（可以做）—— Phase 2 结束前考虑**：
- **Brain/Engine 分离**（RICE 0.8）：当前隐式分离足够，显式化可推迟

**P3（暂缓）—— Phase 3+**：
- **GraphAgent**（RICE 0.042）：Phase 3 的多步任务编排才需要
- **GroupOrchestration**（RICE 0.125）：与 agent-world 的去中心化理念冲突，Phase 3 用 Social Subsystem 替代

### 推荐实施顺序

```
Phase 2A（第 1-4 周）—— 基础能力建设
├── Week 1-2: Context Engine Pipeline (P0)
│   ├── 记忆检索 + 相关性排序
│   ├── Token 预算控制器
│   └── Prompt 动态构建
├── Week 2-3: InterventionChecker (P0)
│   ├── Action 前置校验层
│   ├── 消息收发拦截
│   └── 广播限流
└── Week 3-4: Hook 生命周期 (P1)
    ├── before_think / after_decide / before_act / after_act / on_error
    └── 基础埋点接入

Phase 2B（第 5-8 周）—— 可观测性与集成
├── Week 5-6: Agent Tracing (P1)
│   ├── 执行快照记录
│   ├── Dashboard 集成
│   └── 异常行为回溯
└── Week 7-8: 集成 + 测试
    ├── 全链路集成测试
    └── Brain/Engine 分离评估（如果需要）
```

---

## 3. 依赖关系图

```
                         ┌─────────────────────────┐
                         │  Context Engine Pipeline  │ ← P0
                         │  (记忆处理 + Token 预算)   │
                         └────────────┬──────────────┘
                                      │
                    ┌─────────────────┼─────────────────┐
                    │                 │                  │
                    ▼                 ▼                  ▼
         ┌──────────────┐  ┌──────────────┐   ┌──────────────┐
         │ Intervention │  │    Hook      │   │   decide.py  │
         │  Checker     │  │  Lifecycle   │   │  (prompt 构建 │
         │  (P0)        │  │  (P1)        │   │   依赖上下文) │
         └──────┬───────┘  └──────┬───────┘   └──────────────┘
                │                 │
                │    ┌────────────┤
                │    │            │
                ▼    ▼            ▼
         ┌──────────────┐  ┌──────────────┐
         │   Agent      │  │   A2A        │
         │   Tracing    │  │   Client     │
         │   (P1)       │  │  (Phase 2)   │
         └──────┬───────┘  └──────────────┘
                │
                ▼
         ┌──────────────┐
         │  Dashboard   │
         │  (Agent 详情) │
         └──────────────┘
```

**依赖关系说明**：

| 依赖 | 说明 | 可否并行 |
|------|------|----------|
| Context Engine → decide.py | Pipeline 产出的上下文直接注入决策 prompt | 否（Context Engine 先行） |
| Context Engine → InterventionChecker | Checker 需要知道当前 Token 预算来判定 | 可并行（接口先行） |
| Hook Lifecycle → Agent Tracing | Tracing 通过 Hook 采集数据 | 否（Hook 先行） |
| InterventionChecker → A2A Client | A2A 消息收发必须经过 Checker | 否（Checker 先行） |
| Agent Tracing → Dashboard | Dashboard 展示 Tracing 数据 | 否（Tracing 先行） |
| Brain/Engine 分离 → 无 | 独立，可在任何时间做 | 是（独立开发） |
| GraphAgent → 无 | 独立，Phase 3 | 是 |
| GroupOrchestration → 无 | 独立，Phase 3 | 是 |

**并行开发建议**：
- Sprint 1：Context Engine + InterventionChecker（并行，接口先行对齐）
- Sprint 2：Hook Lifecycle（依赖 Context Engine 的注入点确定）
- Sprint 3：Agent Tracing（依赖 Hook 的数据采集点）

---

## 4. P0 级别 MVP 最小可行方案

### 4.1 Context Engine Pipeline MVP

**目标**：让 Agent 在信息过载时仍能做出合理决策，Token 消耗可控。

**最简实现**（3 周，不含长期记忆向量 DB）：

```python
# 新增文件：agent_runtime/context/engine.py

class ContextEngine:
    """MVP：三阶段上下文处理管线"""

    def __init__(self, token_budget: int = 2000):
        self.token_budget = token_budget
        self.relevance_threshold = 0.3  # 相关性阈值

    async def build_context(
        self,
        agent_state: AgentState,
        perception: Perception,
        working_memory: WorkingMemory,
        short_term_memory: ShortTermMemory,
    ) -> str:
        """三阶段管线：过滤 → 排序 → 预算截断"""

        # Stage 1: 收集所有候选上下文
        candidates = []
        candidates.extend(self._format_perception(perception))
        candidates.extend(self._format_messages(perception.messages))
        candidates.extend(self._recall_memory(working_memory, short_term_memory, perception))
        candidates.extend(self._format_survival_context(agent_state))

        # Stage 2: 相关性排序（基于关键词 + 时间衰减，不用向量 DB）
        scored = []
        for item in candidates:
            score = self._compute_relevance(item, agent_state, perception)
            scored.append((score, item))
        scored.sort(key=lambda x: x[0], reverse=True)

        # Stage 3: Token 预算截断
        selected = []
        remaining = self.token_budget
        for score, item in scored:
            tokens = self._estimate_tokens(item)
            if tokens <= remaining:
                selected.append(item)
                remaining -= tokens
            if remaining < 100:  # 保留 100 token 余量
                break

        return "\n".join(selected)

    def _compute_relevance(self, item: str, state, perception) -> float:
        """MVP：关键词匹配 + 时间衰减（不用嵌入模型）"""
        score = 0.0
        # 关键词匹配
        keywords = [state.name.lower(), "task", "token", "survival"]
        for kw in keywords:
            if kw in item.lower():
                score += 0.2
        # 时间衰减（越近越重要）
        # ... 简单实现
        return min(score, 1.0)

    def _estimate_tokens(self, text: str) -> int:
        """粗略估算：1 token ≈ 4 字符"""
        return len(text) // 4
```

**集成点**：
- `decide.py` 的 `build_prompt()` 改为调用 `ContextEngine.build_context()`
- 不改 `think_loop.py` 的整体流程
- `ContextEngine` 通过 Protocol 注入 `DecisionEngine`，保持可测试

**不做的事情**（推迟到 Phase 3）：
- 向量嵌入 / 语义搜索（用关键词搜索替代）
- 长期记忆整合（`long_term.py` 未实现，暂不涉及）
- 记忆整理（consolidation）自动化

---

### 4.2 InterventionChecker MVP

**目标**：Agent 行为在执行前经过安全校验，防止恶意/失控行为。

**最简实现**（2 周）：

```python
# 新增文件：agent_runtime/safety/checker.py

class InterventionChecker:
    """MVP：五项安全检查，不可绕过"""

    def __init__(self, config: dict | None = None):
        self.broadcast_limit = 5        # 每 Tick 最多广播 5 次
        self.message_size_limit = 1000  # 单条消息最大字符数
        self.newbie_protection_ticks = 100  # 新手保护期
        self._broadcast_count: dict[str, int] = {}  # agent_id → 本 Tick 广播数

    def check(self, action: Decision, agent_state: AgentState, tick: int) -> CheckResult:
        """不可绕过的前置检查。返回 PASS / REJECT + reason"""

        # Check 1: 广播限流（防消息风暴）
        if action.action == DecisionAction.SEND_MESSAGE:
            if action.parameters.get("broadcast"):
                count = self._broadcast_count.get(agent_state.id, 0)
                if count >= self.broadcast_limit:
                    return CheckResult.reject("广播次数超限，防止消息风暴")

        # Check 2: 消息大小限制
        if action.action == DecisionAction.SEND_MESSAGE:
            content = action.parameters.get("content", "")
            if len(content) > self.message_size_limit:
                return CheckResult.reject(f"消息超过 {self.message_size_limit} 字符限制")

        # Check 3: 新手保护（R003 映射到 Agent 侧）
        if action.action == DecisionAction.PROPOSE_DEAL:
            target_spawn = action.parameters.get("target_spawn_tick", tick)
            if tick - target_spawn_tick < self.newbie_protection_ticks:
                return CheckResult.reject("目标 Agent 处于新手保护期")

        # Check 4: Token 余额二次校验（与 ActionExecutor 联动）
        if hasattr(action, 'estimated_cost'):
            if agent_state.tokens < action.estimated_cost:
                return CheckResult.reject("Token 不足以执行此操作")

        # Check 5: 死亡 Agent 不可操作
        if agent_state.phase in (AgentPhase.DYING, AgentPhase.DEAD):
            return CheckResult.reject("已死亡 Agent 不可执行操作")

        return CheckResult.pass_()

    def reset_tick(self):
        """每个 Tick 开始时重置计数器"""
        self._broadcast_count.clear()
```

**集成点**：
- 在 `think_loop.py` 的 `_act()` 方法中，`ActionExecutor.execute()` 调用前插入 `InterventionChecker.check()`
- 如果 REJECT，记录到 ActionResult 并跳过执行
- 不改 world-engine 的规则引擎（两者并行：agent-runtime 侧做前置拦截，world-engine 侧做后置判定）

**不做的事情**：
- 不做"可配置的安全策略"（硬编码 5 条规则足够 Phase 2）
- 不做"Agent 侧的 ed25519 签名校验"（由 A2A Server 端负责）
- 不做"沙箱执行环境"（Phase 3 的 tools/ 才需要）

---

## 5. 风险评估

### 5.1 过度借鉴风险

| 模式 | 风险等级 | 风险描述 | 缓解策略 |
|------|----------|----------|----------|
| Brain/Engine 分离 | **低** | LobeChat 是"用户意图 → 工具执行"，agent-world 是"Agent 决策 → 世界交互"，概念可映射 | 只借鉴"产出 Instruction"的理念，不照搬 Executor 接口 |
| InterventionChecker | **中** | LobeChat 的安全检查针对"LLM 生成有害内容"，agent-world 需要针对"Agent 破坏世界规则" | 以 agent-world 的 10 条规则为蓝本设计检查项，不照搬 LobeChat 的黑名单 |
| Hook 生命周期 | **低** | 通用模式，两个项目都需要"在执行流程的关键点插入自定义逻辑" | 直接借鉴，风险低 |
| **Context Engine Pipeline** | **高** | LobeChat 的上下文管理针对"对话历史"，agent-world 的上下文来源完全不同（世界状态 + 消息 + 记忆 + 生存） | **必须重新设计**——agent-world 的上下文不是"对话轮次"而是"多源异构数据" |
| GraphAgent | **高** | LobeChat 是"人在回路"的工具调用编排，agent-world 是"自治 Agent 的反应式决策" | 不借鉴。agent-world 用状态机 + 反应式决策，不用图编排 |
| Agent Tracing | **中** | LobeChat 的 Tracing 针对单次对话，agent-world 需要持续数万 Tick 的行为追踪 | 设计增量快照 + 采样策略，不照搬 LobeChat 的完整记录 |
| GroupOrchestration | **极高** | 中心化编排与"自治 Agent"理念根本冲突 | **不借鉴**。用 A2A 协议的去中心化协商替代 |

### 5.2 看起来有用但不适合的模式

#### 5.2.1 GraphAgent —— 不适合（P3 暂缓）

**表面上有用的原因**：Agent 需要执行多步任务（claim_task → execute → submit_task），看起来需要"图编排"。

**实际不适合的原因**：
1. **决策模式不匹配**：GraphAgent 是"规划式"的（先制定完整计划，再逐步执行），而 agent-world 的 Agent 是"反应式"的（每个 Tick 重新评估环境，做出最佳单步决策）。反应式决策更符合"生存沙盒"的设计理念——环境在持续变化，固定计划会失效。
2. **生存压力**：Agent 面临 Token 持续消耗的生存压力，不可能"先规划 10 步再执行"。每一步都要考虑当前 Token 余量和生存状态。
3. **技术栈不匹配**：GraphAgent 用 TypeScript 实现，agent-world 的 agent-runtime 是 Python。直接移植需要重写。

**替代方案**：用简单的"任务状态机"处理多步任务：
```python
# Agent 的任务跟踪（在 AgentState 中）
current_task: Task | None  # 当前持有的任务
task_step: str              # "claimed" → "executing" → "submitting"
```

#### 5.2.2 GroupOrchestrationSupervisor —— 不适合（P3 暂缓）

**表面上有用的原因**：Phase 2 目标是"10-100 Agent 形成社会关系"，看起来需要"编排"。

**实际不适合的原因**：
1. **与设计哲学冲突**：agent-world 的核心理念是"自治 Agent 在没有中心控制的情况下自组织"。加入中心化编排器违反了这一原则。
2. **LobeChat 的编排器是"人驱动的"**：用户选择调用哪个 Agent、决定任务分配。agent-world 没有"人类指挥官"角色。
3. **A2A 协议已内置协商**：PROPOSE → ACCEPT/REJECT 流程本身就是去中心化的任务协商机制。

**替代方案**：在 A2A 协议层实现"协议级编排"——通过扩展消息类型（如 `NEGOTIATE`、`DELEGATE`）支持多轮协商，而非引入中心编排器。

#### 5.2.3 Brain/Engine 分离的误区

**需要注意的风险**：LobeChat 的 Brain/Engine 分离是为了"让用户在不同 LLM 之间切换"，而 agent-world 的"分离"需求是为了"让 Agent 在不同执行环境下运行"（测试环境 vs 生产世界）。两者的抽象目标不同，不应照搬接口设计。

**正确的做法**：保持当前 `Decision` → `ActionExecutor` 的隐式分离，在需要时（Phase 2 后期）再显式化。不要过早抽象。

---

## 6. 总结：行动清单

### 立即行动（Phase 2 启动前）

| 序号 | 行动 | 预计时间 | 负责模块 |
|------|------|----------|----------|
| 1 | 实现 `ContextEngine`（记忆过滤 + Token 预算 + Prompt 动态构建） | 3 周 | `agent_runtime/context/` |
| 2 | 实现 `InterventionChecker`（5 项安全检查） | 2 周 | `agent_runtime/safety/` |

### Phase 2 中期

| 序号 | 行动 | 预计时间 | 负责模块 |
|------|------|----------|----------|
| 3 | 实现 Hook 生命周期（4 个钩子 + 基础埋点） | 2 周 | `agent_runtime/core/think_loop.py` |
| 4 | 实现 Agent Tracing（执行快照 + Dashboard 集成） | 2 周 | `agent_runtime/tracing/` + `dashboard/` |

### 不做的事情

| 模式 | 原因 | 替代方案 |
|------|------|----------|
| GraphAgent | Phase 2 不需要，反应式决策更适合生存沙盒 | 简单任务状态机 |
| GroupOrchestration | 与自治 Agent 理念冲突 | A2A 协议去中心化协商 |
| Brain/Engine 显式分离 | 当前隐式分离足够 | Phase 2 后期再评估 |

### 关键成功指标

| 指标 | Phase 2 目标 | Context Engine 的贡献 |
|------|-------------|----------------------|
| Agent 平均寿命 | > 500 Tick | Token 预算控制直接延长寿命 |
| 单次 LLM 调用 Token 消耗 | < 2000 token | Prompt 动态截断确保预算 |
| 消息风暴事件 | 0 次 | InterventionChecker 的广播限流 |
| Agent 异常行为定位时间 | < 5 分钟 | Tracing + Hook 埋点 |

---

## 核心结论

### P0 阻塞 Phase 2（必须做）

- **Context Engine Pipeline**（RICE 8.0）— 没有记忆预算控制，Agent 会在信息过载中快速耗尽 Token 死亡。这不是优化问题，是 Phase 2 能否运行的前提条件。
- **InterventionChecker**（RICE 5.4）— 没有 A2A 安全拦截，多 Agent 通信会导致消息风暴和资源耗尽。当前 world-engine 的规则是事后判定，需要在 agent-runtime 侧增加执行前拦截。

### P1 质量保障（应该做）

- **Hook 生命周期**（RICE 4.5）— 通过 Hook 插件化实现可观测性，避免在 think_loop 中硬编码埋点。`before_act` 的 mock 能力同时解决测试效率问题。
- **Agent Tracing**（RICE 3.2）— 执行快照支持异常行为回溯，是"Agent 为什么死亡了？"这个问题的唯一解法。

### 不建议借鉴

- **GraphAgent** — 生存沙盒更适合反应式决策（每 Tick 重新评估环境）而非规划式编排（先制定完整计划再执行）。用简单任务状态机替代。
- **GroupOrchestrationSupervisor** — 中心化编排与"自治 Agent 在没有中心控制的情况下自组织"的设计理念根本冲突。应走 A2A 协议的去中心化协商路线。
- **Brain/Engine 显式分离** — 当前 `Decision` → `ActionExecutor` 的隐式分离已够用，过早抽象增加复杂度无收益。Phase 2 后期再评估。

### 实施顺序

```
Sprint 1（并行）: Context Engine Pipeline + InterventionChecker
Sprint 2:         Hook 生命周期
Sprint 3:         Agent Tracing + Dashboard 集成
```

---

## 附录：RICE 评分原始数据

```
模式 1 - Brain/Engine 分离
  Reach: 3     (3 个 Phase 2 用户故事涉及)
  Impact: 1    (中等影响——测试效率提升)
  Confidence: 0.8 (估算较确定)
  Effort: 3    (3 周重构)
  RICE: 3 × 1 × 0.8 / 3 = 0.8

模式 2 - InterventionChecker
  Reach: 6     (6 个 Phase 2 用户故事涉及安全/稳定性)
  Impact: 2    (高影响——防止系统崩溃)
  Confidence: 0.9 (实现方案清晰)
  Effort: 2    (2 周)
  RICE: 6 × 2 × 0.9 / 2 = 5.4

模式 3 - Hook 生命周期
  Reach: 5     (5 个用户故事涉及可观测性/调试)
  Impact: 2    (高影响——可维护性)
  Confidence: 0.9 (通用模式，实现确定)
  Effort: 2    (2 周)
  RICE: 5 × 2 × 0.9 / 2 = 4.5

模式 4 - Context Engine Pipeline
  Reach: 8     (8 个 Phase 2 用户故事涉及记忆/决策/生存)
  Impact: 3    (巨大影响——决定 Agent 能否存活)
  Confidence: 1.0 (明确的技术方案)
  Effort: 3    (3 周)
  RICE: 8 × 3 × 1.0 / 3 = 8.0

模式 5 - GraphAgent
  Reach: 1     (1 个用户故事可能涉及多步任务)
  Impact: 0.5  (低影响——简单状态机可替代)
  Confidence: 0.5 (不确定是否真的需要)
  Effort: 6    (6 周，需要从 TypeScript 移植)
  RICE: 1 × 0.5 × 0.5 / 6 = 0.042

模式 6 - Agent Tracing
  Reach: 4     (4 个用户故事涉及调试/分析)
  Impact: 2    (高影响——调试效率)
  Confidence: 0.8 (方案清晰，但 Dashboard 集成有不确定性)
  Effort: 2    (2 周)
  RICE: 4 × 2 × 0.8 / 2 = 3.2

模式 7 - GroupOrchestration
  Reach: 2     (2 个用户故事涉及多 Agent 协作)
  Impact: 0.5  (低影响——A2A 协议可替代)
  Confidence: 0.5 (与设计哲学冲突，不确定性高)
  Effort: 4    (4 周)
  RICE: 2 × 0.5 × 0.5 / 4 = 0.125
```
