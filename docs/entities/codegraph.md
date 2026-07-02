---
title: CodeGraph — AI 编码助手的预索引代码知识图谱
created: 2026-05-18
updated: 2026-06-28
type: entity
tags: [ai-coding, agent, llm, product, project]
sources: [https://github.com/colbymchenry/codegraph]
confidence: high
---

# CodeGraph

> 为 Claude Code、Cursor、Codex、OpenCode 提供预索引代码知识图谱 — 更少 token、更少工具调用、100% 本地

*GitHub: colbymchenry/codegraph ⭐ 4.3k | License: MIT | Version: v0.7.9*

## Overview

当 AI 编码助手探索代码库时，会反复调用 grep/glob/read 扫描文件，每次消耗 token。CodeGraph 预先构建代码知识图谱，Agent 直接查询图谱获取符号关系、调用链、代码结构——**一次查询替代数十次文件扫描**。

实测平均 **92% 工具调用减少 · 71% 速度提升**。

## Key facts

- tree-sitter 解析 19+ 语言为 AST，提取节点（函数/类/方法）和边（调用/导入/继承）
- 本地 SQLite + FTS5 全文搜索，零外部依赖
- MCP Server 标准协议，支持 Claude Code / Cursor / Codex / OpenCode
- Framework 路由感知：自动识别 13 个 Web 框架路由→处理函数映射
- 原生 OS 文件事件监听，2 秒去抖增量同步
- 一键安装：`npx @colbymchenry/codegraph`

## Benchmark

| 项目 | 语言 | 用 CG | 不用 CG | 工具调用 ↓ | 速度 ↑ |
|------|------|-------|---------|-----------|--------|
| VS Code | TypeScript | 3 calls, 17s | 52 calls, 1m37s | 94% | 82% |
| Excalidraw | TypeScript | 3 calls, 29s | 47 calls, 1m45s | 94% | 72% |
| Claude Code 源码 | Python+Rust | 3 calls, 39s | 40 calls, 1m8s | 93% | 43% |
| Claude Code 源码 | Java | 1 call, 19s | 26 calls, 1m22s | 96% | 77% |
| Alamofire | Swift | 3 calls, 22s | 32 calls, 1m39s | 91% | 78% |
| Swift Compiler | Swift/C++ | 6 calls, 35s | 37 calls, 2m8s | 84% | 73% |

## 技术架构

```
AI Agent (Claude Code / Cursor / Codex / OpenCode)
         │
         ▼ MCP 协议
┌─────────────────────────┐
│   CodeGraph MCP Server  │
│  ┌───────┐ ┌─────────┐  │
│  │Search │ │Callers  │  │
│  └───┬───┘ └────┬────┘  │
│  ┌────┴─────────┴───┐   │
│  │   Context Build  │   │
│  └────────┬─────────┘   │
│           ▼              │
│  ┌─────────────────┐    │
│  │  SQLite + FTS5   │    │
│  │  .codegraph/db   │    │
│  └─────────────────┘    │
└─────────────────────────┘
         ▲
         │ tree-sitter AST 解析
    源代码文件监听 (FSEvents/inotify)
```

### 四阶段管线

1. **Extraction** — tree-sitter 解析源码为 AST，语言特定查询提取节点和边
2. **Storage** — 写入本地 SQLite + FTS5 全文搜索
3. **Resolution** — 解析引用关系：函数调用→定义、导入→源文件、类继承、框架路由
4. **Auto-Sync** — 原生 OS 文件事件监听，2 秒去抖，增量同步

## 支持的语言 (19+)

TypeScript, JavaScript, Python, Go, Rust, Java, C#, PHP, Ruby, C, C++, Swift, Kotlin, Dart, Svelte, Liquid, Pascal/Delphi

## Framework 路由感知

自动识别 13 个 Web 框架的路由，将 URL 模式关联到处理函数：

| 框架 | 识别模式 |
|------|---------|
| Django | `path()`, `re_path()`, `url()`, `include()` |
| Flask | `@app.route()`, Blueprint |
| FastAPI | `@app.get()`, `@router.post()`, 所有 HTTP 方法 |
| Express | `app.get()`, `router.post()` + middleware |
| Laravel | `Route::get()`, `Route::resource()`, Controller@action |
| Rails | `get '/x', to: 'users#index'` |
| Spring | `@GetMapping`, `@PostMapping`, `@RequestMapping` |
| Gin/chi/mux | `r.GET()`, `router.HandleFunc()` |
| Axum/actix/Rocket | `.route("/x", get(handler))` |
| ASP.NET | `[HttpGet("/x")]` |
| Vapor | `app.get("x", use: handler)` |
| React Router/SvelteKit | Route component nodes |

## 安装

```bash
# 一键安装（交互式，自动检测已装的 AI 工具）
npx @colbymchenry/codegraph

# 非交互式
codegraph install --yes                              # 全局
codegraph install --target=cursor,claude --yes       # 指定目标
codegraph install --target=auto --location=local     # 仅本地
codegraph install --print-config codex               # 只打印配置
```

| Flag | 值 | 默认 |
|------|---|------|
| `--target` | auto, all, none, csv (claude,cursor,...) | 交互 |
| `--location` | global, local | 交互 |
| `--yes` | boolean | 交互确认 |
| `--no-permissions` | boolean | 开启权限 |
| `--print-config <id>` | 打印指定 agent 配置 | — |

### 自动配置的文件

| 文件 | 用途 |
|------|------|
| `~/.claude.json` + `~/.claude/settings.json` | Claude Code MCP server |
| `~/.claude/CLAUDE.md` | Claude Code 指令 |
| `~/.cursor/mcp.json` | Cursor MCP server |
| `~/.codex/config.toml` + `~/.codex/AGENTS.md` | Codex CLI |
| `.cursor/rules/codegraph.mdc` | 项目级 Cursor 规则 |

### 项目初始化

```bash
cd your-project
codegraph init -i    # 交互式，构建索引 + 配置 agent surfaces
```

## CLI 参考

```bash
codegraph                         # 交互式安装器
codegraph install                 # 运行安装器
codegraph init [path]             # 初始化项目（--index 同时索引）
codegraph uninit [path]           # 移除（--force 跳过确认）
codegraph status [path]           # 查看索引状态
codegraph reindex [path]          # 重新索引
codegraph serve                   # 启动 MCP server
```

## 竞品对比

| 特性 | CodeGraph | [[graphify]] | CodeGraphContext |
|------|-----------|-------------|------------------|
| ⭐ Stars | 4.3k | 47.4k | 3.3k |
| 核心思路 | 预索引知识图谱 + MCP | 代码图谱可视化 | 图数据库 + MCP |
| 存储 | SQLite + FTS5 | 多种输出 | Neo4j/SurrealDB |
| AI 集成 | 4 种 Agent | 20+ 平台 | 通用 MCP |
| 路由感知 | ✅ 13 框架 | — | ❌ |

## agent-world 实测

在 [[agent-world]]（Rust + Python + Next.js）上安装测试：

| 指标 | 值 |
|------|---|
| 扫描文件 | 80 |
| 节点数 | 2,064 |
| 边数 | 5,308 |
| DB 大小 | 4.98 MB |
| 后端 | native |
| 索引时间 | ~1.9s |

语言分布：Python 44, Rust 20, TSX 11, TypeScript 5

节点类型：methods 889, functions 345, imports 310, classes 204

## 适用场景

- **大型代码库维护** — Agent 快速理解项目结构
- **跨模块重构** — 追踪调用链和影响范围
- **新成员上手** — AI 更准确回答架构问题
- **多语言项目** — Rust+Python+TS 混合项目特别适合

## 限制

- CLI 默认不在 PATH（通过 npx 运行或安装时选择添加）
- 仅静态分析，不追踪运行时依赖
- tree-sitter 对某些语法糖/宏可能不完整
- 首次索引大项目需要一定时间

See also: [[agent-world]], [[graphify]], [[gstack]], [[context-mode]]

## 最新动态（截至 2026-06-28）

> [!note] 爆发增长：94% 工具调用减少，登上 GitHub Trending
> CodeGraph 2026-05-20 登上 GitHub Trending，被实测能 **减少 94% 的 Claude Code 工具调用**（原调研记为 94%，部分来源称最高 49x token 节省）。与 [[graphify]] 形成"双子星"竞争。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| 曝光 | 新项目 | **GitHub Trending（2026-05-20）** |
| 实测效果 | 94% 工具调用减少 | 获社区独立验证（dev.to/Reddit/Medium 多篇）|
| 存储 | SQLite | 确认 **tree-sitter 解析 + 本地 SQLite** |
| 定位 | 预索引图谱 | **"Stop agent from grepping same files 50 times"**（新叙事）|

### 与 Graphify 的竞合
| 维度 | CodeGraph | [[graphify]] |
|------|-----------|-------------|
| 规模 | 较小 | 63.2K stars，77 contributors |
| 重点 | token/工具调用节省（94%）| 多模态（代码+文档+图片+视频）|
| 引擎 | tree-sitter + SQLite | tree-sitter + Leiden 聚类 |
| 路线 | 纯本地 CLI/MCP | CLI + 全局图谱 + Obsidian/wiki 导出 |

两者都属"代码知识图谱 for agents"品类，但 Graphify 更全能，CodeGraph 更聚焦"省 token"。

### 生态信号
- 学术界跟进：arXiv 出现《Codebase-Memory: Tree-Sitter-Based Knowledge Graphs for LLMs》论文，验证该范式
- 衍生品：code-graph-mcp（LobeHub）、SourceForge mirror 等，说明品类成立

### 仍待观察
- 与 Graphify 的市场份额分化
- 仅静态分析的局限（运行时依赖不追踪）
