---
title: 从 Open Design 学习开源项目实践
created: 2026-05-20
updated: 2026-05-20
type: concept
tags: [opensource, practices, contributing, skill-system, plugin, design-system, code-review, monorepo, pnpm, typescript]
sources:
  - https://github.com/nicepkg/open-design
  - ~/Projects/open-design
  - CONTRIBUTING.md
  - docs/skills-protocol.md
  - docs/skills-contributing.md
  - docs/publishing-a-plugin.md
  - docs/code-review-guidelines.md
confidence: high
related:
  - "[[open-design-architecture]]"
  - "[[opensource-practices-from-lobechat]]"
  - "[[opensource-project-practices-from-multica]]"
  - "[[design-md-spec]]"
---

# 从 Open Design 学习开源项目实践

> Open Design (github.com/nicepkg/open-design) 是一个本地优先的开源 AI 设计工具，Apache-2.0 许可证。项目包含 129 个设计系统、31 个设计技能、18 种语言 i18n，是一个技术栈丰富、贡献体系完善的中大型开源项目。本文从贡献流程、Skill/Plugin 生态、代码审查、PR 工具链和社区治理五个维度提取可复用的开源项目实践方法论。

---

## 一、贡献者引导：三件事一下午能做

OD 的 `CONTRIBUTING.md` 开篇就列出三个新手友好的贡献入口：

| 贡献类型 | 工作量 | 入口 |
|---------|--------|------|
| 添加设计系统 | ~1 小时 | `design-systems/<brand>/DESIGN.md`，一个 Markdown 文件 |
| 添加设计技能 | ~2 小时 | `skills/<name>/SKILL.md`，复制最接近的 skill 改造 |
| 添加 coding-agent CLI 支持 | ~2 小时 | 按 agent-adapters 文档新增 adapter |

**可复用**：降低首次贡献门槛的关键是给出 "复制最近似的 → 改几个字段 → 跑起来 → 提 PR" 的明确路径，而不是 "先读完 10 页架构文档"。

### 本地开发一键启动

```bash
# Corepack 启用 pnpm
corepack enable

# 安装 + 启动
pnpm install
pnpm tools-dev        # 唯一的开发入口，启动 daemon + web

# 验证
pnpm guard            # 代码规范检查
pnpm typecheck        # 类型检查
```

**可复用**：开发环境启动命令控制在 3 步以内。`pnpm tools-dev` 是唯一的生命周期入口，避免 `pnpm dev`、`pnpm start`、`pnpm preview` 等碎片化命令。

---

## 二、Skill 生态：可组合的能力注册机制

OD 的核心扩展机制是 **Skill**——一个 Markdown 文件定义一种设计能力。

### Skill 三级发现与优先级

```
优先级（高 → 低）:
1. ./.claude/skills/    → 项目私有，不提交 git
2. ./skills/            → 项目提交，团队共享
3. ~/.claude/skills/    → 用户全局，跨项目
```

同名 skill 冲突时取高优先级版本。所有目录通过 `chokidar` 实时监听变更。

### Symlink 策略

借鉴 `cc-switch`，一个 skill 安装到中心位置后自动链接到各 agent 目录：

```
~/.open-design/skills/magazine-web-ppt/  (canonical)
~/.claude/skills/magazine-web-ppt → ~/.open-design/skills/magazine-web-ppt
~/.codex/skills/magazine-web-ppt  → ~/.open-design/skills/magazine-web-ppt
```

**可复用**：当项目需要支持多个外部工具的插件目录时，symlink 策略比重复安装更优雅。

### Skill 类型

| 类型 | 用途 | 举例 |
|------|------|------|
| `prototype-skill` | 生成 Web 原型 | web-prototype、dashboard、mobile-app |
| `deck-skill` | 生成 PPT | guizang-ppt、simple-deck、weekly-update |
| `template-skill` | 基于模板生成 | HTML PPT 模板系列 |
| `design-system-skill` | 注入设计系统上下文 | 129 个品牌 DESIGN.md |

### Skill 文件结构

```
skills/my-skill/
├── SKILL.md           # frontmatter (name, mode, trigger, scenario) + 指令正文
├── templates/         # 可选：种子模板文件
└── assets/            # 可选：静态资源
```

`SKILL.md` 的 frontmatter 扩展了 Claude Code 的 skill 协议，增加了 `od:` 前缀的 OD 特有字段（`mode`、`scenario`、`craft` 等），完全省略 `od:` 时 skill 仍可正常工作。

---

## 三、设计系统贡献：9 节 Schema + 双镜头审查

