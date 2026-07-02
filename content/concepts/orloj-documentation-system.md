---
title: Orloj 文档管理体系
created: 2026-05-25
updated: 2026-05-25
type: concept
tags: [ai, documentation, open-source, knowledge-management]
sources:
  - ~/Projects/orloj/docs/ (源码)
  - https://docs.orloj.dev
confidence: high
---

# Orloj 文档管理体系

> 基于 Vocs（VitePress 替代品）的文档站，5 大顶级导航 + 50+ 页面覆盖 Getting Started / Concepts / Guides / Deploy & Operate / Reference 全链路，API 文档由 OpenAPI 3.1 规范驱动，CLI 参考自动生成，资源参考按 CRD 分组。

---

## 文档站点技术栈

| 组件 | 技术 |
|------|------|
| 框架 | [Vocs](https://vocs.dev) v1.4.1（基于 Vite 的文档站框架） |
| 语言 | TypeScript 配置 + Markdown 内容 |
| 构建 | `vocs dev` / `vocs build` / `vocs preview` |
| 部署 | 环境变量控制 `VOCS_BASE_URL` + `VOCS_BASE_PATH` |
| API 参考 | OpenAPI 3.1 + Redocly CLI lint |
| 站点名 | "Orloj Docs" |

## 站点架构

```
docs/
├── vocs.config.ts          # 站点配置（导航、侧边栏、主题）
├── package.json            # vocs 依赖
├── pages/                  # 所有文档内容（Markdown）
│   ├── index.md            # 首页 "What is Orloj?"
│   ├── getting-started/    # 安装、快速上手、核心概念
│   ├── concepts/           # 架构、Agent、Task、Tool、治理、记忆、A2A
│   ├── guides/             # 教程和操作指南（13 篇）
│   ├── deploy/             # 部署：本地、VPS、K8s、远程 CLI
│   ├── operations/         # 运维：配置、Runbook、安全、升级、排错、可观测
│   └── reference/          # 参考：CLI、API、A2A JSON-RPC、资源 schema
├── design/                 # 设计文档（部署参考配置）
│   ├── kubernetes/         # K8s YAML 参考
│   └── vps/                # Docker Compose + systemd 参考
└── public/                 # 静态资源
    ├── favicon.png
    └── readme/             # README 截图和 GIF
```

## 导航结构（5 个顶级入口）

### Top Nav

| 导航项 | 链接 |
|--------|------|
| Getting Started | `/getting-started/install` |
| Concepts | `/concepts/architecture` |
| Guides | `/guides/` |
| Deploy & Operate | `/deploy/` |
| Reference | `/reference/cli` |

### Sidebar 完整树

```
├── What is Orloj? (/)
├── Getting Started
│   ├── Install
│   ├── Quickstart
│   └── Core Concepts
├── Concepts
│   ├── Architecture
│   ├── Execution Model
│   ├── Agents
│   │   ├── Agent
│   │   └── AgentSystem
│   ├── Tasks
│   │   ├── Task
│   │   ├── TaskSchedule
│   │   └── TaskWebhook
│   ├── Tools
│   │   ├── Orloj Tools (内置)
│   │   ├── Custom Tool
│   │   ├── CLI Tool
│   │   ├── MCP Server
│   │   ├── Model Endpoint
│   │   └── Secret
│   ├── Memory
│   │   ├── Overview
│   │   └── Providers
│   ├── Governance
│   │   ├── Overview
│   │   ├── AgentPolicy
│   │   ├── AgentRole
│   │   ├── ToolPermission
│   │   ├── ToolApproval
│   │   └── TaskApproval
│   ├── Evaluation
│   ├── Worker
│   └── A2A Interoperability
├── Guides (13 篇)
│   ├── 5-Minute Tutorial
│   ├── Deploy Your First Pipeline
│   ├── Set Up Multi-Agent Governance
│   ├── Configure Model Routing
│   ├── Human Review Checkpoints
│   ├── Connect an MCP Server
│   ├── Build a Custom Tool
│   ├── Build a WASM Tool
│   ├── Run Agent Evaluation
│   ├── Starter Blueprints
│   ├── Expose Agents via A2A
│   ├── Use Remote A2A Agents
│   └── kubectl vs orlojctl
├── Deploy & Operate
│   ├── Deployment
│   │   ├── Local Development
│   │   ├── VPS
│   │   ├── Kubernetes
│   │   └── Remote CLI & API Access
│   ├── Day-to-Day
│   │   ├── Configuration
│   │   ├── Runbook
│   │   ├── Security
│   │   ├── Upgrades & Rollbacks
│   │   ├── Task Scheduling (Cron)
│   │   ├── Webhook Triggers
│   │   └── Troubleshooting
│   └── Observability
│       ├── Overview
│       ├── Monitoring & Alerts
│       └── Backup & Restore
└── Reference
    ├── CLI (orlojctl)
    ├── API
    ├── A2A JSON-RPC
    ├── Server Flags
    ├── Internal Tools
    └── Resources（按 CRD 分组）
        ├── Agents: Agent / AgentSystem / Agent Card
        ├── Tasks: Task / TaskSchedule / TaskWebhook
        ├── Tools & Models: Tool / ModelEndpoint / McpServer
        ├── Governance: AgentPolicy / AgentRole / ToolPermission / ToolApproval / TaskApproval
        ├── Infrastructure: Worker
        ├── Evaluation: EvalDataset / EvalRun
        ├── Memory: Memory
        └── Secrets: Secret / SealedSecret
```

## 内容组织模式

### 文档类型分层

| 类型 | 位置 | 用途 | 典型读者 |
|------|------|------|----------|
| 入口 | `pages/index.md` | 产品介绍、核心价值、快速导航 | 新访客 |
| Getting Started | `pages/getting-started/` | 安装、5 分钟上手、概念速览 | 评估用户 |
| Concepts | `pages/concepts/` | 架构设计、资源模型、机制说明 | 开发者/架构师 |
| Guides | `pages/guides/` | 步骤式教程（如何做 X） | 实践者 |
| Deploy | `pages/deploy/` + `design/` | 部署方案 + 参考配置 | 运维 |
| Operations | `pages/operations/` | 日常运维手册 | SRE/DevOps |
| Reference | `pages/reference/` | CLI/API/协议/资源 schema | 所有人 |

### Guide 设计特点

- **渐进式**：从 5 分钟教程到 WASM 工具开发
- **场景驱动**：每个 Guide 解决一个具体场景
- **含代码示例**：YAML 片段 + CLI 命令 + 输出示例
- **交叉链接**：Guide 之间相互引用，不重复

### Concept 页面模式

每个 Concept 页面遵循：

1. 一句话定义
2. 为什么需要它
3. 工作原理（带 ASCII 流程图）
4. 资源 schema 关键字段
5. 与其他资源的关系
6. 常见配置示例

## API 文档策略

| 文档类型 | 来源 | 工具 |
|----------|------|------|
| OpenAPI 3.1 Spec | `openapi/openapi.yaml` + `openapi/schemas/` | 手写 + Redocly CLI lint |
| A2A JSON-RPC | `pages/reference/a2a-jsonrpc.md` | 手写 |
| CLI 参考 | `pages/reference/cli.md` | 手写 |
| Server Flags | `pages/reference/server-flags.md` | 手写 |
| Resource Schema | `pages/reference/resources/*.md` | 手写 + CRD 类型关联 |

### OpenAPI 维护流程

```
Go resources/ 类型变更 → 手动更新 openapi/schemas/*.yaml → 更新 openapi.yaml
→ npx @redocly/cli@1.28.5 lint openapi/openapi.yaml → 提交
```

CI 通过重新运行 generator 并检查 `git diff --exit-code` 验证 OpenAPI 与代码一致。

## 设计亮点

### 1. 五层导航深度

侧边栏最深 5 层嵌套（Reference → Resources → Governance → ToolPermission），但每层都是 `collapsed: false`，用户一眼可见完整结构，不需要逐层展开。

### 2. 环境变量驱动部署

`VOCS_BASE_URL` 和 `VOCS_BASE_PATH` 允许同一份构建产物部署到自定义域名或 GitHub Pages 子路径，无需硬编码。

### 3. 部署文档 + 参考配置分离

`pages/deploy/*.md` 是面向用户的文档；`design/kubernetes/` 和 `design/vps/` 是可直接使用的 YAML/Compose 参考配置。文档引用配置，配置不混入文档。

### 4. 概念与操作分离

Concepts 只讲 "是什么" 和 "为什么"；Guides 讲 "怎么做"；Operations 讲 "怎么运维"。三层不重叠。

### 5. 资源参考按 CRD 分组

Reference → Resources 按领域分组（Agents / Tasks / Tools & Models / Governance / Infrastructure / Evaluation / Memory / Secrets），每组 `collapsed: false`，结构清晰。

## 与其他项目对比

| 维度 | Orloj | [[zed]] 文档 | [[temporal]] 文档 |
|------|-------|------------|-----------------|
| 框架 | Vocs | mdBook + Rust 渲染器 | Docusaurus |
| 内容格式 | Markdown | Markdown | Markdown + MDX |
| API 文档 | OpenAPI 3.1 手写 | 无独立 API 文档 | gRPC proto 生成 |
| 导航深度 | 5 层 | 2 层 | 3 层 |
| 品牌声音 | 无评分卡 | 8 项评分卡强制 | 标准 |
| 参考配置 | 分离（design/ 目录） | 内嵌 | 内嵌 |

## 可借鉴实践

- **Vocs 框架**：轻量级替代 VitePress，配置简洁（单个 `vocs.config.ts`），适合 Go 项目文档
- **部署文档与参考配置分离**：文档专注说理，配置可直接复用
- **Concept / Guide / Operations 三层分离**：避免文档角色混淆
- **OpenAPI 规范驱动**：API 文档与代码同步，CI 强制验证
- **`collapsed: false` 全展开侧边栏**：对于 API 参考类文档，全展开比折叠更友好

## 相关链接

- 文档站：https://docs.orloj.dev
- GitHub 源码：`github.com/OrlojHQ/orloj` → `docs/`
