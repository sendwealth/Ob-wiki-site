---
title: CLI-Anything — 将任何软件转化为 AI Agent 可用的 CLI
created: 2026-05-18
updated: 2026-05-18
type: concept
tags: [agent, cli, automation, open-source, python, ai-tooling]
sources: [README.md, cli-anything-plugin/HARNESS.md]
confidence: high
---

# CLI-Anything

> 一条命令把任何桌面软件变成 AI Agent 可直接调用的 CLI 工具，保留 100% 真实功能

*项目路径: ~/Projects/CLI-Anything | 状态: 活跃开发 | 许可: MIT | GitHub: HKUDS/CLI-Anything*

## 核心问题

AI Agent 擅长推理，但无法操作专业 GUI 软件。现有方案各有缺陷：

| 方案 | 问题 |
|------|------|
| UI 自动化（截图+点击） | 脆弱，布局一变就挂 |
| 有限 API | 覆盖不到 10% 功能 |
| 简化重实现 | 丢失 90% 专业能力 |

**CLI-Anything 的解法**：自动生成结构化 CLI 接口，Agent 直接调用真实软件后端，零妥协。

## 工作原理

### 7 阶段全自动流水线

```
源码分析 → 架构设计 → 代码实现 → 测试规划 → 测试编写 → 文档生成 → PyPI 发布
```

一条命令触发：

```
/cli-anything ./gimp
```

1. **Analyze** — 扫描源码，映射 GUI 操作到 API
2. **Design** — 设计命令组、状态模型、输出格式
3. **Implement** — 生成 CLI 代码（Click 框架）
4. **Test Plan** — 规划测试策略
5. **Test Write** — 编写测试用例
6. **Document** — 生成文档和 SKILL.md
7. **Publish** — 打包发布到 PyPI

### 核心：真实软件集成

```
Agent 发出 CLI 命令
      ↓
CLI 生成有效项目文件（ODF、MLT XML、SVG...）
      ↓
调用真实软件后端渲染（Blender、LibreOffice、FFmpeg...）
      ↓
输出结构化 JSON + 人类可读结果
```

不做替代实现。用真实软件，拿真实结果。

## 架构设计

### 核心原则

1. **真实软件集成** — 调用真实应用渲染，不做简化替代
2. **双模式交互** — REPL 交互模式 + 子命令脚本模式
3. **Agent 原生** — 每个命令内置 `--json` 输出
4. **零妥协依赖** — 必须有真实后端，测试失败而非跳过
5. **一致体验** — 统一 REPL 界面（repl_skin.py）

### 项目结构

```
cli-anything-plugin/          # Claude Code 插件（主入口）
├── skill_generator.py        # 核心生成逻辑
├── repl_skin.py              # 统一 REPL 界面
├── commands/                 # 插件命令定义
│   ├── cli-anything.md       # 主构建命令
│   ├── refine.md             # 扩展现有 harness
│   ├── test.md               # 测试运行器
│   └── validate.md           # 标准验证
├── HARNESS.md                # 开发方法论
└── QUICKSTART.md             # 5 分钟快速开始

<软件名>/agent-harness/       # 各软件的 CLI 包
├── cli_anything.<软件名>/
│   ├── cli.py                # Click CLI 定义
│   ├── core/                 # 核心业务模块
│   └── utils/                # REPL、后端包装等
└── tests/                    # 测试套件

cli-hub/                      # CLI-Hub 分发平台
├── setup.py
└── README.md

skills/                       # 统一 SKILL.md 目录
codex-skill/                  # Codex 支持
```

### 每个 Harness 的内部结构

```
cli_anything.blender/
├── __init__.py
├── cli.py              # Click CLI（命令注册、参数解析）
├── core/
│   ├── scene.py        # 场景操作
│   ├── mesh.py         # 网格建模
│   └── render.py       # 渲染管线
├── utils/
│   ├── repl_skin.py    # 统一 REPL 界面
│   └── backend.py      # 后端调用包装
└── tests/
    ├── test_scene.py   # 单元测试
    └── test_e2e.py     # 端到端测试
```

## Agent 如何使用

### 发现能力

```bash
# REPL 模式（交互式）
$ cli-anything-blender
Blender CLI > which           # 列出所有可用命令
Blender CLI > scene create --json   # JSON 输出给 Agent
```

