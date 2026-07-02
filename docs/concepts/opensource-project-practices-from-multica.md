---
title: 从 Multica 项目学习开源开发维护实践
created: 2026-05-15
updated: 2026-05-15
type: concept
tags: [open-source, devops, ci-cd, monorepo, testing, go, typescript, api-design, documentation]
sources:
  - https://github.com/multica-ai/multica
  - ~/Projects/multica
confidence: high
related:
  - "[[multica]]"
  - "[[opensource-project-practices-from-temporal]]"
---

# 从 Multica 项目学习开源开发维护实践

> Multica 是一个 AI 原生任务管理平台（类 Linear），以 Go 后端 + TypeScript monorepo 前端构建。以下从项目结构、CI/CD、API 兼容性、测试策略、文档体系和开发者体验六个维度，提炼中小型开源项目的治理实践。

---

## 1. 项目结构与 Monorepo 治理

### 分层包架构 + 严格依赖方向

```
apps/web (Next.js)  ←→  packages/views  ←→  packages/core (纯逻辑，零 react-dom)
apps/desktop (Electron)  ←→  packages/views  ←→  packages/ui (纯 UI，零业务逻辑)
```

- **依赖方向单向**：`views → core + ui`，core 和 ui 互不依赖
- **Internal Packages 模式**：共享包直接导出 `.ts/.tsx` 源码，由消费方编译，零配置 HMR 和即时跳转定义
- **pnpm catalog**：`pnpm-workspace.yaml` 中 `catalog:` 统一版本号，所有共享依赖引用 `catalog:` 保证单版本

```yaml
# pnpm-workspace.yaml
packages:
  - "apps/*"
  - "packages/*"
catalog:
  react: "19.2.3"
  vitest: "^4.1.0"
  zod: "^4.1.5"
  # ... 所有共享依赖版本在此单一声明
```

- **Turborepo** 管理构建流水线，`turbo.json` 声明任务依赖关系和缓存策略

### 包边界硬约束

| 包 | 可以依赖 | 禁止依赖 |
|---|---|---|
| `packages/core` | 无应用特定代码 | `react-dom`, `localStorage`, `process.env`, `next/*` |
| `packages/ui` | 无 | `@multica/core`，任何业务逻辑 |
| `packages/views` | `core/`, `ui/` | `next/*`, `react-router-dom`, stores |
| `apps/web/platform/` | `next/*` | 其他 app |
| `apps/desktop/.../platform/` | `react-router-dom`, electron | 其他 app |

**核心规则**：如果同一逻辑在两个 app 中都存在，**必须**抽取到共享包，没有例外。

---

## 2. CI/CD 流水线

### CI (`ci.yml`)：PR 和 main push 触发

```
Frontend job: install → 生成代码漂移检查 → build + typecheck + lint + test
Backend job:  pgvector + Redis 服务容器 → Go build → 迁移 → 测试
```

**关键特性**：

- **并发取消**：同一 PR 新 commit 自动取消旧运行
- **漂移防护**：CI 重新运行 `pnpm generate:reserved-slugs`，然后 `git diff --exit-code` 检查，防止 Go/TS 两端数据不同步
- **完整矩阵**：Node 22 + Go 1.26.1 + pgvector/pgvector:pg17 + Redis 7

### Release (`release.yml`)：git tag 触发，多阶段发布

```
Tag push → 验证 semver 格式 → Go 测试 → GoReleaser 多平台构建
        → Docker 多架构原生构建 (amd64 + arm64)
        → Desktop 打包 (Linux + Windows)
        → GitHub Releases + Homebrew tap
```

**亮点**：

- **Tag 格式严格验证**：拒绝 `dirty` tag，区分 stable/pre-release
- **多架构原生构建**：amd64 在 `ubuntu-latest`，arm64 在 `ubuntu-24.04-arm`，避免 QEMU 模拟（之前 arm64 Next.js 构建耗时 30+ 分钟）
- **Fork 保护**：`if: github.repository_owner == 'multica-ai'` 防止 fork 误触发发布到上游
- **macOS 手动签名**：桌面端 macOS 构建需 Apple Developer 凭据，尚未自动化到 CI

---

## 3. API 响应兼容性：桌面应用的特殊挑战

桌面应用的特殊性：安装版本永远比服务器旧（用户可能还在跑 0.2.26，但服务器已是 0.4.x）。三次线上事故（#2143, #2147, #2192）催生了以下规则：

