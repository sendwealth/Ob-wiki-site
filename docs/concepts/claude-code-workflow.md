---
title: Claude Code Workflow
created: 2026-05-29
updated: 2026-05-29
type: concept
tags: [ai, agent-orchestration, multi-agent, workflow-engine, claude-code]
sources:
  - https://codewithandrea.com/newsletter/january-2026/
  - https://maecapozzi.com/blog/building-a-multi-agent-orchestrator
  - https://github.com/steveyegge/gastown
  - https://howborisusesclaudecode.com/
confidence: high
---

# Claude Code Workflow

> Claude Code 的 Workflow 工具是一个确定性的多 agent 编排引擎，通过 JavaScript 脚本精确控制子 agent 的调度、并行执行、循环和结果汇总。区别于 Agent 工具的模型驱动调用，Workflow 用脚本实现确定性控制流，支持 pipeline、parallel、loop-until-dry 等模式，适用于代码审查、安全审计、大规模迁移等需要多维度并行处理的场景。

---

## 核心定位

Workflow 工具解决的核心问题：当任务需要**确定性控制流**（循环、条件分支、扇出/扇入）而非模型自主决策时，如何编排多个 AI agent。

| 维度 | Agent 工具 | Workflow 工具 |
|------|-----------|--------------|
| 控制流 | 模型驱动，非确定性 | 脚本驱动，确定性 |
| 适用场景 | 单一明确任务 | 多步骤、需循环/条件/扇出 |
| 并行度 | 有限 | 最高 16 并发 agent |
| 总量限制 | 无硬限制 | 1000 agent/workflow |
| 结果缓存 | 无 | 相同 prompt+opts 命中缓存 |
| 持久化 | 无 | 脚本自动保存，支持 resume |

**选择原则：** 需要循环、条件分支、扇出时用 Workflow；否则 Agent 更轻量。

---

## 脚本语法

Workflow 脚本是纯 JavaScript（非 TypeScript），以 `export const meta` 元数据开头：

```javascript
export const meta = {
  name: 'review-changes',
  description: 'Review changed files across dimensions',
  phases: [
    { title: 'Review', detail: 'parallel dimension review' },
    { title: 'Verify', detail: 'adversarial verification' },
  ],
}

// 脚本体使用 async/await
phase('Review')
const results = await pipeline(
  DIMENSIONS,
  d => agent(d.prompt, { label: `review:${d.key}`, phase: 'Review' }),
  review => parallel(review.findings.map(f => () =>
    agent(`Verify: ${f.title}`, { label: `verify:${f.file}`, phase: 'Verify' })
  ))
)
```

### 核心 API

| API | 用途 | 说明 |
|-----|------|------|
| `agent(prompt, opts)` | 生成子 agent | `opts.schema` 强制结构化输出；`opts.isolation: 'worktree'` 独立工作树 |
| `pipeline(items, stage1, stage2, ...)` | 流水线处理 | 每个 item 独立通过所有阶段，无阶段间屏障 |
| `parallel(thunks)` | 屏障同步 | 等待所有任务完成后返回，是真正的屏障 |
| `phase(title)` | 开始新阶段 | 后续 agent 调用归入该阶段（进度显示分组） |
| `log(message)` | 输出进度 | 向用户展示叙述性进度信息 |
| `workflow(name, args)` | 内联子工作流 | 嵌套调用另一个 workflow（仅一层） |
| `budget` | token 预算 | `budget.total`、`budget.spent()`、`budget.remaining()` |

### `agent()` 选项详解

```javascript
agent(prompt, {
  label: 'review:security',           // 显示标签
  phase: 'Review',                    // 阶段分组
  schema: FINDINGS_SCHEMA,            // JSON Schema 强制结构化输出
  model: 'sonnet',                    // 模型覆盖（通常省略）
  isolation: 'worktree',              // 独立 git worktree（~200-500ms 开销）
  agentType: 'code-reviewer',         // 自定义子 agent 类型
})
```

