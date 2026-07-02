---
title: Three.js Game Skills
created: 2026-06-21
updated: 2026-06-21
type: entity
tags: [threejs, game-dev, ai-agent, skills, codex, claude-code, webgl]
sources: [公众号「AI开源提效指南」2026-06-19]
confidence: high
---

# Three.js Game Skills

> 9 个专业级 AI Agent 游戏开发技能包，让 Codex / Claude Code 从零构建可玩的 AAA 级 3D 网页游戏。

**项目仓库**：https://github.com/majidmanzarpour/threejs-game-skills

## 定位

给 AI 一句话需求（如"做赛博朋克赛车游戏"），AI 自动搭建场景、编写物理引擎、设计 HUD、生成 3D 模型、配上音效，最后输出浏览器可玩的游戏。

面向 Codex CLI 和 Claude Code 等 AI 编程智能体，将 3D 网页游戏开发的完整流程——玩法设计、画面升级、UI 制作、资源生成、音效制作、发布测试——封装成标准化技能。

## 6 大项目亮点

1. **AI 全流程编排**：9 个专业技能包 + 导演技能自动路由，用户只需一句话描述需求
2. **专业质量门禁**：10 维度视觉评分卡、QA 检查清单、发布门禁、审计脚本，确保输出质量
3. **外部 AI 资源集成**：Tripo 3D 生成 + Gemini 图像 + ElevenLabs 音频
4. **脚手架即用**：内置 Vite + TypeScript + Three.js 项目模板，含完整的游戏循环架构
5. **移动端优先**：触控、安全区域、响应式布局从一开始就纳入
6. **台账透明**：技能加载、参考文档、资源采购、阶段执行全部记录，过程完全可审计

## 9 个技能包

### 1. 导演技能（threejs-game-director）—— 总指挥

整个技能包的入口和大脑。用户只需说"用 threejs-game-director 做一个游戏"，它就会：

1. **自动加载**所有相关子技能（玩法、画面、UI、调试、QA）
2. **按阶段执行**：先做可玩循环 → 画面升级 → UI 设计 → 调试优化 → QA 发布
3. **维护台账**：技能加载台账、参考文档台账、外部资源台账、阶段执行台账
4. **验证输出**：构建检查、浏览器截图、画布像素检测、移动端适配

关键优势：
- ✅ 用户不需要知道每个子技能的名字，导演自动路由
- ✅ 内置资质探测脚本，自动检测 API Key 是否可用
- ✅ 审计脚本自动检查最终报告完整性

### 2. AAA 画面构建器（threejs-aaa-graphics-builder）—— 视觉升级

当游戏截图看起来"太基础"时登场：

- 使用 **10 维度视觉评分卡**（艺术方向、主角、敌人、奖励、世界、材质、光照、特效、UI、性能）
- 从截图出发，逐项评分，直到每个维度 ≥ 2/3
- 核心原则：**先建模，再材质，再光照，最后特效**——而不是给方块加发光

关键优势：
- ✅ 禁止用"加发光"冒充 AAA 画质
- ✅ 外部资源采购台账：每个高价值表面记录来源（程序化 / 图像生成 / 3D 生成 / 混合）
- ✅ 评分卡前后对比，量化视觉提升

### 3. 3D 资源生成器（threejs-3d-generator）—— AI 建模

基于 **Tripo API**，支持完整的 3D 资产生成管线：

| 功能 | 命令 | 说明 |
|---|---|---|
| 文字→3D | `text --prompt "..."` | 输入文字描述生成 3D 模型 |
| 图片→3D | `image --image ...` | 基于概念图生成 3D 模型 |
| 贴图 | `postprocess --type texture_model` | 为模型重新生成 PBR 贴图 |
| 骨骼绑定 | `postprocess --type animate_rig` | 自动骨骼绑定（人形/四足） |
| 动画重定向 | `postprocess --type animate_retarget` | 将预设动画映射到绑定模型 |
| 格式转换 | `postprocess --type conversion` | GLB/FBX 互转 |
| 风格化 | `postprocess --type stylize_model` | 体素/低多边形风格化 |
| 角色流水线 | `character-pipeline` | 一键生成→绑定→动画→下载 |

关键优势：
- ✅ 支持人形角色（v1.0 解剖学骨骼）和四足生物（v2.5 骨骼）
- ✅ 内置验证工具：`validate-rig` 检查骨骼链深度，`validate-animation` 检查关键帧质量
- ✅ 自动重试机制：骨骼绑定失败自动重试（默认 2 次）

### 4. 图像生成器（threejs-image-generator）—— 概念设计

基于 **Gemini 图像 API**，为游戏生成 2D 素材：

- 角色概念图（T-pose/A-pose，用于后续 3D 建模输入）
- 纹理参考图（无缝贴图、PBR 材质参考）
- 环境背景（天空盒、城市天际线、星云背景）
- UI 素材（Logo、图标、徽章、GUI 面板）

关键优势：分辨率可选 1K/2K/4K | 支持基于已有图片的编辑修改 | 与 3D 生成器无缝衔接：概念图 → 图片转 3D

### 5. 音频生成器（threejs-audio-generator）—— 声音设计

基于 **ElevenLabs API**，覆盖游戏音频全需求：

- **音效（SFX）**：跳跃、射击、爆炸、拾取、碰撞
- **环境音**：风声、雨声、引擎轰鸣、氛围循环
- **语音**：解说员台词、Boss 语音、教程提示
- **语音转换**：将真人录音转换为目标角色声线
- **音频清理**：人声分离、降噪

关键优势：内置循环音效支持（`--loop`）| 提示词影响度可调（`--prompt-influence 0.3-0.8`）| 生成后直接集成到 Three.js Web Audio 运行时

### 6-9. 其他技能

