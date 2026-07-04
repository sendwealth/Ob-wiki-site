---
title: LeaferJS
created: 2026-07-04
updated: 2026-07-04
type: entity
tags: [canvas, rendering-engine, frontend, graphics, chinese-oss, design-tool]
sources:
  - https://www.leaferjs.com/
  - https://www.leaferjs.com/ui/guide/
  - https://www.leaferjs.com/ui/guide/start.html
  - https://github.com/leaferjs/leafer-ui
  - https://juejin.cn/post/7389651690306355241
  - https://juejin.cn/post/7256386855721074747
confidence: high
---

# LeaferJS

> 国产开源（MIT）Canvas 2D 渲染引擎 + UI 框架，主打极致性能（百万级图形）与开箱即用的图形交互/编辑能力，适用于 AI 无限画布、在线设计工具、组态可视化等场景。

**官网**：https://www.leaferjs.com/
**GitHub**：https://github.com/leaferjs/leafer-ui
**1.0 发布**：2024 年

## 定位

一句话：想做「网页版 Figma / Miro / Canva」这类产品，它就是为此生的。

LeaferJS 致力于实现一套**简洁、开放、现代化的 UI 绘图语言标准**，让不同软件之间能够沟通、协作、共享绘图数据。它把"高性能渲染引擎"和"UI 框架"两层合在一起，相比纯底层引擎（PixiJS）多了上层 UI 元素和编辑能力，相比对象模型库（Konva）多了局部渲染等极致性能优化。

### 适用场景

AI 无限画布、AI 设计工具、图形/流程图编辑器、组态/工业可视化、数据大屏、互动应用、小游戏、生成图片与短视频。

## 核心特性

| 能力 | 说明 |
|------|------|
| **场景树** | 类 DOM 的树结构（`Group`/`Leafer` 容器 + `Rect`/`Text`/`Path` 等节点），矢量化 |
| **极致性能** | 分层渲染 + 脏矩形（partRender，只重绘变化区域）+ 虚拟化，可瞬间创建百万级图形 |
| **交互内置** | 原生拖拽、缩放、旋转、多点触控，毫秒级命中检测（Hit Testing） |
| **开箱即用** | 视窗控制、自动布局、图形编辑器、SVG 导出/导入 |
| **设计软件互通** | 方便对接 Photoshop / Figma / Sketch 数据 |
| **跨平台** | Web / 小程序 / Node / 服务端，统一交互事件 |
| **动画/状态/游戏** | 1.0 后新增动画、状态过渡、游戏能力 |
| **TS 友好** | 原生 TypeScript，类型完善 |
| **轻量** | 核心约 70KB（min+gzip），零依赖 |

## 性能优化机制

1. **分层渲染** — 静态元素与动态元素分离到不同画布，避免相互重绘
2. **脏矩形渲染（partRender）** — 只重绘发生变化的局部区域，而非整个画布
3. **虚拟化技术** — 对不可见区域的节点延迟渲染
4. **数据分级加载** — 按需加载节点数据

这四点叠加，是它能在「图形编辑器」这类高频局部更新场景下保持流畅的关键——也是它区别于 Konva / Fabric 的核心技术壁垒。

## 架构

核心包 + 场景插件 的设计模式，关键模块：

| 模块 | 功能 |
|------|------|
| `leafer-interface` | 通用接口 |
| `leafer-display` | 树结构管理 |
| `leafer-canvas` | 渲染画板 |
| `leafer-interaction` | 用户交互 |
| `leafer-data` | 数据处理器 |

### 核心包

- **`leafer`** — 全量包，含所有 `@leafer-in/*` 插件（editor / view-port 等）
- **`leafer-ui`** — 仅核心 UI（约 70KB），推荐大多数场景
- **`leafer-draw`** — 仅绘图 + 导出，去掉了 App、查找元素、事件交互，更轻量

### 平台版本

- Web：`leafer` / `leafer-ui`
- 小程序：`@leafer-ui/miniapp` / `@leafer-draw/miniapp`

## 关键概念

- **`Leafer`** — 单个画布场景的核心类（一棵场景树 + 一个 canvas）
- **`App`** — 应用级管理器，可管理多个 tree / ground / flyer 等层，多场景应用用它
- **`@leafer-in/*`** — 官方功能插件（如 `@leafer-in/editor` 编辑器、`@leafer-in/view-port` 视窗控制）

## 快速上手

**安装**（任选一种）：

```bash
# 方式1：脚手架（最快，含完整工程）
npm create leafer@latest

# 方式2：仅核心 UI（推荐）
npm install leafer-ui

# 方式3：全量（含所有插件）
npm install leafer
```

**最小示例**（画一个可拖拽的圆角矩形 + 文字）：

```html
<div id="box" style="width:600px;height:400px"></div>
<script type="module">
  import { Leafer, Rect, Text } from 'https://unpkg.com/leafer-ui'

  const app = new Leafer({ view: 'box', fill: '#1a1a1a' })

  const rect = new Rect({
    x: 100, y: 100,
    width: 200, height: 120,
    fill: '#89AACC',
    cornerRadius: 12,
    draggable: true   // 直接可拖拽
  })

  const text = new Text({
    text: 'Hello Leafer',
    x: 130, y: 145,
    fill: '#fff', fontSize: 22
  })

  app.add(rect)
  rect.add(text)   // 文字作为矩形的子节点
</script>
```

## 选型对比

| 维度 | **LeaferJS** | PixiJS | Konva | Fabric.js |
|------|------|------|------|------|
| 渲染 | Canvas 2D（局部渲染优化） | **WebGL 优先**，最快 | Canvas 2D | Canvas 2D |
| 强项 | 图形编辑、AI 画布、百万图形 | 游戏、复杂动画、海量精灵 | 快速搭可交互图形 | 图片编辑、滤镜 |
| 交互 | 内置丰富 | 需自行封装 | 内置拖拽/变换 | 内置对象编辑 |
| 学习成本 | 低，API 友好 | 中高（偏底层） | 低 | 中 |
| 生态 | 新兴但活跃，**中文文档完善** | 最成熟 | 成熟 | 成熟 |

**选型口诀**：
- 图形编辑器 / AI 画布 → **LeaferJS**
- 游戏 / 高性能动画 → **PixiJS**
- 快速搭可交互图表 / Demo → **Konva**
- 图片编辑器（裁剪、滤镜）→ **Fabric.js**

## 学习路径

1. **官网 Playground** 在线调试每段示例 → https://www.leaferjs.com/ui/guide/start.html
2. 按底部「下一步」顺序学，重点掌握 4 块：
   - **场景树结构**（`add` / `remove` / 父子关系）
   - **样式**（fill / stroke / cornerRadius / 渐变 / 图案）
   - **交互事件**（drag / hover / click / 多点触控）
   - **图形编辑器**（`@leafer-in/editor`：选中、变换、多选）
3. **进阶**：动画系统、自动布局、状态过渡、SVG 导入导出、服务端渲染

## 相关页面

- [[design-as-code]] — 设计系统编码为纯文本的理念，LeaferJS 的"绘图语言标准"是这个范式在 Canvas 端的体现
- [[design-md-spec]] — Google Stitch 的纯 Markdown 设计规范，可与 Leafer 的设计数据互通思路对照
- [[awesome-design-md]] — 73 个现成 DESIGN.md 集合，跨设计↔代码范式的参考