### 限制与约束

- **纯 JavaScript** — 类型注解、接口、泛型会解析失败
- **无 `Date.now()`/`Math.random()`** — 破坏 resume 缓存，通过 `args` 传入
- **无文件系统/Node.js API** — 所有 I/O 通过工具完成
- **嵌套限制** — `workflow()` 内不可再调用 `workflow()`
- **并发上限** — `min(16, cpu_cores - 2)` 并发 agent
- **总量上限** — 1000 agent / workflow 生命周期

---

## 五大编排模式

### 1. 对抗性验证（Adversarial Verify）

为每个发现生成 N 个独立审查者，要求**反驳**结论。≥majority 反驳则丢弃。

```javascript
const votes = await parallel(Array.from({length: 3}, () => () =>
  agent(`Try to refute: ${claim}. Default to refuted=true if uncertain.`, {
    schema: VERDICT_SCHEMA
  })
))
const survives = votes.filter(v => !v.refuted).length >= 2
```

**适用场景：** 安全审计、bug 确认 — 防止"看似合理但实际错误"的发现存活。

### 2. 评审团模式（Judge Panel）

从不同角度生成 N 个独立方案，评分后综合最佳方案并嫁接亚军亮点。

```javascript
const proposals = await parallel([
  () => agent('Design from MVP-first perspective', { schema: PROPOSAL }),
  () => agent('Design from risk-first perspective', { schema: PROPOSAL }),
  () => agent('Design from user-first perspective', { schema: PROPOSAL }),
])
const scored = await parallel(proposals.map(p => () =>
  agent(`Score proposal: ${p.summary}`, { schema: SCORE })
))
// 选出最佳方案，嫁接其他方案的亮点
```

**适用场景：** 架构设计、方案比选 — 解空间大时优于单次迭代。

### 3. 循环直到收敛（Loop-Until-Dry）

持续发现直到 K 轮无新发现。去重集合（`seen`）防收敛振荡。

```javascript
const seen = new Set(), confirmed = []
let dry = 0
while (dry < 2) {
  const found = await parallel(FINDERS.map(f => () =>
    agent(f.prompt, { phase: 'Find', schema: BUGS })
  ))
  const fresh = found.filter(b => !seen.has(key(b)))
  if (!fresh.length) { dry++; continue }
  dry = 0; fresh.forEach(b => seen.add(key(b)))
  // 验证 fresh findings...
}
```

**适用场景：** Bug 搜索、问题发现 — 未知规模时自动收敛。

### 4. 多模态扫描（Multi-Modal Sweep）

并行 agent 各用不同搜索维度（按容器、按内容、按实体、按时间），互补覆盖。

```javascript
const results = await parallel([
  () => agent('Search by container structure', { phase: 'Scan' }),
  () => agent('Search by content patterns', { phase: 'Scan' }),
  () => agent('Search by entity relationships', { phase: 'Scan' }),
  () => agent('Search by temporal changes', { phase: 'Scan' }),
])
```

**适用场景：** 全面审计、代码扫描 — 单一搜索维度遗漏时使用。

### 5. 完整性批评（Completeness Critic）

最终 agent 检查"遗漏了什么"（未运行的模态、未验证的声明、未读的源），触发下一轮补充。

**适用场景：** 深度研究后的质量门禁。

---

## Pipeline vs Parallel 选择

**`pipeline` 是默认选择。** 仅在以下情况使用 `parallel` 屏障：

1. 阶段 N 需要跨 item 合并/去重后才能继续
2. 早期退出条件依赖全量结果（如"0 bugs → 跳过验证"）
3. 阶段 N 的 prompt 需要引用其他 item 的结果

**反模式：**
```javascript
// ❌ 中间转换不需要屏障
const a = await parallel(items.map(i => fetch(i)))
const b = transform(a)
const c = await parallel(b.map(i => process(i)))

// ✅ 放入 pipeline 的阶段中
await pipeline(items, fetch, transform, process)
```

