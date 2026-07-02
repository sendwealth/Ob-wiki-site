---
title: Blitz
created: 2026-05-20
updated: 2026-06-28
type: entity
tags: [product, ai-coding, agent, macos, swift, app-store-connect, mcp, platform]
sources: [~/Projects/blitz-mac 源码研究]
confidence: high
---

# Blitz

原生 macOS SwiftUI 应用，用于通过 AI 代理（Claude Code / Codex 等）自动化 iOS 应用的 App Store Connect 提交流程。内嵌 MCP 服务器暴露 ~35 个工具，让 AI 代理直接控制模拟器、管理 IAP、上传截图、提交审阅。

- **GitHub**: blitzdotdev/blitz-mac
- **官网**: blitz-mac.com
- **许可**: Apache 2.0
- **语言**: Swift 5.10
- **要求**: macOS 14+, Xcode 16+, Node.js 18+, Go 1.26+

## 1. 解决的核心痛点

App Store Connect 提交流程繁琐——表单多、IAP 必须手动附加、截图要按设备尺寸分轨上传。Blitz 把这些步骤全部暴露为 MCP 工具，AI 代理可以自然语言驱动完成。

## 2. 技术栈

| 层面 | 技术 |
|---|---|
| 语言 | Swift 5.10 |
| UI | SwiftUI + Observation (`@Observable`) |
| 构建 | Swift Package Manager（无 .xcodeproj） |
| 系统框架 | ScreenCaptureKit, Metal, MetalKit, AVFoundation, AppKit, WebKit |
| 外部依赖 | SwiftTerm（终端模拟器） |
| 辅助工具 | asc-cli（Go 编译，git submodule 引入） |

## 3. 代码规模

- **141 个 Swift 文件**，约 **38,800 行**
- 单 target 结构，所有源码在 `src/`
- 3 个 products：`Blitz`（主 app）、`blitz-macos-mcp`（MCP helper）、`BlitzMCPCommon`（共享库）

## 4. 架构

### 4.1 状态管理

单一 `AppState`（`@Observable`）持有全部应用状态，下辖子 Manager：

- **ProjectManager** — 项目列表和加载
- **SimulatorManager** — 模拟器生命周期（boot/shutdown via `SimctlClient`）
- **SimulatorStreamManager** — ScreenCaptureKit + Metal 渲染屏幕捕获
- **ASCManager** — App Store Connect API 集成
- **ProjectSetupManager** — 项目脚手架（blitz / react-native / swift / flutter）

### 4.2 MCP 服务器（核心亮点）

```
Claude Code ←stdio→ Bridge Script (~/.blitz/blitz-mcp-bridge.sh) ←HTTP→ MCPServerService (Swift actor)
```

- **MCPServerService** — 动态端口 TCP HTTP 服务器，端口写入 `~/.blitz/mcp-port`，处理 `/mcp` JSON-RPC 请求
- **MCPRegistry** — 静态定义所有 ~35 个工具（导航、项目、模拟器、设置、设备交互、ASC 表单、构建管线）
- **MCPExecutor** — 执行工具调用。只读工具直接执行；修改类工具走审批流（continuation-based），弹原生 macOS alert
- 按领域拆分执行器：`MCPExecutorASC`、`MCPExecutorBuildPipeline`、`MCPExecutorTabState`、`MCPExecutorAppNavigation`、`MCPExecutorProjectEnvironment`
- `ApprovalRequest` model + `ToolCategory` enum 决定是否需要用户审批

### 4.3 设备交互

统一 `DeviceInteractionService` actor，两条路径：

- **模拟器**: `SimctlClient`（xcrun simctl，生命周期）+ `IDBClient`（idb CLI，触摸/滑动/describe）
- **真机**: `WDAClient`（WebDriverAgent HTTP API port 8100，触摸/滑动/截图）

### 4.4 屏幕捕获

`SimulatorCaptureService` 使用 ScreenCaptureKit `SCStream` 捕获 Simulator.app 窗口 → `MetalRenderer` (Metal pipeline) 渲染帧。Tab 切换时暂停/恢复以节省资源。

### 4.5 导航

`AppTab` 枚举定义 13 个标签页，分 5 组：

| 组 | 标签 |
|---|---|
| 顶层 | Dashboard, App |
| Release | App Information, Screenshots, Monetization, Review |
| Insights | Analytics, Reviews |
| TestFlight | Builds, Groups, Beta Info, Feedback |
| Settings | Settings |

