---
title: Nuwax
created: 2026-05-29
updated: 2026-05-29
type: entity
tags: [product, platform, ai, saas, b2c, active]
sources:
  - https://github.com/nuwax-ai/nuwax
  - ~/Projects/nuwax-ai/nuwax
confidence: high
---

# Nuwax

> AI Agent 平台前端 — 基于 React 18 + Umi.js 的多租户 AI 智能体构建、管理与交互平台，集成 Web IDE、工作流编辑器、MCP 工具市场和订阅支付系统。

---

## 一句话定位

Nuwax 是一个面向企业/团队的 **AI Agent 全生命周期管理平台**，用户可以在浏览器中创建、编排、发布和对话 AI 智能体，同时集成 Web IDE 实现代码辅助开发。

## 核心数据

| 维度 | 数值 |
|------|------|
| 版本 | 1.1.9 |
| 许可证 | Apache-2.0 |
| 总提交 | 7,157 |
| 贡献者 | ~14 人 |
| TS/TSX 文件 | 1,130 |
| 页面模块 | 40+ |
| Hooks | 50+ |
| Services | 35+ |
| Models | 20+ |

## 技术栈

```
┌─────────────────────────────────────────────────┐
│                    Frontend                      │
├─────────────────────────────────────────────────┤
│  Framework:   Umi.js v4 (@umijs/max)            │
│  UI:          Ant Design 5 + Pro Components + X  │
│  Language:    TypeScript                         │
│  State:       Umi Model (内置)                   │
│  Routing:     Convention-based (Umi)             │
│  i18n:        Umi locale (zh-CN default)         │
├─────────────────────────────────────────────────┤
│  Code Editor: Monaco Editor                      │
│  Rich Text:   TipTap                             │
│  Graph/Flow:  AntV X6 + G6                      │
│  Markdown:    react-markdown + ds-markdown        │
│  DnD:         @dnd-kit + react-beautiful-dnd     │
│  Preview:     PDF/DOCX/Excel/PPTX/PPT            │
├─────────────────────────────────────────────────┤
│  Build:       Webpack + esbuild minifier          │
│  PM:          pnpm                               │
│  Test:        Vitest                             │
│  Style:       Less + CSS Variables (xagi prefix) │
│  Lint:        Prettier + lint-staged              │
│  Release:     standard-version                   │
└─────────────────────────────────────────────────┘
```

## 架构分层

```
Pages (40+)  →  Components (100+)  →  Hooks (50+)  →  Services (35+)
     ↓                ↓                    ↓               ↓
   Layouts        Business/UI           State           API Calls
     ↓                ↓                    ↓               ↓
  Models (20+)  ←  Types  ←  Constants  ←  Utils
```

**依赖方向规则**：

- Pages → Components → Hooks → Services → Utils
- Models ← Types ← Constants（无上层依赖）
- 禁止：Components 直接依赖 Models，Services 依赖 Hooks

## 核心功能模块

### 1. AI 对话系统 (Chat)

- SSE (Server-Sent Events) 实时流式对话
- Agent 侧边栏（收藏、历史、切换）
- 文件上传与预览
- Prompt 变量参数（TipTapVariableInput）
- 多模型选择与切换
- 会话管理（创建/删除/重命名）

### 2. 智能体开发 (EditAgent / SpaceDevelop)

- 拖拽式智能体配置
- Prompt 编辑 + 变量模板
- 模型绑定（组件级模型设置）
- 版本历史与回滚
- 发布与审核流程
- 统计分析仪表盘

### 3. Web IDE (AppDev)

```
┌──────────────┬──────────────────┬──────────────┐
│  FileTree    │  Monaco Editor   │  Live Preview │
│  Panel       │  (Code Editing)  │  (iframe)     │
│              │                  │               │
│  - 文件树     │  - 多语言高亮     │  - 自动刷新   │
│  - CRUD操作   │  - 智能提示      │  - 全屏预览   │
│  - 修改追踪   │  - 自动布局      │  - 错误状态   │
├──────────────┴──────────────────┴──────────────┤
│                  AI Chat Area                   │
│  (SSE 流式对话 + 思考过程 + 工具调用状态)          │
└─────────────────────────────────────────────────┘
```

- Dev Server 自动管理（端口分配 3000-4000、保活、重启）
- 文件内容缓存与同步
- AI 辅助代码生成与修改
- DevLog 控制台

### 4. 工作流编辑器 (Antv-X6)

- 可视化拖拽编排
- 节点/边/历史/键盘快捷键
- 测试运行与调试

### 5. 工作空间系统 (Space)

- 多租户隔离
- 角色（管理员/开发者/普通用户）
- 子模块：
  - SpaceSquare — 空间广场
  - SpaceKnowledge — 知识库管理
  - SpaceMcpManage — MCP 服务器管理
  - SpaceSkillManage — 技能管理
  - SpacePluginTool — 插件管理
  - SpaceResource — 资源管理
  - SpaceLog — 操作日志
  - SpaceTaskCenter — 任务中心
  - SpaceTable — 数据表格

### 6. 生态市场

- Square — 公共智能体广场
- EcosystemMcp — MCP 工具市场
- EcosystemTemplate — 模板市场

### 7. 支付与订阅

- 订阅计划管理
- 支付集成（feat-subscriptions-payments 分支活跃开发中）
- 收益管理与提现

### 8. 系统管理

- SystemManagement — 系统配置
- UserManage — 用户管理
- GlobalModelManage — 全局模型配置
- PublishAudit — 发布审核

## 实时通信架构