---

## 调用方式

```bash
# 内联脚本
claude> /workflow script="export const meta = { name: 'test', description: 'test' }; ..."

# 引用 .claude/workflows/ 下的命名 workflow
claude> /workflow name="review-changes"

# 通过脚本文件路径
claude> /workflow scriptPath="/path/to/workflow.js"
```

每次 Workflow 调用自动将脚本保存到会话目录，返回文件路径。迭代时用 `scriptPath` + `resumeFromRunId` 恢复。

---

## 实际应用案例

### Boris Cherny（Claude Code 创造者）的工作流

- 运行 **5 个并行 Claude 会话** + 5-10 个在 claude.ai
- 每个会话用独立的 git checkout（非 branch/worktree）
- 从 **Plan Mode** 开始，迭代后切换到 auto-accept
- 维护团队级 CLAUDE.md（~2.5K tokens）记录错误和最佳实践
- 使用 **PostToolUse hooks** 自动格式化
- 接受 10-20% 的会话会被放弃
- 核心理念："**给 Claude 一种验证自己工作的方法**"——测试、浏览器、模拟器

> 详见 [howborisusesclaudecode.com](https://howborisusesclaudecode.com/)

### Mae Capozzi — 6 阶段多 Agent 编排器

6 阶段流水线：Planning → Git Setup → Implementation → Testing → Review → PR Creation

关键设计决策：
- **阶段即恢复点** — 实现阶段失败时仍有干净的 worktree
- **进程隔离** — 每个 agent 独立进程 + 独立 worktree
- **Trace 传播** — 传递 `TRACEPARENT` 环境变量实现跨 agent 可观测性
- **协调者优先路由** — coordinator agent 决定调用哪个 specialist，而非硬编码

### Steve Yegge — Gas Town 编排系统

- Go 语言实现，协调 **20-30 个并行 Claude Code agent**
- 使用 tmux 管理会话
- 7 种 worker 角色
- 基于 [Beads](https://github.com/steveyegge/beads) 的 git 工作跟踪系统
- 成本：$100-200/hour API 费用

---

## AI 辅助编码成熟度模型

Steve Yegge 提出的 8 阶段模型：

| 阶段 | 描述 | 典型工具 |
|------|------|---------|
| 1-2 | 无/极少 AI（自动补全、侧栏聊天） | Copilot autocomplete |
| 3-5 | 单 agent，逐步增加信任和自动化 | Claude Code 单会话 |
| 6-7 | CLI 多 agent，手工管理（3-10+ 并行） | 多 terminal + worktree |
| **8** | **构建自己的编排器** | Workflow 工具 / Gas Town |

---

## Cache 与成本优化

Workflow 的缓存机制直接影响成本：

- **结果缓存：** 相同 (prompt, opts) 的 agent 调用自动命中缓存
- **Resume：** 编辑脚本后，未变更的前缀调用返回缓存结果
- **Cache TTL：** Anthropic prompt cache 有 5 分钟 TTL
  - < 5 分钟（60-270s）：cache 保持热
  - 5-60 分钟（300-3600s）：需付 cache miss 代价
  - 避免 300s — "两败"选择（cache miss 却没有分摊收益）

---

## 与相关概念的关系

- [[ecc]] — ECC 系统的 skills 和 agents 定义了 Workflow 可调用的子 agent 类型
- [[codegraph]] — Workflow 审查流程中可利用 CodeGraph 的结构化代码查询
- [[context-mode]] — 大规模 Workflow 的上下文压缩方案，减少 agent 间的 token 消耗
- [[a2a-protocol]] — Agent-to-Agent 协议定义了跨平台 agent 通信标准，与 Workflow 的编排层互补
- [[acp-protocol]] — Agent Client Protocol 定义了编辑器↔Agent 通信，Workflow 可通过 ACP 集成 IDE
- [[agentic-rag]] — Workflow 的 research 模式可结合 Agentic RAG 实现智能信息检索
