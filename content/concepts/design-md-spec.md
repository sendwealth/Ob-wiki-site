---
title: DESIGN.md 规范
created: 2026-05-11
updated: 2026-05-11
type: concept
tags: [design-system, tokens, ui, accessibility, spec, markdown, ai-design]
sources: []
confidence: high
---

# DESIGN.md 规范

## 是什么

Google Stitch 提出的开放规范（Apache-2.0，仓库 `google-labs-code/design.md`），用**单个 Markdown 文件**定义项目完整视觉设计系统。

核心类比：
- `AGENTS.md` → 告诉 AI 怎么**构建**项目
- `DESIGN.md` → 告诉 AI 项目应该**看起来怎样**
- `README.md` → 告诉人类项目是**什么**

## 文件结构

两部分组成：
1. **YAML front matter** — 机器可读 design tokens（颜色、字体、间距、组件）
2. **Markdown body** — 人类可读的设计理念、规范说明

### Token 类型

| 类型 | 格式 | 示例 |
|------|------|------|
| Color | `#` + hex | `"#1A1C1E"` |
| Dimension | number + unit | `48px`, `"-0.02em"` |
| Token ref | `{path.to.token}` | `{colors.primary}` |
| Typography | 对象 | fontFamily, fontSize, fontWeight, lineHeight, letterSpacing |

### 8 个标准章节（按序）

1. **Overview** — 品牌调性、设计哲学
2. **Colors** — 色板、语义色名、功能角色
3. **Typography** — 字体族、层级表
4. **Layout & Spacing** — 间距系统、网格、留白
5. **Elevation & Depth** — 阴影系统
6. **Shapes** — 圆角、形状
7. **Components** — 按钮、卡片、输入框等（变体是独立条目如 `button-primary-hover`）
8. **Do's and Don'ts** — 设计护栏

## CLI 工具

```bash
npx -y @google/design.md lint DESIGN.md          # 验证 + WCAG 对比度
npx -y @google/design.md diff A.md B.md          # 检测回归
npx -y @google/design.md export --format tailwind DESIGN.md  # 导出 Tailwind
npx -y @google/design.md export --format dtcg DESIGN.md      # 导出 DTCG JSON
```

### Lint 7 条规则

- `broken-ref` — token 引用不存在
- `duplicate-section` — 重复章节
- `invalid-color/dimension/typography` — 格式错误
- `wcag-contrast` — 对比度不足（warning）
- `unknown-component-property` — 非白名单属性（warning）

## 注意事项

- hex 颜色和负值 dimension 必须**引号包裹**
- Token 引用用点路径：`{colors.primary}`
- 当前版本 `version: alpha`（截至 2026-04）

## 相关

- [[awesome-design-md]] — 73 个现成 DESIGN.md 集合
- [[design-as-code]] — 设计即代码范式

## 来源

- 规范仓库：https://github.com/google-labs-code/design.md
- 文档：https://stitch.withgoogle.com/docs/design-md/overview/