### 防御性 API 边界

| 规则 | 做法 |
|---|---|
| Parse, don't cast | `parseWithFallback(schema, fallback)` — zod 验证 + 回退值，失败不抛异常 |
| 禁止裸 `as` 断言 | 所有端点响应必须经过 schema |
| 可选链全覆盖 | `=== true` 显式布尔检查，不用 truthy/falsy |
| Enum 漂移降级 | `switch` 必须有 `default` 分支，渲染通用回退 |
| 不依赖单一字段 | 按钮状态组合多个信号（cursor、page length 等） |
| 每个端点配测试 | 至少一个畸形响应测试（缺字段、错类型、null 数组） |

```typescript
// parseWithFallback 示例：验证失败不抛异常，返回回退值
const result = parseWithFallback(IssueSchema, rawResponse, fallbackIssue);
```

> **核心洞察**：CSR-only 浏览器应用可以在几分钟内推送修复；安装在用户笔记本上的 Electron 构建不能。防御性边界不是过度工程，而是桌面应用架构的唯一防护手段。

---

## 4. 代码生成与漂移防护

### sqlc：SQL → Go 类型安全代码

```yaml
# sqlc.yaml
sql:
  - engine: "postgresql"
    queries: "pkg/db/queries/"
    schema: "migrations/"
    gen:
      go:
        package: "db"
        out: "pkg/db/generated"
        sql_package: "pgx/v5"
        emit_json_tags: true
```

### Reserved Slugs：JSON → Go embed + TS 生成

```
reserved_slugs.json (单一真相源)
  ├── Go: embed JSON 直接使用
  └── TS: pnpm generate:reserved-slugs → reserved-slugs.ts
  └── CI: 重新生成 + git diff --exit-code 验证无漂移
```

### 迁移文件规范

- 文件格式：`NNN_descriptive_name.up.sql` + `.down.sql`，必须成对
- 命名规范：表 `snake_case` 单数，列 `snake_case`，外键 `<table>_id`，布尔 `is_<state>` 或 `<state>_at`

---

## 5. 测试策略

### 测试跟随代码，不跟随 App

| 测试对象 | 测试位置 | 工具 |
|---|---|---|
| 共享业务逻辑（stores, hooks） | `packages/core/*.test.ts` | Vitest, Node 环境 |
| 共享 UI 组件 | `packages/views/*.test.tsx` | Vitest + jsdom + testing-library |
| 平台特定接线 | `apps/web/*.test.tsx` | Vitest + 框架 mock |
| 端到端用户流程 | `e2e/*.spec.ts` | Playwright |
| Go 后端 | `server/` | go test |

**核心原则**：共享组件测试在 `packages/views/`，不在 app 里。如果需要 mock `next/navigation` 来测共享组件，说明测试位置错了。

### Mocking 约定

```typescript
// Zustand store mock 模式
const mockUseStore = vi.hoisted(() => {
  const state = { user: null, loading: false };
  const selector = (s: any) => s;
  Object.assign(selector, { getState: () => state });
  return selector;
});
```

- `packages/views/` 测试中：**永不** mock `next/*` 或 `react-router-dom`
- `apps/web/` 测试中：仅 mock 框架特定 API

---

## 6. 文档体系

### 文档即规范

| 文档 | 作用 | 特点 |
|---|---|---|
| `CLAUDE.md` | AI 代码助手行为规范 | 25KB，覆盖架构、编码规则、测试、提交规范 |
| `CONTRIBUTING.md` | 贡献者指南 | setup/worktree/testing/troubleshooting 全链路 |
| `conventions.mdx` | 命名规范 + i18n 词汇表 + 中文语感指南 | **单一真相源**，旧 glossary.md 已重定向至此 |
| `apps/docs/` | 用户文档 | 每篇有 `.zh.mdx` 中文翻译 |
| `SELF_HOSTING.md` | 自托管指南 | Docker Compose 一键部署 |

### i18n 翻译词汇表的核心区分

- **Entity（实体）**：有 URL、数据库行、API 类型的产品名词 → 中文文本中保留英文小写，视觉上读作类型名
- **Concept（概念）**：通用名词，非数据库实体 → 完整翻译，不让中文用户看到嵌入的英文碎片

### 命名规范（conventions.mdx 单一真相源）

