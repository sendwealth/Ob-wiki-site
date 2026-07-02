1|---
2|title: Wiki Schema
3|created: 2026-05-04
updated: 2026-06-28
type: meta
tags: [schema]
---

# Wiki Schema
10|
11|## Domain
12|
13|产品调研、竞品分析、技术架构深度研究、开源项目实践总结、AI Agent 生态、协议规范、设计系统。
14|
15|## Wiki Structure
16|
17|```
18|Ob-wiki/
19|  SCHEMA.md          — 本文件：约定与规则
20|  index.md           — 主索引（创建页面时必须更新）
21|  log.md             — 操作日志（创建页面时必须追加）
22|  concepts/          — 抽象概念：框架、方法论、协议、架构模式
23|  entities/          — 具体实体：组织、产品、人、项目
24|  comparisons/       — 竞品分析、横向对比
25|  raw/               — 未处理的原始资料
26|    articles/
27|    transcripts/
28|```
29|
30|### concepts vs entities 判断标准
31|
32|- **entities/** — 有名字的具体东西（人、公司、产品、项目）。问"这是谁/什么东西"有答案。
33|- **concepts/** — 抽象的想法、框架、方法论、协议。问"这是一种什么方法/概念"有答案。
34|- **comparisons/** — 两个以上实体的对比分析。
35|
36|边界模糊时：紧密绑定某个具体项目的分析放 entities，通用概念放 concepts。
37|
38|## Conventions
39|
40|- 文件名：小写、连字符、无空格。例：`acp-protocol.md`（不是 `ACP Protocol.md`）
41|- 每页必须有 YAML frontmatter（title, created, updated, type, tags, sources, confidence）
42|- 使用 `[[wikilinks]]` 链接，每页至少 2 个出链
43|- 更新页面时 bump `updated` 日期
44|- 新页面必须加入 `index.md`（对应 section，bump 页数和日期）
45|- 每次操作追加 `log.md`（日期、文件名、摘要、关联）
46|- 永远不要把笔记保存到 vault 根目录
47|
48|## Frontmatter
49|
50|```yaml
51|