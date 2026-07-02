---
title: FastGPT
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [llm, rag, knowledge-base, workflow, low-code, chinese]
sources:
  - https://github.com/labring/FastGPT
confidence: 0.9
---

# FastGPT

> 国产开源 AI 知识库与工作流平台 — 聚焦知识库问答场景，Docker 一键部署，兼容国产模型。

---

## 一、项目定位

FastGPT 由环界（LabRing）团队开发，定位为 AI Agent 构建平台，核心聚焦知识库问答场景。在国内与 [[dify]] 形成双雄格局：FastGPT 更聚焦知识库问答，Dify 更偏向通用 AI 应用开发平台。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 18k+ |
| 许可证 | Apache 2.0（附加条款） |
| 语言 | TypeScript (Next.js) |
| 创建者 | LabRing 团队 |
| 官网 | https://fastgpt.io |

核心能力：
1. **可视化工作流编排** — 拖拽构建 AI 工作流
2. **知识库管理** — 多格式导入、自动切片、向量化
3. **国产模型兼容** — 通义千问、文心一言、DeepSeek、智谱等
4. **Docker 一键部署** — docker-compose 一条命令启动
5. **Sealos 云原生** — 与 Sealos 生态深度集成

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                  前端（Next.js）                       │
│   App Editor · Flow Editor · Knowledge Base · Chat   │
├─────────────────────────────────────────────────────┤
│                  API 层（Next.js API Routes）          │
│   REST API · SSE Streaming                           │
├─────────────────────────────────────────────────────┤
│                  核心引擎                              │
│   Workflow Engine · RAG Engine · AI Chat Engine       │
│   Plugin System · Vector Search                      │
├─────────────────────────────────────────────────────┤
│                  存储层                               │
│   MongoDB · PostgreSQL · Redis · Milvus/PGVector     │
│   MinIO/S3                                           │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 全栈 | Next.js (App Router) | 前后端一体 |
| 数据库 | MongoDB | 主存储 |
| 向量库 | Milvus / PGVector / Tencent VectorDB | 可选 |
| 缓存 | Redis | 会话、限流 |
| 对象存储 | MinIO / S3 | 文件存储 |
| 部署 | Docker Compose | 一键部署 |

## 三、核心架构

### 3.1 目录结构

```
FastGPT/
  projects/
    app/                    — 主应用（Next.js）
      src/
        pages/                — API Routes
          api/
            v1/
              chat/             — 对话 API
              app/              — 应用 API
              dataset/          — 数据集 API
              knowledge/        — 知识库 API
        components/           — React 组件
          core/
            chat/               — 聊天组件
            app/                — 应用组件
            workflow/           — 工作流组件
            dataset/            — 数据集组件
            knowledge/         — 知识库组件
        global/               — 全局配置
        service/              — 服务调用
        support/              — 辅助工具
    plugin/                 — 插件系统
      src/
        nodes/                — 工作流节点
          core/
            ai/
              llm/               — LLM 节点
              chatNode/          — 对话节点
              tools/             — 工具节点
            flow/
              ifElse/            — 条件分支
              loop/              — 循环节点
              variable/          — 变量节点
              http/              — HTTP 请求
            io/
              input/             — 输入节点
              output/            — 输出节点
```

### 3.2 工作流引擎

FastGPT 的核心是自研的 DAG 工作流引擎：

```
┌──────────────────────────────────────────────────┐
│              FastGPT Workflow                      │
│                                                  │
│  ┌──────┐    ┌──────┐    ┌──────┐    ┌──────┐  │
│  │ User │───>│ AI   │───>│Knowledge│─>│Reply │  │
│  │Input │    │Chat  │    │Search  │   │Output│  │
│  └──────┘    └──┬───┘    └──────┘    └──────┘  │
│                 │                                │
│            ┌────┴────┐                          │
│       ┌────▼───┐┌────▼───┐                      │
│       │If-Else ││Tool    │                       │
│       │Node    ││Call    │                       │
│       └────────┘└────────┘                       │
└──────────────────────────────────────────────────┘
```

节点类型：
- **AI 对话节点** — 调用 LLM
- **知识库搜索** — RAG 检索
- **HTTP 请求** — 外部 API 调用
- **条件判断** — If-Else 分支
- **循环** — 迭代处理
- **变量更新** — 变量赋值
- **工具调用** — Function Calling
- **代码运行** — JavaScript 沙箱执行

### 3.3 知识库系统

```
┌────────────────────────────────────────────────┐
│            知识库处理流水线                       │
│                                                │
│  文档上传 → 格式解析 → 文本分片 → 向量化 → 存储  │
│                                                │
│  用户查询 → Query 改写 → 向量检索 → 重排序       │
│         → 上下文注入 → LLM 生成 → 回答           │
└────────────────────────────────────────────────┘
```

文档格式支持：
- PDF、Word、Excel、PPT、CSV、Markdown、TXT
- 网页链接
- API 数据源

分片策略：
- 自动分片（按段落/语义）
- 自定义分片大小
- 递归分片

检索模式：
- 向量检索
- 全文检索
- 混合检索

### 3.4 模型供应商

| 类别 | 供应商 |
|------|--------|
| 国际 | OpenAI、Anthropic、Google、DeepSeek |
| 国产 | 通义千问、文心一言、智谱、MiniMax、百川、讯飞、月之暗面 |
| 本地 | OneAPI（兼容 OpenAI 格式）、Ollama |

### 3.5 应用类型

| 类型 | 说明 |
|------|------|
| 简单对话 | 单轮/多轮对话 |
| 工作流 | 可视化工作流编排 |
| 插件 | 可复用的工具/能力 |

## 四、关键特性

### 4.1 商业化支持

- SaaS 版本（fastgpt.io）
- 私有化部署
- 商业授权（团队版/企业版）
- API 开放平台

### 4.2 多租户

- 团队空间隔离
- 成员权限管理
- API Key 管理
- 用量统计

### 4.3 分享嵌入

- iframe 嵌入
- API 调用
- 分享链接

### 4.4 定时任务

- Cron 定时触发工作流
- 数据同步

## 五、关键设计决策

1. **Next.js 全栈** — 前后端一体，降低部署复杂度
2. **MongoDB 主存储** — 灵活 Schema，适合知识库场景
3. **知识库优先** — 核心差异化在知识库问答，不是通用 AI 平台
4. **国产模型兼容** — 重点适配国内模型供应商
5. **Sealos 生态** — 与 Sealos 云原生平台深度集成

## 六、开发命令速查

```bash
# Docker 一键部署
git clone https://github.com/labring/FastGPT.git
cd FastGPT/deploy/docker
docker compose up -d

# 本地开发
pnpm install
pnpm dev

# 环境变量
cp .env.example .env
```

## 七、与竞品对比

| 维度 | FastGPT | [[dify]] | [[flowise]] |
|------|---------|----------|-------------|
| 定位 | 知识库问答 | 全栈 AI 平台 | 轻量原型 |
| 知识库深度 | 深（核心） | 深 | 浅 |
| 工作流 | 可视化 DAG | 可视化 DAG | 拖拽节点 |
| 国产模型 | 重点支持 | 支持 | 有限 |
| 部署 | Docker 一键 | Docker 多服务 | Docker |
| 数据库 | MongoDB | PostgreSQL | SQLite |
| 多租户 | 原生 | 原生 | 无 |

---

## 相关

- [[dify]] — 全栈 LLMOps 平台（国内双雄）
- [[llama-index]] — 数据 Agent 和工作流框架
- [[flowise]] — 低代码 LLM 构建器
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