| 领域 | 规则 |
|---|---|
| 路由 | 单词 (`/login`) 或 `/{noun}/{verb}` (`/workspaces/new`)，禁止连字符词组 |
| 包/模块 | 按功能/领域组织，不按类型 |
| 数据库 | `snake_case` 单数表名，`<table>_id` 外键 |
| Go | 标准 Go 惯例 |
| TypeScript | strict mode，显式类型 |
| 提交 | Conventional commits: `feat(scope)`, `fix(scope)` |

---

## 7. 开发者体验 (DX)

### 一键命令

```bash
make dev       # 自动创建环境、安装依赖、启动 DB、迁移、启动应用
make check     # typecheck + TS 测试 + Go 测试 + E2E
make selfhost  # 一键 Docker Compose 自托管部署（含 JWT 密钥自动生成）
```

### Worktree 隔离

- 共享一个 PostgreSQL 容器，每个 worktree 独立数据库
- `make worktree-env` 自动生成 `.env.worktree`（唯一 DB 名 + 端口）
- 配置、PID、健康检查端口、工作目录全部隔离

| 资源 | 主环境 | Worktree |
|---|---|---|
| 配置文件 | `~/.multica/config.json` | `~/.multica/profiles/dev-<slug>-<hash>/config.json` |
| 健康端口 | `19514` | `19514 + 1 + (name_hash % 1000)` |
| 数据库 | `multica` | `multica_<slug>_<hash>` |

**多个 worktree 可同时运行，零冲突。**

---

## 8. 可直接复用的实践清单

### 项目起步

- [ ] **CLAUDE.md** — 让 AI 助手理解项目规则，代码生成更准确
- [ ] **CONTRIBUTING.md** — 从 clone 到第一次成功运行，零知识假设
- [ ] **conventions 文档** — 命名、翻译、风格的单一真相源
- [ ] **Makefile 一键命令** — `make dev` / `make check` 隐藏工具链复杂性

### CI/CD

- [ ] **CI 验证生成代码** — 自动运行生成器 + diff 检查，不信任开发者手动跑
- [ ] **并发取消** — 同一 PR 新 commit 取消旧运行
- [ ] **多架构原生构建** — 避免 QEMU 模拟，用对应平台的 runner
- [ ] **Tag 驱动发布** — 格式验证 + 区分 stable/pre-release
- [ ] **Fork 保护** — 发布 job 检查 `repository_owner`

### API 设计

- [ ] **Schema 验证所有外部数据** — `parseWithFallback`，失败返回回退值不崩溃
- [ ] **每个端点配畸形响应测试** — 缺字段、错类型、null
- [ ] **不依赖单一布尔字段驱动 UI** — 组合多个信号

### Monorepo 治理

- [ ] **依赖方向单向** — 画出依赖图，禁止循环
- [ ] **pnpm catalog** — 共享依赖版本单一声明
- [ ] **包边界硬约束** — 列出每个包可以/禁止依赖什么
- [ ] **测试跟随代码** — 共享组件测试在共享包，不在 app

### 代码生成

- [ ] **单一真相源 + 生成** — 手写一份源文件，自动生成多语言输出
- [ ] **CI 验证无漂移** — 生成 + diff，防止手改生成文件

### 开发环境

- [ ] **Worktree 友好** — 数据库/端口/配置隔离，多人多分支并行不冲突
- [ ] **一键 setup** — `make dev` 或等效命令完成全部初始化
- [ ] **自托管支持** — Docker Compose + 自动密钥生成

---

## 核心启示

> **中小型开源项目的关键不是功能多，而是降低贡献者的认知负担。**
>
> Multica 的做法是：每个关注点只有一个权威来源（`reserved_slugs.json`、`conventions.mdx`、`pnpm catalog`），CI 自动验证一致性而不是靠人肉检查，`make` 命令隐藏工具链复杂性，API 边界用 schema + 回退值防御性处理。这些实践让 2-10 人团队可以高效协作而不被复杂性拖垮。
>
> 与 [[opensource-project-practices-from-temporal|Temporal 的实践]] 对比：Temporal 用 CODEOWNERS + 智能分片 + flaky test 治理解决大规模问题；Multica 用单一真相源 + 漂移防护 + 一键命令解决中小团队的效率问题。两者共通的是**把人的经验写成文档、把重复劳动交给机器**。