`ContentView` 使用 `NavigationSplitView`（SidebarView + DetailView）。

### 4.6 项目存储

项目位于 `~/Library/Application Support/Blitz/projects/{projectId}/`，每个项目有 `.blitz/project.json` 元数据。

## 5. 关键模式

- 所有需要隔离的服务使用 Swift `actor`
- UI 变更通过 `@MainActor` / `MainActor.run`
- 外部进程：`ProcessRunner.run()`（async 一次性）或 `ProcessRunner.stream()`（长时运行 + stdout/stderr 回调）
- 使用 `@Observable`（Observation framework）而非 `ObservableObject`/`@Published`
- ASC helper 通过 git submodule 引入 `deps/App-Store-Connect-CLI-helper`（Go 编译）

## 6. 复杂度热点（Top 10 文件）

| 文件 | 行数 | 职责 |
|---|---|---|
| ASCService.swift | 1928 | App Store Connect API 核心服务 |
| MCPExecutorASC.swift | 1574 | ASC 相关 MCP 工具执行 |
| PricingView.swift | 1144 | 定价 UI |
| BuildPipelineService.swift | 1126 | 构建管线服务 |
| ScreenshotsView.swift | 1066 | 截图管理 UI |
| OnboardingView.swift | 910 | 首次引导 |
| ASCOverview.swift | 844 | ASC 总览 |
| ASCModels.swift | 789 | ASC 数据模型 |
| ASCScreenshotsManager.swift | 773 | 截图管理器 |
| ASCMonetizationManager.swift | 728 | 变现管理器 |

## 7. 安全设计

- MCP 服务器绑定 `127.0.0.1`，不暴露网络
- 修改类 MCP 工具需要用户在 macOS 弹窗中审批
- 遥测仅在官方 release 构建中启用，匿名设备 ID，不记录项目名/路径/表单内容
- 屏幕捕获限于 iOS Simulator 窗口

## 8. 关联

- [[gstack]] — 同类 AI 编码工具链，gstack 的 browse skill 可用于 Blitz QA
- [[ruflo]] — 多 Agent 编排平台，MCP 生态交叉
- [[context-mode]] — MCP Server 解决上下文窗口问题，Blitz 亦是 MCP 生态一员
- [[heuristic-learning]] — AI 编码 Agent 行为塑造，Blitz 的 MCP 审批流是 agent guardrail 实例
- [[slack]] — 同为原生平台应用，PLG 增长路径可参考

## 最新动态（截至 2026-06-28）

> [!note] 从"ASC 提交工具"扩展为"iOS 全生命周期 agent 客户端"，搭上 Apple MLX agentic AI 东风
> Blitz 团队 2026 年推出姊妹项目 **iPhone-mcp**（agent 控制真机/模拟器），WWDC26 同期 Apple 主推 Mac 本地 agentic AI（MLX），Blitz 正好卡位。

### 关键演进

| 维度 | 原调研（2026-05）| 2026-06 现状 |
|------|------------------|-------------|
| 范围 | ASC 提交 pipeline | **+ iOS 全生命周期**（build/test/simulator/TestFlight/submit）|
| 生态 | 单项目 | **+ iPhone-mcp 姊妹项目**（agent 控制真机）|
| 行业背景 | MCP 新兴 | **WWDC26 Apple 主推本地 agentic AI（MLX）** |

### 生态信号
- **iPhone-mcp**：同一团队推出，让 agent 控制真实 iPhone 和模拟器，覆盖 Claude Code/Cursor/Codex/OpenCode 等 MCP 客户端
- **WWDC26 Session 232**：Apple 官方推 Mac 本地 agentic AI（MLX），Blitz 的"macOS 原生 + MCP"路线与官方趋势一致
- **dev.to/HN 热议**：多篇自动化 App Store 提交教程涌现，社区采用度上升

### 战略意义
Blitz 代表了 **"垂直行业 API → MCP 化"** 的范式——把 Apple 私有/公共 ASC API 包装成 MCP 工具，让任何 agent 能驱动。这与 [[automaton]]（经济 API 化）、[[ruflo]]（编排 API 化）是同一趋势的不同切面。

### 仍待观察
- Apple 官方是否会推出竞品 ASC agent 工具
- iPhone-mcp 的真机控制安全边界
