---
title: Design as Code
created: 2026-05-11
updated: 2026-05-11
type: concept
tags: [design-system, ai-design, design-as-code, agent]
sources: []
confidence: high
---

# Design as Code

## 是什么

将视觉设计系统编码为**纯文本 Markdown 文件**的范式，LLM 原生理解并遵循，无需 Figma/Sketch 中间导出。

## 对比传统方式

| 传统 | Design as Code |
|------|---------------|
| 设计师在 Figma 创作 | 编写 DESIGN.md |
| 导出 JSON/SVG 交付 | Markdown 放项目根目录 |
| 开发者手动还原 | AI 代理自动遵循 |
| 静态快照 | Git 友好，可 diff/merge |
| 工具特定格式 | 纯文本跨工具通用 |

## 核心优势

- **LLM 原生** — Markdown 零解析成本
- **即插即用** — 复制文件切换视觉风格
- **可组合** — 混搭不同 DESIGN.md 段落
- **版本控制** — 可 diff、可回滚
- **可验证** — CLI 自动 WCAG 对比度检查
- **可导出** — Tailwind theme JSON / W3C DTCG JSON

## 局限

- 规范仍为 alpha，可能有破坏性变更
- 侧重 Web/UI，3D/动画/复杂交互覆盖有限
- 需编码代理支持读取 DESIGN.md

## 相关

- [[design-md-spec]] — Google 官方规范 + CLI
- [[awesome-design-md]] — 73 个现成设计系统
