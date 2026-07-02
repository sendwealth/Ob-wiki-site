---
title: LangFlow
created: 2026-06-02
updated: 2026-06-02
type: entity
tags: [llm, workflow, low-code, python, langchain, visual-editor]
sources:
  - https://github.com/langflow-ai/langflow
confidence: 0.85
---

# LangFlow

> 可视化 LangChain 工作流编辑器 — 基于 React Flow 的拖拽式编辑器，一键导出 Python 代码或 JSON，DataStax 收购。

---

## 一、项目定位

LangFlow 是基于 React Flow 的可视化 LangChain 工作流编辑器，2024 年被 DataStax 收购后与 Astra DB 深度集成。与 [[flowise]] 是直接竞品：LangFlow 更偏向开发者（可导出代码），Flowise 更偏向低代码用户。

| 指标 | 数据 |
|------|------|
| GitHub Stars | 30k+ |
| 许可证 | MIT |
| 语言 | Python + TypeScript |
| 创建者 | LangFlow 团队 → DataStax |
| 官网 | https://langflow.org |

## 二、技术栈总览

```
┌─────────────────────────────────────────────────────┐
│                  前端（React + React Flow）            │
│   Canvas · Sidebar · Chat · Component Panel          │
├─────────────────────────────────────────────────────┤
│                  LangFlow Core                       │
│   Flow Engine · Component Registry · Export Engine    │
├─────────────────────────────────────────────────────┤
│                  LangChain + Partner Packages         │
│   Chains · Agents · Tools · VectorStores · LLMs      │
├─────────────────────────────────────────────────────┤
│                  存储层                               │
│   SQLite · PostgreSQL · DataStax Astra DB            │
└─────────────────────────────────────────────────────┘
```

| 层 | 技术 | 说明 |
|---|---|---|
| 前端 | React + React Flow + TailwindCSS | 拖拽画布 |
| 后端 | FastAPI + uvicorn | Python API 服务 |
| LLM 框架 | LangChain Python | 底层框架 |
| 数据库 | SQLite / PostgreSQL | 流程存储 |
| 向量库 | Astra DB（DataStax）/ 其他 | 知识库 |
| 部署 | pip / Docker | 多种方式 |

## 三、核心架构

### 3.1 目录结构

```
src/
  langflow/               — 主包
    core/                   — 核心抽象
      component/             — 组件基类
      flow/                  — 流程引擎
      graph/                 — 图数据结构
      cache/                 — 缓存
      template/              — 模板系统
    components/            — 内置组件
      agents/                — Agent 组件
      chains/                — Chain 组件
      documentloaders/       — 文档加载器
      embeddings/            — Embedding 组件
      helpers/               — 辅助组件
      llms/                  — LLM 组件
      memories/              — Memory 组件
      outputs/               — 输出组件
      prompts/               — Prompt 组件
      retrievers/            — 检索器
      tools/                 — 工具
      vectorstores/          — 向量库
      wrappers/              — 封装器
    custom/                — 自定义组件
      custom_component.py     — 自定义组件基类
    services/              — 服务层
      auth/                   — 认证
      chat/                   — 聊天
      database/               — 数据库
      cache/                  — 缓存
    api/                   — API 层
      v1/                     — V1 API
        chat.py
        flows.py
        components.py
    init/                  — 初始化
    utils/                 — 工具函数
  frontend/               — React 前端
    src/
      components/           — UI 组件
      pages/               — 页面
      stores/              — 状态管理（Zustand）
      types/               — TypeScript 类型
```

### 3.2 组件系统

每个 LangFlow 组件继承自 `Component` 基类，定义了：
- **输入端口** — 接收上游数据
- **输出端口** — 输出到下游
- **配置字段** — 节点参数
- **build() 方法** — 返回 LangChain 组件实例

```python
from langflow.custom import Component
from langflow.inputs import TextInput
from langflow.template import Output

class MyComponent(Component):
    inputs = [
        TextInput(name="query", display_name="Query"),
    ]
    outputs = [
        Output(display_name="Result", name="result", method="build_result"),
    ]
    
    def build_result(self) -> str:
        return f"Processed: {self.query}"
```

### 3.3 导出能力（核心差异化）

LangFlow 的核心差异化功能——可导出为 Python 代码或 JSON 配置：

**Python 代码导出**：
```python
# 从 LangFlow 导出的可运行 Python 代码
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(model="gpt-4o")
prompt = ChatPromptTemplate.from_messages([...])
chain = prompt | llm
result = chain.invoke({"question": "Hello"})
```

**JSON 配置导出**：
```json
{
  "nodes": [...],
  "edges": [...],
  "global_variables": {...}
}
```

**API 部署**：
```bash
# 部署为 API 服务
langflow run --flow my-flow.json --port 7860
```

### 3.4 全局变量和凭证

- **全局变量** — 跨流程共享变量
- **凭证管理** — 加密存储 API Key
- **环境变量** — 从 .env 文件加载

## 四、关键特性

### 4.1 自定义组件

支持用户创建自定义组件：
- Python 代码编写
- 在 UI 中即时添加
- 支持所有 LangChain 组件类型

### 4.2 Chat 窗口

内置聊天测试窗口，可直接在编辑器中测试流程。

### 4.3 Astra DB 集成

DataStax 收购后的深度集成：
- Astra DB 作为向量存储
- Astra DB 作为流程存储
- Stargate API 集成

### 4.4 预构建模板

内置常见 LLM 应用模板：
- Basic Prompting
- Conversation Chain
- RAG Pipeline
- Agent with Tools
- Multi-Agent

## 五、关键设计决策

1. **Python 优先** — 后端用 Python（FastAPI），天然与 LangChain 生态对齐
2. **可导出代码** — 核心差异化：从可视化到可部署 Python 代码
3. **React Flow 画布** — 业界最成熟的开源图编辑器
4. **DataStax 生态** — 收购后深度绑定 Astra DB，云向量搜索
5. **组件 = LangChain 类** — 每个组件直接映射 LangChain 的一个类

## 六、开发命令速查

```bash
# 快速开始
pip install langflow
langflow run

# 或 UV
uv add langflow
langflow run

# 开发模式
git clone https://github.com/langflow-ai/langflow.git
cd langflow
make install
make dev

# Docker
docker run -d -p 7860:7860 langflowai/langflow

# 导出流程
langflow export --flow my-flow.json --output python
```

## 七、与竞品对比

| 维度 | LangFlow | [[flowise]] | [[dify]] |
|------|----------|-------------|----------|
| 底层框架 | LangChain Python | LangChain.js | 自研 |
| 代码导出 | Python + JSON | 无 | 无 |
| 目标用户 | 开发者 | 低代码用户 | 全栈 |
| 部署复杂度 | 中 | 低 | 高 |
| DataStax 集成 | 深度 | 无 | 无 |
| 自定义组件 | Python 代码 | 有限 | API 工具 |

---

## 相关

- [[langchain]] — 底层框架
- [[flowise]] — 低代码 LLM 构建器（竞品）
- [[dify]] — 全栈 LLMOps 平台
- [[ai-workflow-landscape]] — AI Workflow 开源项目全景调研
