---
title: 从 OpenHuman 项目学习开源开发维护实践
created: 2026-05-18
updated: 2026-05-18
type: concept
tags: [open-source, devops, ci-cd, testing, rust, react, tauri, documentation, developer-experience]
sources:
  - ~/Projects/openhuman
  - https://github.com/tinyhumansai/openhuman
confidence: high
related:
  - "[[openhuman-architecture]]"
  - "[[opensource-project-practices-from-multica]]"
  - "[[opensource-project-practices-from-temporal]]"
---

# 从 OpenHuman 项目学习开源开发维护实践

> OpenHuman 是一个 Rust + React/Tauri 桌面 AI 助手开源项目。它在**双语言栈（Rust + TypeScript）**环境下展示了一套完整的工程实践：覆盖率硬门、Agent 友好的调试工具链、域驱动的模块化规范、以及面向 AI 协作的项目文档体系。

## 1. 覆盖率硬门：diff-cover ≥ 80%

### 1.1 三路覆盖率收集

```
frontend-coverage  → Vitest (app/) → lcov.info
rust-core-coverage → cargo-llvm-cov (Cargo.toml) → lcov.info
rust-tauri-coverage→ cargo-llvm-cov (app/src-tauri/) → lcov.info
                         ↓
              coverage-gate: diff-cover ≥ 80%
```

- **diff-cover** 只检查 PR 变更行的覆盖率，不是全量覆盖率
- 测试文件本身不纳入 lcov（Vitest `coverage.exclude` + `#[cfg(test)]`），不会膨胀分母
- 前端 lcov 路径用 `sed` 从 `src/` 修正为 `app/src/`，与 git diff 路径对齐
- 覆盖率不达标 → PR **无法合并**，不是警告而是硬阻断

### 1.2 关键设计

- **lcov 路径归一化**：Vitest 输出 `SF:src/...`，但 diff-cover 需要仓库根相对路径 `SF:app/src/...`，CI 中用 sed 修正
- **Rust 覆盖率**：`cargo-llvm-cov`，禁用 `CARGO_INCREMENTAL`（与 instrumentation 不兼容），不用 sccache
- **Docker CI 镜像**：`ghcr.io/tinyhumansai/openhuman_ci:rust-1.93.0` 统一环境

**对比** [[opensource-project-practices-from-multica|Multica]]：Multica 用 Go + TypeScript 两路 lcov，OpenHuman 增加了 Tauri shell 的第三路 Rust 覆盖率，复杂度更高但原则一致——**只卡变更行，不卡全量**。

---

## 2. 测试策略：四层金字塔

| 层 | 工具 | 覆盖范围 | 运行方式 |
|----|------|----------|----------|
| Rust 单元 | `cargo test` | 核心域逻辑 | `pnpm test:rust` |
| 前端单元 | Vitest | React 组件、hooks、utils | `pnpm test` |
| JSON-RPC E2E | cargo test + mock | 核心到 RPC 的完整链路 | `scripts/test-rust-with-mock.sh` |
| 桌面 E2E | WDIO + tauri-driver / Appium | 全栈用户流程 | `pnpm test:e2e:all:flows` |

### 2.1 共享 Mock 后端

- `scripts/mock-api-core.mjs` + `scripts/mock-api-server.mjs`
- 管理端点：`GET /__admin/health`、`POST /__admin/reset`、`POST /__admin/behavior`
- Rust 测试和前端测试共用同一个 mock server

### 2.2 双平台 E2E

| 平台 | 驱动 | 端口 | App 格式 |
|------|------|------|----------|
| Linux (CI) | tauri-driver | 4444 | Debug binary |
| macOS (local) | Appium Mac2 | 4723 | `.app` bundle |

- 用 `element-helpers.ts` 封装原生操作（`clickNativeButton`、`waitForWebView`），不直接使用 `XCUIElementType*`
- 每个规格有独立的 `OPENHUMAN_WORKSPACE`（临时目录），确保测试隔离

### 2.3 设计哲学

> 测试跟随代码，不跟随 App。新增/变更行为必须先有测试再堆叠功能。未测试代码 = 未完成代码。

---

## 3. Agent 友好的调试工具链

