---
title: Zed 文档管理体系
created: 2026-05-22
updated: 2026-05-22
type: concept
tags: [documentation, open-source, practices, architecture, rust, zed]
sources: [~/Projects/zed/docs/]
confidence: high
---

# Zed 文档管理体系

> Zed 的文档系统是一个工程化的知识产品：mdBook 构建 + Rust 预处理器 + 8 项品牌声音评分卡 + Prettier 强制格式化 + 金标范例模板 + 完整的质量检查清单。

---

## 1. 文档架构

```
docs/
├── book.toml              # mdBook 配置（site-url: /docs/）
├── AGENTS.md              # Agent 自动化规则（安全约束、变更分类）
├── README.md              # 写作指南（voice/tone/formatting）
├── .rules                 # 文档质量规则
├── .conventions/          # 约定体系
│   ├── CONVENTIONS.md     # 结构约定（页面/节/格式/术语/质量检查清单）
│   └── brand-voice/       # 品牌声音
│       ├── SKILL.md       # 核心声音原则和工作流
│       ├── rubric.md      # 8 项评分标准（每项 1-5 分，全部 ≥4 才通过）
│       ├── taboo-phrases.md  # 禁用词列表
│       └── voice-examples.md # 改写前后对照
├── .doc-examples/         # 金标范例
│   ├── simple-feature.md  # 简单功能文档模板
│   ├── complex-feature.md # 复杂功能文档模板
│   ├── configuration.md   # 配置文档模板
│   └── reference.md       # 参考文档模板
├── src/                   # 文档源文件
│   ├── SUMMARY.md         # mdBook 目录结构
│   ├── ai/                # AI 功能文档（17 个页面）
│   ├── collaboration/     # 协作功能
│   ├── business/          # 企业功能
│   ├── development/       # 开发者文档
│   ├── extensions/        # 扩展开发
│   └── languages/         # 语言支持文档（50+ 语言）
└── theme/                 # mdBook 主题定制
```

## 2. 构建系统

### mdBook + 自定义渲染器

- **构建工具**：mdBook（Rust 生态标准文档工具）
- **自定义渲染器**：`zed-html` — 包装 mdBook 内置 HTML 渲染器 + 后处理
- **自定义预处理器**：`docs_preprocessor` crate（Rust 编写）
  - 展开 `{#kb action::ActionName}` → 动态渲染键绑定
  - 展开 `{#action git::Commit}` → 渲染 action 名称
  - 键绑定从代码自动提取，文档永远准确

### 旧页面重定向

`book.toml` 中配置了 URL 重定向映射（如 `/assistant-panel.html` → `/docs/ai/agent-panel.html`），确保旧链接不失效。

## 3. 写作哲学

### 核心原则

| 原则 | 描述 |
|------|------|
| **实用优先** | 关注用户能做什么，不卖产品。禁用 "powerful"、"revolutionary" |
| **诚实面对局限** | 缺功能直接说，配 workaround |
| **直接简洁** | 短句，快速到点。开发者扫描不阅读 |
| **第二人称** | 称呼读者为 "you"，不用 "the user" |
| **现在时** | "Zed opens the file" 不说 "will open" |

### 禁用模式

- 无实质的最高级（"incredibly fast"）
- 犹豫词（"simply"、"just"、"easily"）— 如果简单，指令自然展示
- 道歉语气 — 说明局限后继续
- 贬低竞品 — 事实对比，不用攻击性语言
- LLM 话术（"entirely"、"certainly"、"deeply"、"definitely"）

## 4. 8 项品牌声音评分卡

每篇文档必须 **全部 ≥4 分** 才能通过：

| # | 评分项 | 5 分标准 |
|---|--------|----------|
| 1 | Technical Grounding | 精确、可验证的技术细节 |
| 2 | Natural Syntax | 自然的句子结构，朗读流畅 |
| 3 | Conciseness | 每句话传递新信息，无冗余 |
| 4 | Voice Consistency | 一致的品牌声音，不漂移 |
| 5 | Specificity | 具体场景和例子，非泛泛而谈 |
| 6 | Actionability | 读者看到就知道怎么做 |
| 7 | Honest Framing | 不回避局限，提供背景 |
| 8 | Reader Respect | 不居高临下，不废话 |

## 5. 页面结构模板

### 标准顺序

