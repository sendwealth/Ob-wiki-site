---
title: little-talk 网文写作工具集
created: 2026-11-02
updated: 2026-11-02

type: entity
tags: [project, active, ai-writing, web-novel, zcode-skills]
sources: [~/Projects/little-talk]
confidence: high
---

# little-talk 网文写作工具集

> [!summary] 自有探索项目（active）。用 ZCode Skills + Hooks 把网文创作全流程工程化：13 个 story-* Skill 覆盖「写/拆/扫/审/导入」，Hook 做机械守卫，结构化追踪系统支撑千章级连续性，直通番茄平台发布。

## 探索目标

1. Skill 化写作流水线能否稳定产出可直接平台发布的网文（质量与产能 vs 纯手写）？
2. 千章规模下，结构化追踪（`_tracking-state.json` 单一事实源）能否守住伏笔、角色状态与时间线的连续性？
3. Agent 生成文本的「AI 味」能否通过流程化 deslop 持续消除，而非逐章手工修？

## 当前结论

（2026-11-02 入册时快照）

- **工具链成型**：AGENTS.md 路由表 + 13 个 story-* Skill（long/short-write、long/short-analyze、long/short-scan、deslop、cover、review、import、setup、模糊分发 story）+ browser-cdp；ZCode 不执行自定义 Agent，统一降级 solo 并报告 Fallback。
- **质量双守卫**：PreToolUse Hook 保证「无细纲不写正文」；PostToolUse Hook 检查落盘、截断、占位符、工程词泄漏、复读、标题重复；字数只由流程末端一次 chapter check 测量，避免多口径。
- **追踪体系**：`追踪/_tracking-state.json` 唯一结构化权威，派生 7 栏 `上下文.md`（Compact 后恢复入口）、伏笔视图、角色快照、双时间线、逐章记录，全部由追踪工具生成。
- **商业化通路**：`上传_番茄/` + `自动发布/` 目录打通番茄平台发布。

## 时间线

- **2026-11-02** — 入册 Ob-wiki，按「自己探索的项目」模式管理（单主页 + raw 子目录 + active 标签）。
- **2026-09-17 ~ 10-01** — 《散财成神》密集质检迭代：返修/清账/裁定/deslop/修正五类备份快照 16+ 份；ch5/ch6/ch7/ch32 逐章事务文件。
- **（更早历史待补）**

## 产出与链接

- 仓库：`~/Projects/little-talk`（入口约定见 AGENTS.md）
- 《散财成神》：大纲/设定/追踪/对标/质检/封面/正文（至第 1210 章）/上传_番茄/自动发布
- 《朕的2027》：大纲/设定/追踪/参考资料/正文（至第 600 章）

## Wikilinks

- [[agent-world]] — 另一个自有探索项目（智能体生存沙盒设计），同属「自己下场做实验」线
- [[humanizer-skill]] — AI 写作痕迹检测与消除方法论，story-deslop 的同方向参照
- [[ai-short-drama-workflow]] — 同属 AI 内容生产工作流封装方向
- [[diary-to-book-skill]] — Skill 封装方法论：问题驱动迭代、骨架来自用户口述
- [[adapted-6plus1-rss-obsidian-kb]] — log.md 单一事实源的知识库设计，与 _tracking-state.json 思路相通