```bash
# 子命令模式（脚本/管道）
$ cli-anything-blender scene create --name "MyScene" --json
{"status": "success", "data": {"scene": "MyScene", "objects": []}}
```

### CLI-Hub 自动发现

Agent 通过 CLI-Hub 自主发现和安装需要的 CLI：

```bash
pip install cli-anything-hub
cli-hub install blender
```

Meta-skill 让 Agent 浏览 20+ 社区 CLI 目录，自动选择合适的安装。

## 已支持软件

| 软件 | 命令 | 测试数 | 领域 |
|------|------|--------|------|
| Blender | `cli-anything-blender` | 208 | 3D 建模/渲染 |
| Inkscape | `cli-anything-inkscape` | 202 | 矢量图形 |
| Audacity | `cli-anything-audacity` | 161 | 音频编辑 |
| GIMP | `cli-anything-gimp` | 107 | 图像处理 |
| FreeCAD | `cli-anything-freecad` | — | CAD/工程 |
| Shotcut | `cli-anything-shotcut` | — | 视频编辑 |
| Draw.io | `cli-anything-drawio` | — | 图表绘制 |
| LibreOffice | `cli-anything-libreoffice` | — | 办公套件 |
| VideoCaptioner | `cli-anything-videocaptioner` | — | 字幕生成 |

共 18+ 应用，2280+ 测试，全部通过。

## Preview 系统

CLI-Anything 引入了 Preview + Live Preview + Trajectory 三层可视化闭环：

```
Agent 执行命令 → 生成预览包（preview bundle）
      ↓              ↓
验证结果    ←    Live Preview 持续刷新
      ↓
Trajectory.json 记录命令→预览历史
```

这让 Agent 能看到自己每一步操作的视觉反馈，实现"看图做事"的闭环。

## 技术栈

| 组件 | 技术 | 用途 |
|------|------|------|
| CLI 框架 | Python + Click | 命令定义、参数解析 |
| 分发 | PyPI | `pip install cli-anything-*` |
| 插件 | Claude Code Plugin | 主入口和生成引擎 |
| 测试 | pytest | 单元 + E2E 测试 |
| Agent 接入 | SKILL.md | AI Agent 自动发现 |
| Hub | Python + Web | 社区 CLI 目录 |
| REPL | repl_skin.py | 统一交互界面 |

## 与 Agent 生态的集成

```
Claude Code  → /cli-anything ./gimp    → 生成 GIMP CLI
Codex        → CLI-Anything skill      → 同样的流水线
OpenClaw     → cli-hub-meta-skill      → 自动发现安装
nanobot      → cli-hub-meta-skill      → 自动发现安装
Cursor/Pi    → 生成的 CLI 包           → 直接调用
```

## 关键设计决策

| 决策 | 理由 |
|------|------|
| 调用真实后端而非重实现 | 保留 100% 功能，不做妥协 |
| Click 框架 | Python 生态最成熟的 CLI 库 |
| 双模式（REPL + 子命令） | 交互探索 + 脚本自动化 |
| 测试失败不跳过 | 确保真实功能完整性 |
| SKILL.md 机制 | 让任何 Agent 平台都能发现和使用 |
| 7 阶段全自动 | 降低贡献门槛，保证质量一致 |

## HARNESS.md 方法论

开发过程中的关键经验：

| 经验 | 描述 |
|------|------|
| 用真实软件 | CLI 必须调用真实应用渲染，不用替代品 |
| 渲染鸿沟 | GUI 应用在渲染时才应用效果，CLI 须用原生渲染器 |
| 滤镜翻译 | 格式间映射需注意重复合并、交错排序、参数差异 |
| 时间码精度 | 非整数帧率（29.97fps）用 `round()` 而非 `int()` |
| 输出验证 | 不信任 exit code 0，验证文件头、结构、像素、音频 |

## 贡献方式

1. Fork → 新建 `<软件名>/agent-harness/`
2. 运行 `/cli-anything <path>` 自动生成骨架
3. 补充和测试
4. PR 合并后自动进入 CLI-Hub 目录

See also: [[agent-world]], [[agentic-rag]], [[a2a-protocol]]