- **threejs-gameplay-systems** — 玩法系统：游戏循环、物理引擎选择、碰撞检测
- **threejs-ui-designer** — UI/HUD 设计
- **threejs-debugger** — 调试：控制台错误、渲染上下文、性能分析
- **threejs-qa-release** — QA 发布：构建检查、截图验证、移动端适配

## 10 维度视觉评分卡

> 文件路径：`skills/threejs-aaa-graphics-builder/references/visual-scorecard.md`

| 维度 | 满分 | 评判标准 |
|---|---|---|
| 艺术方向 | 3 | 有统一的视觉主题和风格 |
| 主角/玩家 | 3 | 主角模型有细节、可识别 |
| 障碍物/敌人 | 3 | 多样且有视觉层次 |
| 奖励/可交互物 | 3 | 视觉反馈清晰 |
| 世界/环境 | 3 | 场景丰富不空旷 |
| 材质/贴图 | 3 | PBR 材质、程序化纹理 |
| 光照/渲染 | 3 | 多光源、阴影、后处理 |
| 特效/动态 | 3 | 粒子、着色器效果 |
| UI/HUD | 3 | 定制化、响应式 |
| 性能证据 | 3 | 帧率、draw calls 可接受 |

满分 30 分，AAA 级要求平均 ≥ 2/3（即 ≥ 20 分），且每项 ≥ 2 分。

## 物理引擎选择指南

> 文件路径：`skills/threejs-gameplay-systems/references/physics-engine-selection.md`

| 引擎 | 适用场景 | 特点 |
|---|---|---|
| Rapier | 严肃物理游戏（刚体、传感器、球类、高速碰撞） | WASM 加速，功能完整 |
| cannon-es | 轻量简单场景 | 纯 JS，无需 WASM |
| 自定义碰撞 | 街机风格触发器 | 完全可控，性能最优 |

## 技术架构

### 脚手架项目结构

```
my-game/
├── src/
│   ├── main.ts               入口
│   ├── core/
│   │   ├── Loop.ts            游戏循环
│   │   ├── Renderer.ts        渲染器
│   │   └── InputController.ts  输入控制
│   ├── entities/
│   │   ├── Player.ts          玩家实体
│   │   └── Pickup.ts          拾取物
│   ├── systems/
│   │   ├── CameraRig.ts       相机系统
│   │   ├── CollisionSystem.ts 碰撞系统
│   │   ├── AudioSystem.ts     音频系统
│   │   ├── Hud.ts             HUD 系统
│   │   └── DebugTools.ts      调试工具
│   └── game/
│       └── Game.ts            游戏主逻辑
├── tests/
│   └── visual.spec.ts         Playwright 视觉测试
└── vite.config.ts
```

### 技术栈

| 层级 | 技术 | 选型理由 |
|---|---|---|
| 前端框架 | TypeScript + Vite | 类型安全，极速构建 |
| 3D 引擎 | Three.js | 最成熟的 WebGL 库 |
| 物理引擎 | Rapier（默认）/ cannon-es | WASM 加速 vs 轻量纯 JS |
| 3D 生成 | Tripo API | 文字/图片转 3D，支持骨骼绑定 |
| 图像生成 | Gemini API | Google 高质量图像生成 |
| 音频生成 | ElevenLabs API | 专业级游戏音效和语音 |
| 视觉测试 | Playwright | 浏览器自动化截图验证 |
| 调试 UI | lil-gui / stats.js | 运行时调参和性能监控 |

### 导演技能工作流

```
用户请求 → 导演技能加载
    ↓
1. 加载兄弟技能（玩法/画面/UI/调试/QA/3D/图像/音频）
    ↓
2. 加载阶段参考文档（每阶段入口必读）
    ↓
3. 执行阶段管线：
   玩法系统 → 外部资源采购 → AAA画面 → UI设计 → 调试优化 → QA发布
    ↓
4. 审计最终报告
    ↓
5. 输出：技能台账 + 参考台账 + 资源台账 + 阶段台账 + 评分卡
```

## 安装

```bash
# 安装所有技能到 Codex
npx skills add majidmanzarpour/threejs-game-skills --skill '*' -a codex -g -y

# 安装所有技能到 Claude Code
npx skills add majidmanzarpour/threejs-game-skills --skill '*' -a claude-code -g -y

# 从源码安装
git clone https://github.com/majidmanzarpour/threejs-game-skills.git
cd threejs-game-skills
./install.sh --codex     # 安装到 Codex
./install.sh --claude    # 安装到 Claude Code
./install.sh --all       # 安装到所有
```

### API Key 配置

```bash
export TRIPO_API_KEY=""       # 3D 模型生成
export GEMINI_API_KEY=""      # 图像生成
export ELEVENLABS_API_KEY=""  # 音频生成
```

## 设计启发

这个项目的模式与 Hermes 技能系统高度相似——导演技能 = 主入口，子技能 = 各领域专家。几个值得借鉴的做法：

- **评分卡作为质量门禁**：用可量化的标准（10 维度评分卡）驱动迭代，而不是模糊的"好看"
- **台账透明化**：每个阶段、每个资源来源都记录，过程完全可审计
- **技能自动路由**：用户不需要知道子技能名字，导演自动按需加载
- **正确的升级顺序**：先建模 → 再材质 → 再光照 → 最后特效，拒绝"加发光"捷径

## 相关页面

- [[superpowers]] — 同类 AI 编码 Agent 行为塑造技能插件（14 技能 + Hook 自动注入）
- [[ecc]] — 跨 harness AI 代理优化系统（63 agents + 249 skills）
- [[agents-cli]] — Google 官方 CLI + Skills 工具链
- [[claude-code-workflow]] — Claude Code 确定性多 Agent 编排引擎
