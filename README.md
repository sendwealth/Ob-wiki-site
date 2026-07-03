# Ob-wiki 文档站

基于 [MkDocs Material](https://squidfunk.github.io/mkdocs-material/) 构建的 Obsidian 知识库公开站点。

> 🔗 站点：<https://sendwealth.github.io/Ob-wiki-site/>
> 📦 笔记源仓（私有）：<https://github.com/sendwealth/Ob-wiki>

本仓库是发布站。`docs/` 是从源仓同步来的镜像，**不要直接编辑 `docs/` 下的笔记**——去源仓改，同步过来才会生效。本 README 说明仓库运维。

---

## 目录结构

```
Ob-wiki-site/
├── docs/                # 笔记内容（源仓同步而来，勿直接编辑）
│   ├── concepts/        # 抽象概念、方法论、协议
│   ├── entities/        # 具体实体：组织、产品、项目
│   ├── comparisons/     # 竞品分析、横向对比
│   ├── index.md         # 全量索引（首页）
│   ├── log.md           # 操作日志
│   ├── SCHEMA.md        # 知识库约定
│   ├── .pages           # awesome-pages 导航配置（每分区也有）
│   └── css/extra.css    # 自定义样式（坏链红字标记等）
├── scripts/
│   └── gen_index_pages.py   # 从 frontmatter 生成分区列表页（CI 会自动跑）
├── mkdocs.yml           # MkDocs 配置（主题、插件、导航、扩展）
├── requirements.txt     # Python 依赖（版本锁定）
└── .github/workflows/
    └── deploy.yml       # GitHub Actions：push 到 v5 → 构建 → 部署 Pages
```

---

## 发布流程（自动）

```
源仓 Ob-wiki 写笔记 → push main
    │
    ▼  源仓 publish-site.yml
Ob-wiki-site/docs/（本仓库，push 到 v5 分支）
    │  排除 raw/、_archive/，生成分区列表页
    ▼  本仓 deploy.yml
MkDocs build → GitHub Pages
    │
    ▼
https://sendwealth.github.io/Ob-wiki-site/
```

**正常无需手动操作**：源仓笔记一改，几分钟内自动同步 + 重新部署。

---

## 本地预览

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
mkdocs serve                 # → http://127.0.0.1:8000/Ob-wiki-site/
```

改 `mkdocs.yml` 或 `docs/` 会自动热重载。

---

## 技术栈

| 组件 | 作用 |
|---|---|
| `mkdocs-material` | 主题：顶部 tab 导航、深浅色切换、Material Design |
| `mkdocs-roamlinks-plugin` | `[[wikilinks]]` 全语法（含 `[[a\|别名]]`、`[[a#章节]]`、`![[img]]`） |
| `mkdocs-callouts` | `> [!warning]` Obsidian callout → Material admonition |
| `mkdocs-awesome-pages-plugin` | 从目录结构自动生成侧栏导航（配合 `.pages` 文件） |
| `jieba` | 中文搜索分词 |

无需任何预处理脚本，Obsidian 语法直接支持。

---

## ⚠️ 维护红线（防止发布出错）

### 1. 构建用 `mkdocs build`，不要加 `--strict`

知识库里有约 20 处悬空 wikilinks（指向计划写但尚未创建的笔记），这是正常状态。`--strict` 会把它们当致命错误导致部署失败。坏链由 `docs/css/extra.css` 的红字标记辅助排查。

### 2. 改插件版本要同步更新两处

升级 `mkdocs-material` 或任何插件时：
1. 改 `requirements.txt` 的版本号
2. 本地 `pip install -r requirements.txt && mkdocs build` 验证通过
3. 提交——CI 会用 `requirements.txt` 装同样的版本

**不要只改本地 `.venv` 不改 `requirements.txt`**，否则 CI 环境版本不一致会出诡异问题。

### 3. 分区列表页是自动生成的

`docs/concepts/index.md`、`docs/entities/index.md`、`docs/comparisons/index.md` 由 `scripts/gen_index_pages.py` 从 frontmatter 的 `title` 生成。**不要手编这几个文件**，每次部署会被覆盖。

新增分区时，在 `gen_index_pages.py` 的 `SECTIONS` 列表里加上，并放一个 `.pages` 文件。

### 4. `mkdocs.yml` 的搜索语言配置

中文搜索依赖 `plugins.search.lang` 含 `ja`（jieba 无独立 lang key，借 CJK 触发）。**不要删掉 `ja`**，否则中文分词失效。

### 5. baseUrl 不要改

`site_url` 配的是 `https://sendwealth.github.io/Ob-wiki-site/`（Project Pages 子路径）。改用自定义域名时才动这里，同时启用 cname 插件。

---

## CI 详解

### `.github/workflows/deploy.yml`

触发：push 到 `v5` 分支（源仓同步会触发）或手动。

步骤：
1. checkout（`fetch-depth: 0`，为 git-revision-date 取日期）
2. setup-python + `pip install -r requirements.txt`（带 pip 缓存）
3. `python scripts/gen_index_pages.py docs`（生成分区列表页）
4. `mkdocs build`（产物在 `site/`）
5. `upload-pages-artifact` → `deploy-pages`

### 源仓的 `publish-site.yml`

触发：源仓 push 到 main 且 paths 匹配笔记目录。它 checkout 本仓、清空 `docs/`、拷贝笔记、生成列表页、push 回来——从而触发本仓的 deploy。

---

## 常见问题

**Q：部署失败 `error_count: N` / `Deployment failed, try again later`？**
GitHub Pages 侧的瞬时错误（构建本身是成功的）。在 Actions 页面点 "Re-run failed jobs" 即可。

**Q：某页面内容显示乱 / 代码块吞掉后续内容？**
源笔记的 frontmatter 或代码块不是合法语法（如未闭合的 ` ``` `）。到源仓修正该笔记后重新 push。常见坑见源仓 `SCHEMA.md` 的 Frontmatter 章节。

**Q：wikilink 显示红字？**
目标笔记尚未创建（正常待办提示）。若目标笔记已存在但仍红字，检查文件名大小写/连字符是否匹配。

**Q：网站打不开但 CI 显示成功？**
检查本地网络代理（Clash/Surge 等）是否拦截了 `*.github.io`。`198.18.x.x` 是代理 fake-ip，会中断 TLS。用手机流量验证，或给代理加 `DOMAIN-SUFFIX,github.io` 规则。

**Q：要加新插件 / 改主题？**
1. `pip install <plugin>` → 改 `requirements.txt`
2. 在 `mkdocs.yml` 的 `plugins` 启用
3. 本地 `mkdocs serve` 验证
4. 提交推送

---

## 自定义速查

| 想改什么 | 改哪里 |
|---|---|
| 站点标题 / 配色 / 字体 | `mkdocs.yml` 的 `site_name` / `theme.palette` / `theme.font` |
| 顶部 tab 导航 | `docs/.pages` 的 `nav` |
| 侧栏分区标题 | 各分区的 `.pages`（如 `docs/concepts/.pages`） |
| 坏链标记样式 | `docs/css/extra.css` |
| 新增分区列表页 | `scripts/gen_index_pages.py` 的 `SECTIONS` |
| 底部社交链接 | `mkdocs.yml` 的 `extra.social` |

---

## 相关仓库

- [Ob-wiki](https://github.com/sendwealth/Ob-wiki) — 笔记源仓（Obsidian vault，私有）

---

Built with [MkDocs Material](https://squidfunk.github.io/mkdocs-material/)