```
User Action → sendChatMessage() → POST /api/...
                                      ↓
                              SSE Connection
                                      ↓
                    ┌─────────────────┼─────────────────┐
                    ↓                 ↓                 ↓
            agent_thought      agent_message      tool_call
            _chunk              _chunk
                    ↓                 ↓                 ↓
            思考过程展示       AI 回复流式显示    工具调用状态
```

**消息类型**：
- `agent_thought_chunk` — AI 思考过程（实时展示推理路径）
- `agent_message_chunk` — AI 回复内容（流式增量更新）
- `tool_call` — 工具调用通知（文件操作、代码生成）
- `prompt_end` — 会话结束

## 设计模式与亮点

| 模式 | 实现 |
|------|------|
| 分层架构 | Pages → Components → Hooks → Services → Utils |
| 不可变数据 | lodash cloneDeep 用于状态更新 |
| 组件复用 | ResizableSplit、FileTreeView、MarkdownRenderer 等通用组件 |
| SSE 流式 | @microsoft/fetch-event-source |
| 国际化 | Umi locale 插件，i18nRuntime 动态字典 |
| 主题系统 | CSS Variables（xagi 前缀）+ 统一主题 Hook |
| 权限控制 | usePermission Hook + PermissionMask 组件 |
| 移动适配 | PC/M 双向跳转（阿里云验证码 + 路由重定向） |
| 错误恢复 | Mock 模式 + localStorage 持久化 + 网络延迟模拟 |
| 文件预览 | PDF + DOCX + Excel + PPT + 图片多格式支持 |

## API 服务层（35+ 模块）

| 服务 | 职责 |
|------|------|
| appDev | Web IDE 开发环境（start/stop/restart dev server） |
| agentConfig | 智能体配置 CRUD |
| agentDev | 智能体开发相关 |
| agentTask | AI 任务管理 |
| chat / message | 对话与消息 |
| subscriptionService | 订阅与支付 |
| ecosystem | 生态市场 |
| mcp | MCP 服务器管理 |
| skill | 技能管理 |
| knowledge | 知识库 |
| workflow | 工作流 |
| workspace | 工作空间 |
| userService | 用户认证 |
| tenant | 租户管理 |
| vncDesktop | VNC 远程桌面 |

## 目录结构概览

```
src/
├── pages/                    # 40+ 页面模块
│   ├── AppDev/              # Web IDE（Monaco + Preview + Chat）
│   ├── Chat/                # AI 对话主页面
│   ├── EditAgent/           # 智能体编辑器
│   ├── Home/                # 首页（智能体分类 + 推荐）
│   ├── Space/               # 工作空间入口
│   ├── SpaceDevelop/        # 智能体开发
│   ├── SpaceMcpManage/      # MCP 管理
│   ├── Square/              # 公共广场
│   ├── Antv-X6/             # 工作流编辑器
│   ├── Login/               # 登录认证
│   └── ...                  # 其他 30+ 页面
├── components/              # 100+ 通用/业务组件
│   ├── base/                # 基础 UI 组件
│   ├── business-component/  # 业务组件
│   ├── ChatView/            # 聊天视图
│   ├── CreateAgent/         # 智能体创建
│   ├── FileTreeView/        # 文件树
│   ├── MarkdownRenderer/    # Markdown 渲染
│   ├── TiptapVariableInput/ # 富文本变量输入
│   └── ...
├── hooks/                   # 50+ 业务逻辑 Hook
├── services/                # 35+ API 服务
├── models/                  # 20+ 状态模型
├── utils/                   # 工具函数
├── contexts/                # React Context
├── constants/               # 常量定义
└── types/                   # TypeScript 类型
```

## 设计取舍

| 决策 | 理由 |
|------|------|
| Umi.js 而非 Next.js | 国内生态、内置 layout/request/model/plugin 约定 |
| Monaco 而非 CodeMirror | 与 VS Code 一致的编辑体验、更丰富的语言支持 |
| AntV X6 而非 ReactFlow | 国内生态、更完善的图编辑能力（对齐/吸附/组合） |
| SSE 而非 WebSocket | 单向流足够、HTTP 兼容性好、无需维护 WS 连接 |
| Webpack 而非 Vite | Umi 生态绑定、Monaco 集成成熟 |
| CSS Variables 主题 | 运行时切换、无构建依赖 |
| Convention-based routing | Umi 默认模式、减少路由样板代码 |

## 团队与开发

- **组织**: nuwax-ai
- **分支策略**: main → dev → feat-*/bugfix*
- **活跃开发分支**: feat-subscriptions-payments（支付订阅）
- **CI**: lint-staged + Prettier + commit verify
- **版本管理**: standard-version (SemVer)
- **贡献者**: daydayup008, dong, JerryLee, leilinzhou, louis, paoxiao, pujing, soddy, xiedaokun, yangpeng 等

## 与同类产品对比

Nuwax 定位类似 **Coze / Dify / FastGPT** 的 AI Agent 平台，差异在于：

- 更强的 **Web IDE 集成**（Monaco Editor + Live Preview + Dev Server）
- 内置 **工作流可视化编辑**（AntV X6）
- **多租户工作空间** 模型（企业级隔离）
- **MCP 工具市场** 生态
- **订阅支付** 商业化闭环

## Wikilinks

- [[agno]] — 同为 AI Agent 平台，但 Nuwax 是应用层前端而非 SDK
- [[gstack]] — AI 编码工作流技能体系，可类比 Nuwax 的 AppDev 模块
- [[lobechat-architecture]] — LobeChat 同为 AI 对话前端，可对比架构选型
- [[browser-use-architecture]] — 浏览器自动化架构，与 AppDev Preview 机制有相似之处
- [[context-mode]] — 上下文优化工具，适用于 Nuwax 大型前端项目开发
- [[codegraph]] — 代码知识图谱，适用于 1130 文件规模的项目导航
