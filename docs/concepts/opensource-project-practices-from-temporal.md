---
title: 从 Temporal 项目学习开源开发维护实践
created: 2026-05-15
updated: 2026-05-15
type: concept
tags: [open-source, devops, ci-cd, code-review, testing, community, go]
sources:
  - https://github.com/temporalio/temporal
  - ~/Projects/temporal
confidence: high
related:
  - "[[temporal]]"
---

# 从 Temporal 项目学习开源开发维护实践

> Temporal 是一个拥有 10000+ commit、多团队协作的大型 Go 开源项目。以下从其仓库结构、CI/CD、代码审查、测试策略、发布管理和社区维护六个维度，提炼可复用的开源项目治理实践。

---

## 1. 项目结构组织

### 仓库职责清晰划分

- 本仓库 (`temporal`) 只包含 Server 端代码
- SDK、API、UI 等独立为各自仓库（`sdk-go`、`api`、`api-go`）
- 通过 `go.mod` 的 `replace` 指令支持跨仓库本地联调

### 架构文档独立维护

- `docs/architecture/` 下有 15+ 个独立文档，每个聚焦一个子系统
- 子系统包括：history-service、matching-service、schedules、nexus、chasm、workflow-lifecycle、workflow-update 等
- 架构知识不埋在代码注释里，而是独立成可检索的文档

### 目录布局参考

```
temporal/
├── .github/              # CI 工作流、PR 模板、CODEOWNERS
│   ├── workflows/        # 19 个 CI workflow
│   ├── actions/          # 可复用的 composite actions
│   ├── PULL_REQUEST_TEMPLATE.md
│   ├── CODEOWNERS
│   └── copilot-instructions.md
├── api/                  # 公共 API proto 定义
├── cmd/                  # 入口程序
├── common/               # 跨服务共享模块
├── config/               # 配置模板
├── docs/                 # 文档
│   ├── architecture/     # 架构文档
│   └── development/      # 开发指南（testing.md 等）
├── schema/               # 数据库 Schema（多数据库）
├── service/              # 核心服务实现
└── temporal/             # Server 组装层
```

---

## 2. 贡献者友好设计

### CONTRIBUTING.md 全链路覆盖

- **前置依赖**：明确列出 Go、Cassandra/SQL、protobuf 编译器等
- **Windows 开发者专项说明**：降低平台门槛
- **首次构建**：`make` 一键搞定
- **增量构建**：`make bins`（跳过测试）
- **本地 API 变更**：跨仓库联调步骤（api → api-go → sdk-go → server）

### PR 模板结构化

```
## What changed?
（改了什么）

## Why?
（为什么改 — 写给未来的自己）

## How did you test it?
（怎么测试的 — 明确测试方法）

## Potential risks
（潜在风险 — 培养风险意识）
```

### 降低首次参与门槛

根 README 直接链接到：
- proposals（提案流程）
- 架构文档
- 本地构建指南
- 测试最佳实践
- 社区论坛和 Slack

---

## 3. CI/CD 流水线

### 概览：19 个 Workflow

| Workflow | 作用 |
|----------|------|
| `run-tests.yml` | 主测试，智能分片 + 多数据库矩阵 |
| `linters.yml` | actionlint、proto lint、API lint、Go lint |
| `govulncheck.yml` | Go 漏洞扫描 |
| `flaky-tests-report.yml` | 每周三定时，生成 flaky test 报告，推送 Slack |
| `check-pr-placeholders.yml` | 防止 placeholder 代码合入 |
| `check-release-dependencies.yml` | 发布前依赖检查 |
| `stale.yml` | PR 超 120 天自动标记 stale |
| `release.yml` | 基于 GitHub Release 触发构建+发布 |
| `optimize-test-sharding.yml` | 自动优化测试分片策略 |
| `ci-success-report.yml` | CI 成功通知 |
| `auto-approve-cicd-release-pr.yml` | 发布 PR 自动审批 |
| `build-and-publish.yml` | Docker 镜像构建发布 |
| `features-integration.yml` | 功能集成测试 |
| `run-single-test.yml` | 手动触发单测运行 |
| `docker-build-manual.yml` | 手动 Docker 构建 |
| `promote-*-image.yml` | 镜像晋升流程 |
| `trigger-version-info-service.yml` | 版本信息服务触发 |

### 核心亮点：智能测试分片

```
1. PR 触发 → 检测变更范围
2. 智能裁剪：只跑必要的数据库组合（SQL / Cassandra / Elasticsearch）
3. 例外：打 test-all-dbs label 或改了 persistence 包 → 跑全量
4. SHARD_COUNT=3 并行分片
5. MAX_TEST_ATTEMPTS=3 自动重试
6. 并发控制：同一 PR 新 commit 自动取消旧运行
```

### 并发与自动取消

```yaml
concurrency:
  group: run-tests-${{ github.head_ref || github.run_id }}
  cancel-in-progress: true
```

---

## 4. 代码审查制度

### CODEOWNERS 分层管理

```
# 全局兜底
*                @temporalio/server @temporalio/cgs @temporalio/nexus

# 子系统细粒度
/chasm/          @temporalio/nexus
/service/history/ @temporalio/server
/service/matching/ @temporalio/server
/common/persistence/ @temporalio/server
/schema/         @temporalio/server
```

### Copilot 代码审查指南（8 条规则）

