---
title: gstack 浏览器架构
created: 2026-05-11
updated: 2026-05-11
type: concept
tags: [ai-coding, architecture, browser, bun, playwright]
sources: [raw/gstack-architecture.md]
confidence: high
---

# gstack Browser Architecture

> Bun + Chromium daemon + Ref 系统，持久化状态，~100ms/命令

## Overview

gstack 浏览器不是简单截图工具，而是持久化 Chromium 守护进程，通过 HTTP 与 CLI 通信，使用 Ref 系统让 Agent 无需写 CSS 选择器即可操作页面。

## Architecture

```
Claude Code ──POST──→ CLI (binary) ──HTTP──→ Server (Bun.serve) ──CDP──→ Chromium (headless)
                        ↑ reads state file     dispatches command      persistent tabs
                        ↓ localhost:PORT        returns plain text     30min idle timeout
```

First call ~3s startup, subsequent calls ~100-200ms.

## 为什么用 Bun

1. **编译二进制** — `bun build --compile` → ~58MB 单文件，无 node_modules
2. **原生 SQLite** — Cookie 解密直接读 Chromium DB，无需 better-sqlite3
3. **原生 TypeScript** — 开发时 `bun run server.ts`，无编译步骤
4. **内置 HTTP** — `Bun.serve()` ~10 个路由，无需 Express

## 守护进程模型

- **状态文件**: `.gstack/browse.json`（原子写入，权限 0o600）
- **端口**: 随机 10000-60000，10 个工作空间零冲突
- **版本重启**: CLI 对比版本，不匹配自动杀旧启新
- **生命周期**: 自动启动，30 分钟空闲自动关闭

## Ref 系统

`@e1`, `@e2` = ARIA 树元素 | `@c1`, `@c2` = 可点击但不在 ARIA 树中的元素

```
snapshot → accessibility.snapshot() → 分配 refs → 构建 Playwright Locator
click @e3 → resolveRef("e3") → count() 检测过期 → locator.click()
```

**为什么不用 DOM 注入**: CSP 阻止、框架水合剥离、Shadow DOM 不可达。Locator 基于 Chromium 内部无障碍树，完全外部化。

**过期检测**: SPA 变更（React Router、模态框）通过 `count()` 在 ~5ms 内检测，而非等 30 秒超时。

## 安全模型

- **localhost only** — 不可从网络访问
- **Bearer Token** — 每会话随机 UUID
- **Cookie** — Keychain 批准、内存解密、只读 DB 副本、日志无值
- **Shell 注入防护** — 浏览器路径硬编码，不用字符串拼接

## 日志架构

三个环形缓冲区（各 50K 条，O(1) push）→ 每秒异步刷盘 → append-only 磁盘文件

## 测试体系

| 层级 | 内容 | 成本 | 速度 |
|------|------|------|------|
| 1 — 静态 | 解析命令、验证注册表 | 免费 | <5s |
| 2 — E2E | 真实 Claude 会话 | ~$3.85 | ~20min |
| 3 — LLM-as-judge | Sonnet 评分文档 | ~$0.15 | ~30s |

## Gaps

- iframe 不跨边界
- 仅 macOS Cookie 解密
- 无 WebSocket 流式
- 无 MCP 协议

See also: [[gstack]], [[gstack-sprint-flow]]
