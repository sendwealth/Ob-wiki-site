---
title: Wiki Schema
created: 2026-05-04
updated: 2026-07-03
type: meta
tags: [schema]
---

# Wiki Schema

## Domain

产品调研、竞品分析、技术架构深度研究、开源项目实践总结、AI Agent 生态、协议规范、设计系统。

## Wiki Structure

```
Ob-wiki/
  SCHEMA.md          — 本文件：约定与规则
  index.md           — 主索引（创建页面时必须更新）
  log.md             — 操作日志（创建页面时必须追加）
  concepts/          — 抽象概念：框架、方法论、协议、架构模式
  entities/          — 具体实体：组织、产品、人、项目
  comparisons/       — 竞品分析、横向对比
  raw/               — 未处理的原始资料
    articles/
    transcripts/
```

### concepts vs entities 判断标准

- **entities/** — 有名字的具体东西（人、公司、产品、项目）。问"这是谁/什么东西"有答案。
- **concepts/** — 抽象的想法、框架、方法论、协议。问"这是一种什么方法/概念"有答案。
- **comparisons/** — 两个以上实体的对比分析。

边界模糊时：紧密绑定某个具体项目的分析放 entities，通用概念放 concepts。

## Conventions

- 文件名：小写、连字符、无空格。例：`acp-protocol.md`（不是 `ACP Protocol.md`）
- 每页必须有 YAML frontmatter（title, created, updated, type, tags, sources, confidence）
- 使用 `[[wikilinks]]` 链接，每页至少 2 个出链
- 更新页面时 bump `updated` 日期
- 新页面必须加入 `index.md`（对应 section，bump 页数和日期）
- 每次操作追加 `log.md`（日期、文件名、摘要、关联）
- 永远不要把笔记保存到 vault 根目录

## Frontmatter

每页 frontmatter 字段规范：

```yaml
---
title: 页面标题（必填，含冒号时用引号包裹）
created: YYYY-MM-DD        # 创建日期
updated: YYYY-MM-DD        # 最后更新日期，改页面时 bump
type: concept              # concept | entity | comparison | meta
tags: [tag1, tag2]         # 小写连字符标签；含 # 或冒号时用引号包裹
sources: [url1, url2]      # 来源链接（可选）
confidence: high           # high | medium | low（可选）
---
```

### YAML 注意事项

- `title` 含冒号（如 `MAKE: The Indie Maker Blueprint`）必须加引号：`title: "MAKE: ..."`
- `tags` / `sources` 用 flow 序列 `[a, b]` 时，若某项含 `#`（如 `PR #2613`）必须加引号：`["PR #2613"]`
- 日期格式统一 `YYYY-MM-DD`
