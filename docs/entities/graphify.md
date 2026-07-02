---
title: Graphify — 代码知识图谱生成器
created: 2026-05-13
updated: 2026-06-28
type: entity
tags: [ai-coding, knowledge-graph, code-analysis, graphrag, tree-sitter]
sources: [raw/graphify/readme.md]
confidence: high
---

# Graphify

> 47.4K⭐ | 一行命令将代码库转为可查询知识图谱，支持 20+ AI 编码平台

*GitHub: https://github.com/safishamsi/graphify | Author: Safi Shamsi | Language: Python | License: MIT*

## Overview

Graphify 是一个 AI 编码助手技能，将任意代码文件夹（代码、SQL schema、R 脚本、Shell、文档、论文、图片、视频）转换为可查询的知识图谱。应用代码 + 数据库 schema + 基础设施在一个图谱中。

**数据**: 47,444 ⭐ | 5,146 forks | Python | 2026-04-03 创建

**核心体验**: `/graphify .` → 3 个文件（graph.html + GRAPH_REPORT.md + graph.json）

## Key facts

- 支持 29 种编程语言（tree-sitter AST 解析，零 API 调用）
- 支持 20+ AI 编码平台（Claude Code、Codex、Cursor、Gemini CLI、OpenClaw、Aider 等）
- 代码本地解析（隐私安全），文档/图片/PDF 走 LLM API
- Leiden 社区检测 + 置信度评分（EXTRACTED / INFERRED / AMBIGUOUS）
- MCP 服务器模式：`graphify serve` 暴露 query_graph / get_node / get_neighbors / shortest_path
- 递增更新：`--update` 只重新提取变更文件
- 团队协作：graphify-out/ 提交到 git，merge driver 自动合并并行图谱

## 安装

```bash
# 推荐
uv tool install graphifyy && graphify install

# 或
pipx install graphifyy && graphify install

# OpenClaw
graphify install --platform claw
graphify claw install    # 持久化配置
```

> PyPI 包名是 `graphifyy`（双 y），CLI 命令是 `graphify`

## 工作流程

### 1. 构建图谱
```bash
/graphify .                       # 当前目录
/graphify ./docs --update         # 递增更新
/graphify . --cluster-only        # 只重跑聚类
/graphify . --wiki                # 生成 Markdown wiki
/graphify . --obsidian            # 生成 Obsidian vault
/graphify . --directed            # 保留边方向
```

### 2. 查询图谱
```bash
/graphify query "what connects auth to the database?"
/graphify path "UserService" "DatabasePool"
/graphify explain "RateLimiter"
```

### 3. 导出
```bash
graphify export callflow-html     # 架构/调用流 HTML
graphify export callflow-html --output docs/arch.html
/graphify . --svg                 # SVG 导出
/graphify . --graphml             # Gephi / yEd
/graphify . --neo4j               # Neo4j cypher
```

### 4. MCP 服务器
```bash
python -m graphify.serve graphify-out/graph.json
# 提供: query_graph, get_node, get_neighbors, shortest_path
```

## 支持的文件类型

| 类型 | 扩展名 | 处理方式 |
|------|--------|----------|
| 代码（29 语言） | .py .ts .js .go .rs .java .c .cpp .rb .cs .kt .php .swift 等 | tree-sitter AST 本地解析 |
| 文档 | .md .mdx .html .txt .rst .yaml | LLM 语义提取 |
| PDF | .pdf | LLM |
| 图片 | .png .jpg .webp .gif | LLM |
| 视频/音频 | .mp4 .mov .mp3 .wav | faster-whisper 本地转录 |
| Office | .docx .xlsx | LLM（需 `graphifyy[office]`） |
| YouTube/URL | 视频链接 | 转录 + 添加 |

## 报告内容

- **God nodes** — 连接最多的概念
- **Surprising connections** — 跨文件/模块的意外关联
- **The "why"** — `# NOTE:`, `# WHY:`, `# HACK:` 注释和设计理念
- **Suggested questions** — 图谱能独特回答的 4-5 个问题
- **Confidence tags** — 每个关系标记为 EXTRACTED / INFERRED / AMBIGUOUS

## 全局图谱

跨项目关联：
```bash
graphify extract ./docs --global --as myrepo
graphify global add graphify-out/graph.json myrepo
graphify global list
```

## 与 Garry Tan 项目的对比

| | Graphify | [[gbrain]] |
|---|----------|-----------|
| **定位** | 代码知识图谱生成器 | Agent 长期记忆系统 |
| **输入** | 代码文件、文档、媒体 | 会议、邮件、推文、语音 |
| **图谱** | 代码调用关系 + 概念关联 | 人物/公司/事件关系 |
| **查询** | `/graphify query` | `gbrain query` |
| **平台** | 20+ AI 编码助手 | OpenClaw / Hermes |

| | Graphify | [[gstack]] |
|---|----------|-----------|
| **定位** | 代码理解工具 | 软件工厂工作流 |
| **关系** | Graphify 理解代码结构 | gstack 管理开发流程 |
| **互补** | `/investigate` 可用 Graphify 图谱 | Graphify 不涉及发布/测试 |

## 最新动态（截至 2026-06-28）

> [!note] 持续爆发：star 数从 47K 涨到 63.2K，日均发版
> Graphify v0.8.35（2026-06-07）发布时已达 **63.2K stars / 77 contributors**，保持约一天一个 release 的节奏。PyPI 累计 250K+ 下载。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| Star | 47.4K | **63.2K**（+33%）|
| 版本 | 早期 | **v0.8.35**（2026-06-07）|
| 贡献者 | 少量 | **77 人** |
| 平台 | 20+ AI 编码平台 | 原生集成 10+ AI 编码平台 |

### 生态扩展
- **官方独立站点**：上线 [graphify.net](https://graphify.net/)，从 GitHub 项目升级为独立品牌
- **OpenClaw 深度集成**：2026-04 后成为 OpenClaw 生态的代码理解标配
- **衍生对比项目**：社区出现 **code-review-graph (CRG)**（embedding-aware 语义搜索 + MCP），与 Graphify 形成"结构图谱 vs 语义图谱"的互补组合

### 定位演进
原调研强调"代码知识图谱生成器"，2026 年叙事转向 **"Navigate codebase by structure, not similarity"**（按结构而非相似度导航）——这是对传统 RAG 语义检索的明确挑战。

### 仍待观察
- 每日发版节奏的稳定性与质量把控
- 无内置持久记忆的短板是否会被 CRG 类项目补上

## Counter-arguments & data gaps

- 新项目（2026-04-03 创建），成熟度待观察
- 非代码文件需要 LLM API 调用（成本+延迟）
- 大型代码库图谱可能很复杂
- 依赖 tree-sitter 对新语言支持可能有延迟
- 无内置持久记忆（每次构建图谱，不像 gbrain 有增量记忆）

See also: [[gbrain]], [[gstack]], [[ruflo]], [[agentic-rag]]
