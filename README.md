# Ob-wiki 文档站

基于 [Quartz v5](https://quartz.jzhao.xyz/) 构建的 Obsidian 知识库公开站点。

🔗 站点：<https://sendwealth.github.io/Ob-wiki-site/>
📦 笔记源仓（私有）：<https://github.com/sendwealth/Ob-wiki>

## 目录结构

```
Ob-wiki-site/
├── content/              # 笔记内容（由源仓 Ob-wiki 同步而来，请勿直接编辑）
│   ├── concepts/         # 抽象概念、方法论、协议
│   ├── entities/         # 具体实体：组织、产品、项目
│   ├── comparisons/      # 竞品分析、横向对比
│   ├── index.md          # 全量索引（首页）
│   ├── log.md            # 操作日志
│   └── SCHEMA.md         # 知识库约定
├── quartz.config.yaml    # Quartz 配置（站点标题、主题、插件、布局）
├── quartz/               # Quartz 构建器源码（来自上游 fork）
└── .github/workflows/
    └── deploy.yml        # GitHub Actions：push 到 v5 自动部署到 Pages
```

> 笔记的**唯一权威源是 [Ob-wiki](https://github.com/sendwealth/Ob-wiki)**。
> 本仓库的 `content/` 是同步镜像，发布流程见源仓的 `.github/workflows/publish-site.yml`。

## 本地预览

```bash
npm ci                    # 首次安装依赖（Node >= 22）
npx quartz build --serve  # 构建并在 http://localhost:8080 预览
```

改配置或笔记后会自动热重载。

## 发布流程

1. 在源仓 `Ob-wiki` 编辑笔记并 push 到 `main`
2. 源仓的 `publish-site.yml` 自动把笔记同步到本仓 `content/`（排除 `raw/`、`_archive/`）
3. 本仓 `deploy.yml` 自动构建并部署到 GitHub Pages

也可手动触发：GitHub → Actions → Deploy Quartz to GitHub Pages → Run workflow。

## 自定义

- **站点标题/主题/插件**：编辑 `quartz.config.yaml`
- **改用自定义域名**：重新启用 `cname` 插件，并把 `configuration.baseUrl` 改成你的域名
- **同步逻辑**：见源仓 `Ob-wiki/.github/workflows/publish-site.yml`

---

Built with [Quartz](https://quartz.jzhao.xyz/) · 起点仓库 fork 自 [jackyzha0/quartz](https://github.com/jackyzha0/quartz)
