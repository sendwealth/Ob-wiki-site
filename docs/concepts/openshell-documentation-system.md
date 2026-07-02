---
title: OpenShell 文档管理体系
created: 2026-05-27
updated: 2026-05-27
type: concept
tags: [documentation, open-source, practices, architecture, rust, fern, mdx]
sources:
  - ~/Projects/OpenShell/docs/ (源码)
  - ~/Projects/OpenShell/fern/ (Fern 配置)
  - https://docs.nvidia.com/openshell/latest/
confidence: high
---

# OpenShell 文档管理体系

> 基于 Fern v5.23 的文档站系统：`docs/` 为 MDX 内容源 + `fern/` 站点配置 + `docs/index.yml` 导航 + `architecture/` 内部设计文档。NVIDIA 品牌主题定制，PR 自动预览，release tag 触发发布。完整的写作风格指南 + markdownlint 校验 + agent 技能驱动更新。

---

## 1. 文档架构

```
OpenShell/
├── docs/                        # 内容源（Fern MDX）
│   ├── index.yml                # 顶级导航定义
│   ├── index.mdx                # 首页
│   ├── CONTRIBUTING.mdx         # 写作风格指南
│   ├── .markdownlint-cli2.jsonc # Markdown lint 规则
│   ├── _components/
│   │   └── BadgeLinks.tsx       # 徽章链接组件
│   ├── about/                   # 产品介绍（overview, installation, release-notes）
│   ├── get-started/             # 快速上手 + 教程
│   │   └── tutorials/           # 6 个教程（network-policy, ollama, lmstudio 等）
│   ├── sandboxes/               # 沙箱管理（policy, providers, gateways, inference）
│   ├── observability/           # 可观测性（logging, ocsf-json-export）
│   ├── kubernetes/              # K8s 部署（setup, ingress, certificates, openshift）
│   ├── reference/               # 参考（policy-schema, gateway-config, support-matrix）
│   ├── security/                # 安全最佳实践
│   └── resources/               # 许可证等资源
├── fern/                        # Fern 站点配置
│   ├── fern.config.json         # org + version
│   ├── docs.yml                 # 站点完整配置（域名、主题、重定向、组件）
│   ├── main.css                 # 全局样式（NVIDIA 品牌色、暗色模式、footer）
│   ├── components/
│   │   └── CustomFooter.tsx     # NVIDIA 品牌页脚
│   └── assets/                  # logo、架构图、截图
├── architecture/                # 内部架构文档（开发者参考，不发布）
│   ├── README.md                # 架构索引
│   ├── gateway.md
│   ├── sandbox.md
│   ├── security-policy.md
│   ├── compute-runtimes.md
│   └── build.md
└── .agents/skills/              # Agent 技能
    └── update-docs/             # 文档更新自动化技能
```

## 2. 技术栈