### DESIGN.md 9 节结构

每个设计系统是一个 `DESIGN.md` 文件，必须包含 9 个标准节：

```
1. Overview          # 品牌调性概述
2. Color Palette     # CSS 变量 + OKLch 色板
3. Typography        # 字体栈 (Display / Body / Mono)
4. Spacing & Layout  # 间距系统
5. Components        # 按钮、卡片、表单等
6. Motion            # 动效规则 + prefers-reduced-motion
7. Dark Mode         # [data-theme="dark"] 覆盖
8. Anti-patterns     # 明确禁止的做法
9. Locale Notes      # i18n 注意事项
```

### 双镜头审查框架

| 镜头 | 关注点 | 优先级 |
|------|--------|--------|
| **Lens A — 代码正确性** | CSS 变量命名、对比度、语法错误 | P1/P2（阻塞合并） |
| **Lens B — 推理完整性** | 足够让 agent 生成高质量设计的上下文 | P3（建议改进） |

### 预提交检查清单

```markdown
- [ ] 所有 9 节标题按顺序存在
- [ ] 无 #REPLACE_ME 或占位符 hex 代码
- [ ] CSS 变量包裹在 :root {} 中
- [ ] 字体标签块存在（Display / Body / Mono）
- [ ] [data-theme="dark"] 块覆盖而非复制 light tokens
- [ ] 交互组件有 :focus-visible 样式
- [ ] 所有颜色 token 4.5:1+ 对比度
- [ ] 无硬编码颜色（如 #ffffff），使用语义 token
- [ ] prefers-reduced-motion 针对特定元素，非 *
- [ ] Anti-patterns 具体且有边界，非模糊描述
```

**可复用**：对内容型贡献（非代码），标准化 schema + 自动化检查清单比 free-form 贡献更易维护质量。

---

## 四、Plugin 系统：从脚手架到注册表

OD 提供完整的插件生命周期工具链：

### 插件开发流程

```bash
# 1. 脚手架
od plugin scaffold --id figma-workflow --title "Figma workflow" --out ./plugins/community

# 2. 验证 + 打包
od plugin validate ./plugins/community/figma-workflow --no-daemon
od plugin pack ./plugins/community/figma-workflow

# 3. 认证
od plugin auth login

# 4. 发布
od plugin publish ./plugins/community/figma-workflow

# 5. 安装
od marketplace refresh official
od plugin install figma-workflow

# 6. 撤回
od plugin yank figma-workflow@1.0.0 --reason "security fix"
```

### 自托管注册表

支持多种注册表后端，共享同一 CLI 接口：

```bash
# 添加自定义注册表
od marketplace add https://example.com/open-design-marketplace.json --trust restricted
od marketplace refresh <id>
od marketplace search "deck" --json

# 健康检查
od marketplace doctor <id> --strict --json
```

注册表后端可替换：静态 JSON、GitHub PR、数据库（支持 SSO、审批流、审计日志）。

**可复用**：设计插件系统时，从一开始就抽象出 `RegistryBackend` 接口，让静态文件和数据库后端共享同一 CLI 词汇。

---

## 五、PR 工具链：`tools-pr` 控制面板

OD 将 PR 管理抽象为独立的 `tools-pr` 工具包，是维护者专用控制面板：

### 核心命令

```bash
pnpm tools-pr list                           # 按 lane 和 review-state 分桶
pnpm tools-pr list --bucket=merge-ready,approved-blocked
pnpm tools-pr list --lane=skill,contract --json
pnpm tools-pr view 1180                      # 单 PR 审查简报
pnpm tools-pr view 1180 --json
pnpm tools-pr classify --all                 # 全队列自动化标签
pnpm tools-pr assignment                     # 分配视角 + 空闲时间/阻塞视图
```

### 审查车道（Review Lanes）

不同类型的 PR 走不同的审查流程：

| 车道 | 适用范围 |
|------|---------|
| 默认 | 代码/测试变更 |
| Contract | `packages/contracts` 变更 |
| Protocol | sidecar-proto 变更 |
| Design-system | `design-systems/` 新增 |
| Skill | `skills/` 新增 |
| Craft | `craft/` 变更 |

### 工具设计约束

`tools-pr` 是**只读**的：它永远不 approve、merge、comment 或 close PR。所有副作用保持在维护者显式的 `gh` 调用中。

**可复用**：将 PR 管理工具设计为只读的分析/建议层，而非自动化操作层。这避免了工具误操作（自动合并、错误评论）的风险。

---

## 六、代码风格与质量保障

### Guard 脚本