`scripts/debug/` 提供封装好的测试运行器，专为 AI agent 上下文窗口优化：

```bash
pnpm debug unit                                    # 全部 Vitest
pnpm debug unit src/components/Foo.test.tsx        # 单文件
pnpm debug unit Foo -t "renders empty" --verbose   # 按测试名过滤
pnpm debug e2e test/e2e/specs/smoke.spec.ts        # WDIO 单规格
pnpm debug rust                                    # cargo test
pnpm debug logs last                               # 查看最近日志
```

### 3.1 设计原则

- **有界输出**：stdout 只显示摘要 + 失败块，完整输出 tee 到 `target/debug-logs/`
- `--verbose` 同时流式输出原始内容
- **稳定接口**：封装底层工具链的 flag 变化，agent prompt 不会因工具升级而失效
- 位置参数 + 少量 flag（`-t`、`--verbose`），降低 prompt 复杂度

**启示**：为 AI agent 设计工具接口时，**有界输出 > 完整输出**，**稳定接口 > 灵活接口**。

---

## 4. CI/CD 体系

### 4.1 工作流清单

| 工作流 | 触发 | 用途 |
|--------|------|------|
| `coverage.yml` | PR + 手动 | 三路覆盖率收集 + diff-cover 门 |
| `test.yml` | PR + push | Rust core tests + Tauri shell tests |
| `e2e.yml` | PR + push | WDIO 桌面 E2E（Linux） |
| `release.yml` | git tag | 多平台构建发布 |

### 4.2 关键配置

- **并发取消**：同一 PR 新 commit 自动取消旧运行（`concurrency` group）
- **Rust 缓存**：`Swatinem/rust-cache` 分 workspace（core + tauri），`cache-on-failure: true`
- **CEF 缓存**：独立 cache key 绑定 `Cargo.toml` hash
- **Container 化**：统一 CI 镜像避免环境差异

---

## 5. 文档体系：文档即规范

### 5.1 文档层级

```
CLAUDE.md          → AI agent 权威指南（代码规范 + 工作流）
AGENTS.md          → RPC 控制器模式规范
gitbooks/developing/ → 人类贡献者文档
  ├── architecture.md     → 叙事架构
  ├── architecture/*.md   → 子系统架构（前端、Tauri壳、Agent Harness）
  ├── e2e-testing.md      → E2E 测试指南
  ├── testing-strategy.md → 测试策略
  └── cef.md              → CEF 运行时笔记
docs/              → 深层内幕（内存管线、Sentry 等）
.claude/rules/     → 有意为空，指向 CLAUDE.md
```

### 5.2 CLAUDE.md 的设计哲学

CLAUDE.md 不仅仅是 README，它是**可执行规范**：
- 定义了精确的命令集（从 `pnpm dev` 到 `pnpm debug logs last`）
- 规定了编码哲学（Unix 式模块、测试先行、文档随代码）
- 设定了硬约束（无动态 import、无第三方 webview JS 注入、文件 ≤ 500 行）
- 包含了调试日志规范（稳定前缀、关联字段、不记录密钥）

**启示**：AI 时代的项目文档不只是给人看的，更是给 AI agent 的编程接口。写得好 = agent 自动遵循项目规范。

---

## 6. 模块化规范：域布局规则

### 6.1 硬约束

- 新功能必须在 `src/openhuman/<domain>/` 子目录中
- **禁止**在 `src/openhuman/` 根目录添加独立 `.rs` 文件（`dev_paths.rs` 和 `util.rs` 是遗留特例）
- `mod.rs` 只做导出，业务代码在 `ops.rs`、`store.rs`、`types.rs` 等
- 文件 ≤ 500 行，超出则拆分

### 6.2 控制器迁移检查清单

新域的完整流程：
1. 创建 `src/openhuman/<domain>/` 目录 + `mod.rs`
2. 创建 `schemas.rs`：定义 `schemas()`、`all_controller_schemas()`、`all_registered_controllers()`、`handle_*()` fns
3. `mod.rs` 中 `mod schemas;` + re-export
4. 在 `src/core/all.rs` 中接入域导出
5. 从 `src/core/dispatch.rs` 移除已迁移的方法分支