1. **删除冗余代码**（最高优先级）— 不加不必要的测试复杂度，不测可假定正确的东西
2. **Go 命名规范** — 不用 `Get` 前缀、不用 `Impl` 后缀、不在 `Test` 后加下划线
3. **Testify Suite 正确性** — 详细规范了 Suite 的使用方式和常见错误
4. **倾向内联代码** — 避免过度抽象，三行相似代码优于一个过早的抽象
5. **标准错误处理** — 用标准 error type，validate early，不 panic
6. **与代码库保持一致** — 跟随现有模式，使用已有工具
7. **API 和 Proto 设计** — 遵循 Proto 最佳实践
8. **并发安全** — 明确并发模式和安全要求

---

## 5. 测试策略

### 测试最佳实践文档化

文档路径：`docs/development/testing.md`

| 实践 | 说明 |
|------|------|
| **强制并行** | 所有测试使用 `t.Parallel()`，`make parallelize-tests` 自动添加 |
| **退出机制** | `//parallelize:ignore` 可退出并行 |
| **parallelsuite** | 替代 testify Suite，默认全并行 + 安全断言 |
| **testvars** | 生成确定性测试变量，避免手动构造 |
| **require > assert** | 失败即停，不继续执行后续断言 |

### 构建标签隔离

```bash
# 减小二进制体积
-tags disable_grpc_modules

# 测试依赖
-tags disable_grpc_modules,test_dep

# IDE 调试也需指定
-tags disable_grpc_modules,test_dep
```

### 测试工具链

```go
// testvars: 确定性测试变量
tv := testvars.New(t)
req := &workflowservice.SignalWithStartWorkflowExecutionRequest{
    RequestId:    tv.Any().String(),
    Namespace:    tv.NamespaceName().String(),
    WorkflowId:   tv.WorkflowID(),
    TaskQueue:    tv.TaskQueue(),
}

// 后续可精确断言
require.Equal(t, tv.WorkflowID(), startedWorkflow.WorkflowId)
```

---

## 6. 分支与发布管理

### 分支策略

```
main                    → 持续开发
release/v1.29.x         → 稳定发布线
release/v1.30.x         → 稳定发布线
cloud/*                 → 云版本分支
feature/*               → 功能分支
cdf-release/*           → 特定客户发布
```

### Tag 命名

```
v1.32.0-156.0-rc.20260505114857
│       │     │   └─ 时间戳
│       │     └─ RC 标识
│       └─ 内部版本号
└─ 主版本
```

### Commit 消息风格

```
[Scheduler] Always attempt DeleteSchedule on both stacks (#10197)
[Nexus/CHASM] Use token instead of storing batch ID for event load (#10154)
fix: admin-tools container ignores SIGTERM until kill deadline (#10187)
chore: enable scheduler sentinel creation and chasm scheduler routing (#10185)
Refactor sync match return types for readability and extensibility (#10044)
```

规律：
- 可选 `[Subsystem]` 前缀标识子系统
- 或 `fix:` / `chore:` 常规前缀
- 必须附带 PR 编号 `(#xxxxx)`
- 一句话描述做了什么

---

## 7. 社区维护自动化

| 工具 | 触发条件 | 作用 |
|------|----------|------|
| Stale Bot | PR 120 天无更新 | 自动标 stale（不自动关闭） |
| Flaky Test Reporter | 每周三定时 | 生成报告 + Slack 推送 |
| Auto-approve CICD | 发布 PR | 自动审批 |
| CI Success Report | CI 通过 | 统一通知 |
| PR Placeholder Check | 每次 PR | 防止占位代码合入 |
| Release Dependencies | 发布前 | 依赖冲突检查 |

---

## 8. 可直接复用的实践清单

### 开源项目起步必做

- [ ] 一份好的 **CONTRIBUTING.md** — 从 clone 到第一次成功构建，零知识假设
- [ ] **PR 模板** — 强制回答"为什么改"和"怎么测试的"
- [ ] **CODEOWNERS** — 关键路径必须有人兜底审查
- [ ] **LICENSE** — 明确开源协议

### CI/CD 优化

- [ ] **智能测试裁剪** — 按变更范围决定测试范围，不是所有 PR 都跑全量
- [ ] **测试分片 + 自动重试** — 并行提速 + 容错
- [ ] **并发控制** — 同一 PR 新 commit 自动取消旧运行
- [ ] **多维度 lint** — 代码、proto、action 分别检查

### 测试基础设施

- [ ] **提供测试工具包** — 降低写好测试的门槛（如 testvars、parallelsuite）
- [ ] **Flaky Test 治理** — 不靠人肉发现，定时生成报告
- [ ] **并行化默认开启** — 并提供退出机制

### 代码审查

- [ ] **文档化审查标准** — 不是靠口口相传，写在文件里
- [ ] **CODEOWNERS 分层** — 全局兜底 + 子系统细粒度
- [ ] **机器人辅助** — Copilot instructions 自动检查常见问题

### 发布管理

- [ ] **发布分支策略** — main 开发 + release 分支维护
- [ ] **Tag 命名规范** — 版本号 + 时间戳，可追溯
- [ ] **自动化发布流程** — Release 触发 → 构建 → 发布

### 社区维护

- [ ] **Stale Bot** — 自动标记不活跃 PR
- [ ] **多个沟通渠道** — GitHub Issues + 论坛 + Slack
- [ ] **降低参与门槛** — 链接文档、提供示例、简化首次构建

---

## 核心启示

> **开源项目的成功不仅取决于代码质量，更取决于贡献者体验和自动化程度。**
>
> Temporal 的做法是：把人的经验写成文档（CONTRIBUTING.md、testing.md、copilot-instructions.md），把重复劳动交给机器（CI 分片、stale bot、flaky report），把审查责任明确到人（CODEOWNERS），让每个参与者都能以最小的摩擦力完成从 clone 到 PR 的全过程。