1. **Title** (`# Feature Name`) — 清晰可扫描
2. **Opening paragraph** — 这是什么、为什么用（1-2 句）
3. **Getting Started / Usage** — 如何访问或启用
4. **Core functionality** — 主要功能和工作流
5. **Configuration** — 设置 + JSON 示例
6. **Keybindings / Actions** — 参考表格
7. **See Also** — 关联文档链接

### Frontmatter（必须）

```yaml
---
title: Feature Name - Zed
description: 一句话描述页面内容，用于搜索结果
---
```

### 何时创建新页面 vs 添加到现有页面

| 变更 | 操作 |
|------|------|
| 重大新功能 | 新建页面 |
| 新设置项 | 添加到已有页面 |
| 新键绑定 | 添加到已有功能 |
| 新 AI 提供商 | 添加到 `llm-providers.md` |
| 新的配置选项 | 添加到已有功能 |

## 6. 格式约定

### 键绑定
- 用 `{#kb action::ActionName}` 动态渲染（自动跟踪变更）
- 代码格式：`Cmd+Shift+P`
- 同时展示 macOS 和 Linux/Windows：`Cmd+,` (macOS) or `Ctrl+,` (Linux/Windows)

### JSON 示例
- 始终用 `[settings]` 或 `[keymap]` 注解
- 展示完整可用的 JSON，不展示片段
- UI 方式优先，JSON 作为补充

### 表格
- 用于键绑定对比、设置映射、功能对比
- 保持简洁，避免长段落

### Callouts
- `> **Tip:**` 实用建议
- `> **Note:**` 需注意的信息
- `> **Warning:**` 不可逆操作

## 7. 术语一致性

| 用 | 不用 |
|---|------|
| folder | directory |
| project | workspace |
| Settings Editor | settings UI |
| command palette | command bar |
| panel | sidebar |
| language server | LSP（首次全拼） |

## 8. 质量检查清单

每篇文档合并前必须通过：

- [ ] Frontmatter 包含 `title` 和 `description`
- [ ] 开头段落解释了是什么和为什么
- [ ] 设置先展示 UI，再展示 JSON
- [ ] Action 使用 `{#action ...}` 和 `{#kb ...}` 语法
- [ ] 所有 action 都已文档化（完整性）
- [ ] 锚点 ID 在可能被链接的节上
- [ ] 版本差异有版本号标注
- [ ] 无孤立页面（从某处可达）
- [ ] 至少 3 个内部文档链接
- [ ] 通过 Prettier 格式化（80 字符行宽）
- [ ] 通过品牌声音评分卡（8 项全 ≥4）

## 9. 文档范围决策

### 必须文档化
- 新的用户可见功能
- 新的设置/配置选项
- 新的键绑定/命令
- 所有 action（完整性优先）
- 新的 AI 能力（工具、提供商、工作流）
- 新的 UI 面板/视图
- 公共扩展 API
- 破坏性变更
- 版本特定行为变更

### 不需要文档化
- 内部重构
- Bug 修复（除非修复说明现有文档是错的）
- 性能改进（除非用户可感知）
- 测试变更
- CI/工具变更

## 10. 设计亮点

1. **键绑定自动同步** — `{#kb ...}` 从代码提取，文档永远准确
2. **8 项评分卡** — 量化质量控制，不是主观判断
3. **金标范例** — 4 种文档类型各有模板，新贡献者有参考
4. **禁用词列表** — 明确列出要避免的 LLM 话术和营销废话
5. **Prettier 强制** — 格式问题在 CI 拦截，不进入 review
6. **旧链接重定向** — 页面移动时旧 URL 不失效
7. **PR Release Notes** — 文档变更标记 `N/A`，不混入产品 release notes

## 11. 与其他项目对比

| 实践 | Zed | 一般开源项目 |
|------|-----|-------------|
| 品牌声音评分 | 8 项量化评分卡 | 无或主观判断 |
| 金标范例 | 4 种模板 | 无 |
| 禁用词列表 | 有，明确列出 LLM 话术 | 无 |
| 格式化 | Prettier CI 强制 | 手动或无 |
| 键绑定同步 | 代码自动提取 | 手动维护 |
| 旧链接管理 | 重定向映射 | 通常忽略 |

---

关联：[[zed]] — Zed 编辑器概览 | [[zed-agent-architecture]] — Agent 系统架构 | [[opensource-project-practices-from-openhuman]] — OpenHuman 开源实践 | [[heuristic-learning]] — Agent 学习范式
