---
title: Context Mode
created: 2026-05-11
updated: 2026-05-11
type: concept
tags: [ai, agent, context-window, mcp, coding-tool, llm]
sources: [https://github.com/mksglu/context-mode]
confidence: high
---

# Context Mode

> 概括：MCP Server 解决 AI 编码 Agent 上下文窗口浪费问题。通过 Sandbox 隔离工具输出实现 98% 压缩，用 SQLite+FTS5 追踪会话事件实现压缩后精确恢复。支持 15 个平台，完全本地运行。

---

## 核心问题

AI 编码 Agent 每次工具调用（MCP tool call）都向上下文窗口灌入大量原始数据：
- Playwright snapshot: 56 KB
- 20 个 GitHub Issues: 59 KB
- 一份 access log: 45 KB
- 30 分钟后 40% 上下文消失
- Agent 压缩对话时丢失编辑文件、进行中任务、上次请求

## 四大解决方案

### 1. Context Saving — Sandbox 隔离
原始数据不进入上下文窗口。**315 KB → 5.4 KB，压缩 98%**。

| 场景 | 原始 | 压缩后 | 节省 |
|---|---|---|---|
| Playwright snapshot | 56.2 KB | 299 B | 99% |
| GitHub Issues (20) | 58.9 KB | 1.1 KB | 98% |
| Access log (500行) | 45.1 KB | 155 B | 100% |
| Git log (153 commits) | 11.6 KB | 107 B | 99% |
| Repo research | 986 KB | 62 KB | 94% |

### 2. Session Continuity — 会话连续性
- 文件编辑、git 操作、任务、错误、用户决策全部记录到 SQLite
- 对话压缩时通过 FTS5 + BM25 搜索只检索相关内容
- 模型从上次中断处精确恢复
- 5 个 Hook 协同: `PreToolUse` → `PostToolUse` → `UserPromptSubmit` → `PreCompact` → `SessionStart`
- 事件按优先级捕获: P1(文件/任务/规则) → P2(git/错误/约束) → P3(延迟/MCP) → P4(意图/数据)

### 3. Think in Code — 用代码思考
LLM 生成分析脚本，不自己处理数据。1 个脚本代替 10 次工具调用。

```js
// 47 × Read() = 700 KB  →  1 × ctx_execute() = 3.6 KB
ctx_execute("javascript", `
  const files = fs.readdirSync('src').filter(f => f.endsWith('.ts'));
  files.forEach(f => console.log(f + ': ' + fs.readFileSync('src/'+f,'utf8').split('\n').length));
`);
```

### 4. 不干预输出风格
只控制数据流向，不控制模型如何回答。研究表明强制简洁提示会降低编码/推理能力（参考 Moonshot AI kimi-k2.5）。

## 核心 MCP 工具（11 个）

| 工具 | 功能 | 压缩效果 |
|---|---|---|
| `ctx_batch_execute` | 一次调用多命令+多搜索，并发1-8 | 986 KB → 62 KB |
| `ctx_execute` | 11 种语言运行代码，仅 stdout 进入上下文 | 56 KB → 299 B |
| `ctx_execute_file` | Sandbox 中处理文件 | 45 KB → 155 B |
| `ctx_index` | Markdown 分块存入 FTS5 + BM25 | 60 KB → 40 B |
| `ctx_search` | 查询已索引内容 | 按需检索 |
| `ctx_fetch_and_index` | 抓取 URL→转 MD→分块索引，24h TTL 缓存 | 60 KB → 40 B |
| `ctx_stats` | 上下文节省统计 | — |
| `ctx_doctor` | 诊断安装状态 | — |
| `ctx_upgrade` | GitHub 升级 | — |
| `ctx_purge` | 清除所有索引 | — |
| `ctx_insight` | 个人分析面板（90 指标） | — |

## 知识库技术

- **存储**: SQLite FTS5 全文搜索
- **排序**: BM25 + Porter 词干提取 + 标题 5x 加权
- **搜索融合**: Reciprocal Rank Fusion (RRF) 合并 Porter stemming + Trigram substring
- **近邻重排**: 多词查询中词距近的结果排名更高
- **模糊纠错**: Levenshtein 距离纠正拼写
- **智能摘要**: 围绕查询词提取窗口，非截断
- **自动选择后端**: Bun→`bun:sqlite`, Node>=22.13→`node:sqlite`, 其他→`better-sqlite3`

## 支持平台（15 个）

| 平台 | Hooks | 会话连续性 | 路由合规 |
|---|---|---|---|
| Claude Code | 全 5 种 | Full | ~98% |
| Qwen Code | Yes | Full | ~98% |
| Gemini CLI | 4 种 | High | ~98% |
| VS Code Copilot | 3 种 | High | ~98% |
| JetBrains Copilot | 3 种 | High | ~98% |
| Cursor | 2 种 | Partial | ~98% |
| OpenCode / KiloCode | Plugin | Full | ~98% |
| Codex CLI | Yes | Partial | ~98% |
| Antigravity / Zed | — | — | ~60% |
| Kiro | 2 种 | Partial | ~98% |
| Pi / OMP | Extension/Plugin | High | ~98% |

无 hooks 的平台（Zed、Antigravity）仅靠指令文件 ~60% 合规。

## 安全与隐私

- 继承已有 deny/allow 权限规则，扩展到 sandbox
- `ctx_fetch_and_index` 默认阻止危险 URL（file://, 云元数据 169.254.x.x, 多播）
- 敏感字段（token, secret, password）自动脱敏为 `[REDACTED]`
- **完全本地**: 无遥测、无云同步、无账户
- License: Elastic License 2.0（防闭源 SaaS 包装）

## 关联

- [[agentic-rag]] — Agentic RAG 也涉及 LLM 如何高效利用外部信息
- [[heuristic-learning]] — coding agent 学习范式，context-mode 直接优化 coding agent 效率