| 组件 | 技术 |
|------|------|
| 文档框架 | [Fern](https://buildwithfern.com) v5.23.3 |
| 内容格式 | Fern MDX（支持 React 组件） |
| 站点配置 | `fern/docs.yml` + `fern/fern.config.json` |
| 导航定义 | `docs/index.yml`（声明式 YAML） |
| 主题 | NVIDIA 品牌定制（`#76B900` 强调色、暗色/亮色双模式） |
| 本地预览 | `mise run docs:serve` → `fern docs dev` |
| 非交互校验 | `mise run docs:check` → `fern check` |
| Lint | `.markdownlint-cli2.jsonc` |
| 生产域名 | `docs.nvidia.com/openshell` |

## 3. Fern 站点配置详解

### 核心配置 (`fern/docs.yml`)

| 配置项 | 值 |
|--------|-----|
| organization | nvidia |
| 实例 URL | `openshell.docs.buildwithfern.com/openshell` |
| 自定义域名 | `docs.nvidia.com/openshell` |
| 页面宽度 | 1376px / sidebar 248px / content 812px |
| 搜索栏 | header 位置 |
| Logo | NVIDIA SVG（亮/暗双版本） |
| 页脚 | `CustomFooter.tsx`（NVIDIA 品牌页脚 + "Built with Fern"） |
| 版本 | 单版本 `Latest`，指向 `../docs/index.yml` |

### 重定向策略

维护了一组 URL 重定向规则：
- 旧版 `index.html` 后缀 → 去掉后缀
- `tutorials/` 路径 → 迁移至 `get-started/tutorials/`
- 支持 `:path*` 通配符匹配

### 实验性特性

```yaml
experimental:
  mdx-components:
    - ../docs/_components      # docs/ 中的 React 组件对 Fern 可见
  basepath-aware: true          # 内部链接自动适配 /openshell/ 前缀
```

## 4. 导航结构

`docs/index.yml` 定义顶级导航，支持三种条目类型：

```yaml
navigation:
- folder: about                  # 文件夹自动发现
  title: "About NVIDIA OpenShell"
- section: "Get Started"         # 显式 section + 手动内容
  slug: get-started
  contents:
  - page: "Quickstart"
    path: get-started/quickstart.mdx
  - folder: get-started/tutorials  # 嵌套文件夹
    skip-slug: true
- folder: sandboxes              # 每个文件夹对应一个侧边栏分组
- folder: observability
- folder: kubernetes
- folder: reference
- folder: security
- folder: resources
```

**7 个顶级分区**：About、Get Started、Sandboxes、Observability、Kubernetes、Reference、Security。

## 5. 写作风格指南

### 核心原则

| 原则 | 规则 |
|------|------|
| **主动语态** | "The CLI creates a gateway" 不写 "A gateway is created" |
| **第二人称** | 用 "you" 称呼读者 |
| **现在时** | "The command returns" 不写 "will return" |
| **不用犹豫词** | 禁止 "simply"、"just"、"easily"、"of course" |
| **每个句子以句号结尾** | 无例外 |

### 格式规则

- CLI 命令、文件路径、参数名用 `` `code` `` 格式
- 可复制的 CLI 示例用 ` ```shell ` 围栏，不加 `$` 前缀
- 日志/输出用 ` ```text ` 围栏
- 使用 Fern 组件 `<Note>`、`<Tip>`、`<Warning>` 做标注，不用粗体
- 标题不加编号、不加冒号
- 表格用于结构化对比，保持简单

### 页面 Frontmatter 模板

```yaml
---
# SPDX-FileCopyrightText: Copyright (c) 2025-2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0
title: "Page Title"
sidebar-title: "Short Nav Title"
description: "One-sentence summary of the page."
keywords: "Generative AI, Cybersecurity, AI Agents, Sandboxing"
---
```

关键规则：
- `title` → 页面标题 + 浏览器标题
- `sidebar-title` → 侧边栏短标题
- `page:` in `index.yml` 应与 `sidebar-title` 一致（有则用，无则用 `title`）
- 不在 body 中重复 H1（Fern 从 frontmatter 渲染标题）
- `position` 控制排序，`slug` 覆盖 URL

## 6. CI/CD 流水线

### PR 预览 (`branch-docs.yml`)

```
PR 触发条件: docs/**, fern/**, mise.toml, tasks/docs.toml
    │
    ├─ 检查 FERN_TOKEN 是否可用
    ├─ Node.js 24 + Fern CLI 安装
    ├─ fern check（校验配置 + 链接）
    ├─ fern generate --docs --preview（生成预览，需要 FERN_TOKEN）
    └─ 在 PR 评论中发布预览 URL
```

**注意**：Fork PR 没有 `FERN_TOKEN`，跳过预览但仍然运行 `fern check` 校验。

### 生产发布 (`release-tag.yml`)

```
触发条件: git tag v*.*.* 或 workflow_dispatch
    │
    └─ publish-fern-docs job: 发布到 docs.nvidia.com/openshell
```

## 7. 三层文档体系

OpenShell 维护三个不同目标受众的文档层：

| 层级 | 位置 | 受众 | 特点 |
|------|------|------|------|
| **发布文档** | `docs/` | 终端用户 + 运维 | MDX、Fern 构建、公开网站 |
| **架构文档** | `architecture/` | 贡献者 + 开发者 | 短小精干的子系统概览，不发布 |
| **Crate README** | `crates/*/README.md` | 深入该 crate 的开发者 | 实现细节，与代码同目录 |

### 架构文档原则

- 短小精干的子系统概览，不是详尽实现笔记
- 先更新现有架构文档，再考虑新增文件
- 仅在 RFC 级设计需要稳定存档时新建顶级文档
- 关注：稳定边界、数据/控制流、不变量、运维约束
- 删除过时细节，而非默认保留
- 临时计划放在 gitignored `architecture/plans/`

### `rfc/` vs `architecture/`

- `rfc/` 用于讨论中的设计提案
- RFC 被采纳后，关键细节回写到 `architecture/`
- `architecture/` 是设计的规范参考

## 8. Agent 技能驱动更新

项目使用 `update-docs` 技能自动化文档更新：

```
update-docs 技能工作流：
  1. 扫描最近 commits
  2. 识别受影响的文档页面
  3. 按照 CONTRIBUTING.mdx 风格指南起草内容
  4. 更新 docs/index.yml 导航（如需）
```

这是项目 "agent-first" 理念的体现：不仅产品为 Agent 服务，开发流程也由 Agent 技能驱动。

## 9. 设计亮点

| 亮点 | 说明 |
|------|------|
| **内容与配置分离** | `docs/` 纯内容，`fern/` 纯配置，职责清晰 |
| **Basepath-aware** | 内部链接写 `/latest/...`，生产自动加 `/openshell/` 前缀 |
| **MDX 组件扩展** | React 组件（BadgeLinks、CustomFooter）增强页面表现力 |
| **重定向管理** | 旧 URL 全覆盖，SEO 友好 |
| **Fork PR 友好** | 无 token 时降级为仅校验，不阻塞外部贡献 |
| **三层分离** | 发布文档 / 架构文档 / Crate README 各有定位 |
| **Agent 自动化** | `update-docs` 技能扫描 commit 并起草文档更新 |
| **NVIDIA 品牌一致** | 自定义 CSS + 页脚 + Logo，亮暗双主题 |

## 10. 与其他项目对比

| 维度 | OpenShell | [[zed-documentation-system]] | [[orloj-documentation-system]] |
|------|-----------|-----|-------|
| 框架 | Fern (SaaS) | mdBook (Rust) | Vocs (Vite) |
| 内容格式 | MDX | Markdown | Markdown |
| 品牌定制 | 深（CSS + 组件 + 品牌色） | 中（Rust 预处理器） | 浅（Vite 主题） |
| 自动化 | Agent 技能 | Rust 预处理器 | OpenAPI 自动生成 |
| 预览 | PR 预览 URL | 本地 mdBook serve | 本地 vocs dev |
| 导航 | YAML 声明式 | SUMMARY.md | vocs.config.ts |
| 架构文档 | 分离的 `architecture/` | 嵌入 docs/src | 分离的 `docs/` |
| 特色 | basepath-aware + 重定向 | 键绑定自动展开 + 声音评分卡 | CRD 按资源分组 |

## 相关链接

- [[openshell]] — OpenShell 项目整体实体页
- [[zed-documentation-system]] — Zed 文档体系（mdBook + 声音评分卡）
- [[orloj-documentation-system]] — Orloj 文档体系（Vocs + OpenAPI 驱动）
- 生产站点：https://docs.nvidia.com/openshell/latest/
