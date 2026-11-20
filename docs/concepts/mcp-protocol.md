---
title: MCP 协议
created: 2026-11-20
updated: 2026-11-20
type: concept
tags: [mcp, protocol, ai, agent, tooling, interoperability]
confidence: medium
---

# MCP 协议（Model Context Protocol）

> MCP（Model Context Protocol）是 Anthropic 于 2024 年 11 月开源发布的开放协议，为 LLM 应用与外部数据源和工具之间提供标准化的连接方式。常被类比为"AI 应用的 USB-C"：一次接入，任意支持 MCP 的客户端都能使用同一个工具服务器。

## 解决的问题

在 MCP 出现之前，每个 AI 应用（ChatGPT、Claude Desktop、IDE 插件等）接外部工具（数据库、文件系统、搜索 API）都要写各自的集成代码，M×N 的集成问题。MCP 把它变成 M+N：工具方实现一次 MCP server，客户端方实现一次 MCP client，双方通过协议互操作。

## 核心概念

- **Host / Client**：运行 LLM 的应用（如 Claude Desktop、Open WebUI、各类 IDE），内部为每个连接创建 MCP client。
- **Server**：暴露能力的轻量进程，通过 stdio 或 HTTP（Streamable HTTP，早期为 SSE）与 client 通信。
- **三大原语**：
  - **Tools** — 可被模型调用的函数（如查数据库、发消息），由模型决定何时调用；
  - **Resources** — 可读取的数据（文件内容、数据库记录），由应用控制加载；
  - **Prompts** — 预置的提示词模板，供用户主动调用。
- **能力协商**：初始化握手时双方交换支持的特性（tools/resources/prompts、sampling、roots 等），保证向后兼容。
- **消息格式**：基于 JSON-RPC 2.0。

## 生态与定位

- 2024-11 由 Anthropic 发布并开源 SDK（TypeScript、Python 等）；2025 年被 OpenAI、Google DeepMind 等主流厂商采纳，成为事实上的工具连接标准。
- 与 [[a2a-protocol]] 互补：MCP 解决 **agent ↔ 工具** 的连接，A2A 解决 **agent ↔ agent** 的协作。
- 典型用法：本地 MCP server 包装文件系统/Git；远程 MCP server 暴露 SaaS API；客户端（Claude Code、Open WebUI 等）聚合多个 server 的工具供模型调用。

## 相关

- [[a2a-protocol]] — Agent 间协作协议，与 MCP 互补
- [[acp-protocol]] — 另一层面的 Agent 通信协议
- [[ai-agent-ecosystem]] — Agent 生态中协议层的位置
