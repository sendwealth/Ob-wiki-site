# Ob-wiki 文档站

基于 [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) 构建的 Obsidian 知识库公开站点。

🔗 站点：<https://sendwealth.github.io/Ob-wiki-site/>
📦 笔记源仓（私有）：<https://github.com/sendwealth/Ob-wiki>

## 目录结构

```
Ob-wiki-site/
├── docs/                # 笔记内容（由源仓 Ob-wiki 同步而来，请勿直接编辑）
│   ├── concepts/        # 抽象概念、方法论、协议
│   ├── entities/        # 具体实体：组织、产品、项目
│   ├── comparisons/     # 竞品分析、横向对比
│   ├── index.md         # 全量索引（首页）
│   ├── log.md           # 操作日志
│   └── SCHEMA.md        # 知识库约定
├── scripts/
│   └── gen_index_pages.py  # 从 frontmatter 生成分区列表页
├── mkdocs.yml           # MkDocs 配置（主题、插件、导航）
├── requirements.txt     # Python 依赖
└── .github/workflows/
    └── deploy.yml       # GitHub Actions：push 到 v5 自动部署到 Pages
```

> 笔记的**唯一权威源是 [Ob-wiki](https://github.com/sendwealth/Ob-wiki)**。
> 本仓库的 `docs/` 是同步镜像，发布流程见源仓 `.github/workflows/publish-site.yml`。

## Obsidian 语法支持

无需预处理脚本，以下 Obsidian 语法直接支持：

| 语法 | 处理方式 |
|---|---|
| `[[wikilinks]]` / `[[a\|别名]]` / `[[a#章节]]` | `mkdocs-roamlinks-plugin` |
| `> [!warning]` / `> [!note]` 等 callout | `mkdocs-callouts` → Material admonition |
| `![[image.png]]` 嵌入引用 | `mkdocs-roamlinks-plugin` |
| 中文搜索 | Material + `jieba` 分词 |

## 本地预览

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve                 # http://127.0.0.1:8000/Ob-wiki-site/
```

## 发布流程

1. 在源仓 `Ob-wiki` 编辑笔记并 push 到 `main`
2. 源仓 `publish-site.yml` 同步笔记到本仓 `docs/`（排除 `raw/`、`_archive/`），并生成分区列表页
3. 本仓 `deploy.yml` 用 MkDocs 构建并部署到 GitHub Pages

## 自定义

- **主题/配色/功能**：编辑 `mkdocs.yml`
- **导航**：由 `awesome-pages` 插件从目录自动生成，见各目录的 `.pages` 文件
- **列表页样式**：编辑 `docs/css/extra.css`

---

Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
