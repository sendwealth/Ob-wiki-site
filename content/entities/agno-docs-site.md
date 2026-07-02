---
title: Agno Docs Site (agno-agi/docs)
created: 2026-05-28
updated: 2026-05-28
type: entity
tags: [ai, documentation, mintlify, open-source, agent, product]
sources:
  - https://github.com/agno-agi/docs
  - ~/Projects/agno-agi/docs source analysis
confidence: high
---

# Agno Docs Site

> Agno 官方文档站 `docs.agno.com` 的源码仓库。Mintlify 构建，3927 个 MDX 页面，7 个顶级导航 Tab，95+ 可复用 Snippet。覆盖 SDK、AgentOS、Deploy、Examples、Reference 五大产品模块。

---

## 基本信息

| 属性 | 值 |
|------|-----|
| 仓库 | `github.com/agno-agi/docs` |
| 构建工具 | Mintlify (`docs.json` 为导航源) |
| 页面格式 | `.mdx` (frontmatter: title, description) |
| 页面总量 | 3927 MDX + 8 MD + 2 JSON |
| CI | GitHub Actions (`.github/workflows/`) |
| 当前分支 | `main` (工作分支 `v2.6.0`) |
| 品牌色 | `#FF4017` (Agno 红) |
| 字体 | Inter (heading 750, body 400) |

## 导航架构 (7 Tabs)

```
docs.agno.com
├── Home          — 欢迎页、快速开始、特性概览、用例
├── SDK           — 核心开发文档 (Basics 11p + Advanced 12p + Production 5p + Providers 4p)
├── AgentOS       — 运行时管理平台 (18p 管理页 + 11p 示例)
├── Deploy        — 部署模板与接口 (4 Templates + 5 Solutions + 6 Interfaces)
├── Examples      — 可运行代码示例 (Primitives 3p + Context 4p + Models 8p + Tools 11p)
├── Reference     — API 与 CLI 参考 (SDK 16p + AgentOS API 22p + Infra CLI 7p)
└── FAQs          — 常见问题 (10p)
```

**总页面分布**：SDK 最重 (~44p)，AgentOS 次之 (~34p)，Reference 第三 (~45p)。

## 目录结构

```
agno-agi/docs/
├── docs.json          — Mintlify 配置 (导航、主题、品牌)
├── CLAUDE.md          — 文档风格指南 (AI 编辑用)
├── _snippets/         — 95+ 可复用片段
│   ├── db-*-params.mdx        — 数据库参数表
│   ├── embedder-*-reference.mdx — 嵌入模型参考
│   ├── vectordb_*_params.mdx  — 向量数据库参数
│   ├── chunking-*.mdx         — 分块策略
│   ├── *-reader-reference.mdx — 文档读取器参考
│   └── create-agent-infra-*.mdx — 部署代码模板
├── agent-platform/    — Agent 平台相关
├── background-execution/ — 后台执行
├── compression/       — 压缩
├── culture/           — 文化/价值观
├── demo-os/           — AgentOS 演示 (多 Agent 团队)
├── deploy/            — 部署文档 (infra/ templates/ interfaces/)
├── evals/             — 评估 (performance/ accuracy/ agent-as-judge/ reliability/)
├── faq/               — FAQ
├── hooks/             — 钩子
├── images/            — 图片资源
├── integrations/      — 集成 (testing/ governance/ memory/ discord/)
├── learning/          — 学习系统 (stores/)
├── models/            — 模型文档 (providers/)
├── multimodal/        — 多模态 (agent/ team/)
├── prompts/           — Prompt 工程
├── reference-api/     — API 参考 (schema/)
├── run-cancellation/  — 运行取消
├── scheduler/         — 调度器
├── skills/            — 技能系统
├── teams/             — 多 Agent 团队
├── tools/             — 工具系统 (toolkits/ usage/ reasoning_tools/ mcp/ creating-tools/)
└── public/            — 静态资源
```

## Snippet 系统

95+ 可复用片段是维护效率的关键。按类型分：

| 类型 | 数量 | 示例 |
|------|------|------|
| 数据库参数 | 18 | `db-postgres-params.mdx`, `db-mongodb-params.mdx` |
| 向量数据库参数 | 13 | `vectordb_pgvector_params.mdx`, `vectordb_qdrant_params.mdx` |
| 嵌入模型参考 | 12 | `embedder-openai-reference.mdx`, `embedder-gemini-reference.mdx` |
| 文档读取器 | 12 | `pdf-reader-reference.mdx`, `youtube-reader-reference.mdx` |
| 分块策略 | 8 | `chunking-semantic.mdx`, `chunking-fixed-size.mdx` |
| 部署代码模板 | 6 | `create-agent-infra-aws-codebase.mdx` |
| 其他 | 26 | `setup.mdx`, `set-openai-key.mdx`, `team-snippet.mdx` |

每个 Snippet 通过 Mintlify `<Snippet file="name.mdx">` 组件引用，避免跨页面重复。

## 写作风格 (CLAUDE.md)

文档遵循严格风格指南，核心原则：

1. **代码先行** — 先展示代码，再解释
2. **表格优于散文** — 对比/决策用表格
3. **不用破折号** — AI 痕迹检测规避
4. **不用逗号拼接** — 独立从句用句号
5. **砍掉评论** — 类比和评论浪费空间
6. **具体优于泛化** — "用 Claude Opus 4.5" 而非 "用更好的模型"
7. **Diátaxis 框架** — 每页只有一种类型 (Tutorial / How-to / Reference / Explanation)

## 技术架构

```
┌──────────────────────────────────────────────────┐
│                    docs.json                      │  ← 导航 + 主题 + 品牌
├──────────────────────────────────────────────────┤
│                    Mintlify                       │  ← 静态站点生成
├────────────┬────────────┬────────────────────────┤
│  .mdx 页面 │  _snippets/ │      images/          │  ← 内容层
│  (3927)    │  (95+)      │      (~50)             │
├────────────┴────────────┴────────────────────────┤
│               GitHub Actions                      │  ← CI/CD
└──────────────────────────────────────────────────┘
```

## 验证命令

```bash
mint dev              # 本地预览
mint broken-links     # 检查死链
mint build            # 构建检查
```

## 相关项目

| 项目 | 关系 |
|------|------|
| [[agno]] | 核心 SDK 仓库，文档描述其 API |
| [[agno-documentation-system]] | Agno 五层文档体系，本仓库是其中外部文档站层 |
| [[agno-demo-os]] | AgentOS 演示系统，文档中有对应章节 |

## 设计取舍

| 决策 | 原因 |
|------|------|
| Mintlify 而非 Docusaurus/VitePress | 文档专用，组件丰富（CardGroup、Steps、CodeGroup），维护成本低 |
| 3927 MDX 单文件 | 大量是 API 参考自动生成页；导航靠 `docs.json` 分层管理 |
| 95+ Snippet | 数据库/向量库参数表复用频繁，避免改一处漏多处 |
| CLAUDE.md 风格指南 | AI 辅助编辑时保持一致性，减少风格漂移 |
| 不用破折号规则 | 避免 "AI 生成文本" 的语言指纹 |

## Wikilinks

- [[agno]] — 核心 SDK
- [[agno-documentation-system]] — 完整文档体系
- [[agno-demo-os]] — AgentOS 演示