**启示**：固定的脚手架模式（mod → schemas → rpc → ops → store）降低了新域的认知负担，让贡献者不需要理解框架内部就能添加新功能。

---

## 7. PR 模板与社区规范

### 7.1 PR 提交检查清单

PR 模板包含严格的自检清单：
- [ ] 测试已添加（happy path + 至少一个 failure/edge case）
- [ ] **Diff 覆盖率 ≥ 80%**
- [ ] 覆盖率矩阵已更新（`docs/TEST-COVERAGE-MATRIX.md`）
- [ ] 无新增外部网络依赖（使用 mock backend）
- [ ] 手动冒烟清单已更新（如涉及发布面）
- [ ] 关联 issue 通过 `Closes #NNN` 关闭

### 7.2 AI 辅助 PR 的元数据

PR 模板包含 AI Author Metadata 区块（Linear Issue、Commit & Branch、Validation Run、Behavior Changes、Parity Contract），说明这个项目**正式接受 AI 生成代码**并要求标注来源。

### 7.3 Issue 模板

三种模板：`feature.md`、`bug.md`、`task.md`，每种都有验收标准（含 ≥ 80% 覆盖率要求）。

---

## 8. 开发者体验 (DX)

### 8.1 一键命令

所有命令从仓库根执行，`pnpm` 统一入口：
- `pnpm dev` — 前端开发
- `pnpm dev:app` — 完整 Tauri 桌面开发
- `pnpm test` / `pnpm test:rust` — 前端/Rust 测试
- `pnpm debug *` — Agent 友好的调试运行器

### 8.2 确定性环境

- `.env.example` + `scripts/load-dotenv.sh` 统一环境变量加载
- 前端配置集中在 `app/src/utils/config.ts`，杜绝散落的 `import.meta.env`
- Rust 配置用 TOML `Config` struct + env 覆盖

### 8.3 Tauri CLI 保护

使用定制版 `tauri-cli`（CEF-aware），`pnpm tauri:ensure` 自动检查/重装。Stock CLI 会产生损坏包（CEF panic）。这种**定制工具链 + 自动校验**的模式值得借鉴。

---

## 9. 安全实践

### 9.1 CEF Webview 零注入

第三方 webview（Telegram、Slack、LinkedIn 等）**不允许任何 JS 注入**：
- 不新增 `.js` 文件
- 不扩展 init script
- 所有抓取通过 CDP 从外部完成
- 新行为只能通过 CEF handlers 或 scanner 模块

### 9.2 其他安全措施

- 进程内 bearer token 认证（每启动生成新 token）
- PID 复用防护（stale-listener 检测时先验证 PID）
- Tauri 插件审计（如 `tauri-plugin-opener` 的 `init-iife.js` 需主动关闭）
- `isTauri()` 封装而非直接检查 `window.__TAURI__`（模块加载时不存在）

---

## 核心启示

> **OpenHuman 的工程实践核心是"用机器卡住人，用规范降低认知负担"。**
>
> 1. **覆盖率硬门**不是建议而是合并阻断——diff-cover 只卡变更行，让既有技术债不阻碍新开发
> 2. **Agent 友好工具链**预示了 AI-first 的开发工作流——有界输出、稳定接口、log 文件化
> 3. **CLAUDE.md 作为可执行规范**——AI 时代的项目文档不只是说明，更是 agent 的编程接口
> 4. **双语言栈协调**——Rust + TypeScript 各自独立的覆盖率收集，通过 lcov 归一化合并
> 5. **域驱动的固定脚手架**——新域遵循固定模式，贡献者不需要理解框架内部
>
> 与 [[opensource-project-practices-from-multica|Multica]] 对比：Multica 用 Go + TypeScript，通过漂移防护和代码生成保持同步；OpenHuman 用 Rust + TypeScript，通过三路覆盖率和域注册表保持一致。两者共通的是**把重复劳动交给 CI，把认知负担降到最低**。
>
> 与 [[opensource-project-practices-from-temporal|Temporal]] 对比：Temporal 解决大规模问题（CODEOWNERS、智能分片、flaky test 治理）；OpenHuman 解决中小团队问题（固定脚手架、Agent 工具链、文档即规范）。三者共通的是**用规范代替审查、用自动化代替人力**。