```bash
pnpm guard  # 运行 tsx ./scripts/guard.ts + style policy 测试
```

Guard 检查：
- 新增 `.js`/`.mjs`/`.cjs` 文件必须有明确的生成/供应商/兼容性理由
- 源文件必须是 `.ts` 优先
- 测试文件必须在 `tests/` 目录，不在 `src/` 下

### TypeScript 全栈

- 入口、模块、脚本、测试、报告、配置默认 TypeScript
- 残留 JavaScript 限于：生成输出、供应商依赖、明确记录的兼容性构建产物
- `engines` 字段锁定 Node ~24，避免版本漂移

### i18n 类型安全

`apps/web/src/i18n/types.ts` 是类型化的 `Dict`，每个 key 必须在全部 18 个 locale 文件中定义。缺失翻译会导致 typecheck 错误，而非运行时 fallback。

```bash
pnpm i18n:check      # 检查 key 一致性
pnpm i18n:coverage   # 生成覆盖率报告
```

**可复用**：将 i18n key 的完整性检查提升到类型系统层面（编译期报错）比运行时 fallback 更可靠。

---

## 七、明确的不接受范围

OD 在 `CONTRIBUTING.md` 中明确列出不接受的 PR 类型：

| 不接受 | 原因 |
|--------|------|
| Vendor model runtime | OD 的赌注是 "你现有的 CLI 就够了" |
| 重写前端框架 | Next.js 16 + React 18 + TS 是定线 |
| 用 serverless 替换 daemon | daemon 的意义是拥有真实 cwd 和真实 CLI |
| 添加遥测/分析 | local-first，出站调用仅限用户配置的 provider |
| 打包无 license 二进制 | 必须有 license 和作者归属 |

**可复用**：开源项目应该**主动说不**。明确的拒绝列表比模糊的 "欢迎贡献" 更有效——它减少了无效 PR 的噪音，也保护了项目的核心设计决策。

---

## 八、边界约束：防止架构腐化

OD 通过 `AGENTS.md` 定义了严格的边界约束：

| 约束 | 说明 |
|------|------|
| `src/` 纯源码 | 不在 `src/` 下添加 `*.test.ts` 文件 |
| App 不跨导入 | `apps/web/**` 不导入 `apps/daemon/src/**` |
| Contracts 纯 TS | 不依赖 Next.js、Express、Node fs、SQLite、browser API |
| Root 不聚合 | 不添加 `pnpm build`/`pnpm test` 根别名 |
| 单一生命周期入口 | 所有开发流程通过 `pnpm tools-dev` |
| 无 Co-authored-by | Git commits 不包含 co-author 元数据 |
| UI+CLI 双轨 | 每个用户能力必须同时可通过 Web UI 和 `od` CLI 访问 |

**可复用**：在 `AGENTS.md`（或等效文件）中定义边界约束，让 AI agent 和人类贡献者都能在正确的范围内工作。这些约束不是官僚主义的——每一条背后都有实际的架构腐化教训。

---

## 九、License 与特殊处理

- **主许可证**：Apache-2.0
- **特殊例外**：`skills/guizang-ppt/` 保留原始 MIT license，归属 [op7418](https://github.com/op7418)
- **贡献者协议**：贡献即接受 Apache-2.0，特殊文件保留原 license

**可复用**：当项目整合第三方开源内容时，明确标注每个例外的原 license 和作者，避免 license 混淆。

---

## 十、实践总结：可复用的模式清单

| 模式 | 描述 | 适用场景 |
|------|------|---------|
| **三步新手贡献** | "复制→改→跑→提PR" 明确路径 | 需要社区贡献的开源项目 |
| **Skill 三级优先级** | 项目私有 > 项目提交 > 全局 | 可扩展的插件/能力系统 |
| **双镜头审查** | 代码正确性(P1) + 推理完整性(P3) | 内容型贡献的质量控制 |
| **只读 PR 工具** | 分析建议层，不做操作 | PR 管理自动化 |
| **边界约束文档化** | AGENTS.md 明确禁区 | monorepo 和 AI agent 辅助开发 |
| **类型安全 i18n** | 编译期检查 key 完整性 | 多语言项目 |
| **明确的不接受列表** | 主动说 "不" | 保护项目核心决策 |
| **单一生命周期入口** | `tools-dev` 唯一开发命令 | 降低开发环境复杂度 |
| **contracts 包** | 前后端共享纯 TS DTO | monorepo 类型安全通信 |
| **自托管注册表** | 静态 JSON → 数据库渐进增强 | 插件/扩展分发系统 |
