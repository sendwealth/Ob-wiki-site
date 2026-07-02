---
title: Agent Zero
created: 2026-06-27
updated: 2026-06-28
type: entity
tags: [ai-coding, agent, llm, product, project, autonomous]
sources:
  - https://github.com/agent0ai/agent-zero
  - 公众号「如此才是」2026-04-30
confidence: medium
---

# Agent Zero — 自主 AI Agent 框架

> **来源**: 公众号「如此才是」2026-04-30
> **GitHub**: `agent0ai/agent-zero`（17k+ ⭐）
> **核心定位**: 完全开源、本地运行、自主成长的 agentic AI 框架

## 一、核心设计哲学

**一句话**: "Autonomous agentic AI that runs on its own computer, uses and creates tools, learns, self-corrects, and executes transparent workflows."

与传统 Agent 框架的关键差异：
- **不是预设特定任务的代理**，而是动态、有机成长的框架
- **把操作系统本身作为工具**：默认仅带搜索/记忆/通信/代码执行，其他工具由 Agent 动态创建
- **分层多代理架构**（Agent 0 → 子代理），层层分解保持上下文专注
- **几乎无硬编码**：全部行为由 `prompts/default/agent.system.md` 定义，改 prompt 即改行为
- ⚠️ 能做危险操作，**必须在 Docker 沙箱中运行**

## 二、核心功能全景（11 项）

| # | 功能 | 说明 |
|---|------|------|
| 1 | 通用助理+持久记忆 | FAISS 向量搜索，记住历史解决方案/代码/事实 |
| 2 | 电脑即工具+动态自建工具 | 默认仅 4 个工具（搜索/执行/通信/记忆），其余通过 `code_execution_tool` 动态创建 |
| 3 | 多代理协作 | `call_subordinate` 创建子代理，支持 A2A 协议跨实例协作 |
| 4 | 内置 Browser Agent | Playwright Chromium 自动化，支持 vision 模型 |
| 5 | 扩展生态 | Skills（SKILL.md 标准）+ Plugins（一键安装+AI 安全扫描）+ Extensions + MCP + A2A |
| 6 | 内存知识管理 | FAISS 混合内存：Main Memories / Conversation Fragments / Proven Solutions |
| 7 | Projects 系统 | 隔离工作空间，独立内存+Git 集成 |
| 8 | Web UI | 实时流式、可暂停/恢复、文件浏览器+代码编辑器 |
| 9 | 语音能力 | TTS + STT（Whisper 本地） |
| 10 | 模型灵活性 | OpenAI/Anthropic/Grok/OpenRouter/Copilot/Ollama，无密钥泄露 |
| 11 | 其他 | 知识导入、API 访问、Docker 全容器化、环境变量配置 |

## 三、安装方法

**一键安装**:
- macOS/Linux: `curl -L ... | bash`
- Docker: `docker run -d ...`（推荐，自带沙箱）

**源码开发**:
1. `git clone` + VS Code
2. Python 3.12+ 虚拟环境
3. `pip install -r requirements.txt` + Playwright Chromium
4. F5 调试 `run_ui.py`（端口 5000）
5. 可选：单独 Docker 实例做代码执行环境

## 四、技术架构

### 目录结构
```
prompts/        # 所有 prompt 模板（agent.system.md 为核心）
tools/          # 内置工具
plugins/        # 插件系统
skills/         # SKILL.md 技能
agents/         # Agent Profile 配置
memory/         # FAISS 向量存储
extensions/     # Python 扩展
api/            # REST API
webui/          # 前端 UI
agent.py        # 核心 Agent 循环
models.py       # 多模型抽象
```

### Agent Loop
1. 接收上级指令（人类或父 Agent）
2. 加载 VectorDB 记忆 + 相关 Skills
3. Chain-of-Thought 规划 → 决定工具/子代理
4. 执行 → 汇报 → 循环
5. 通信格式：Thoughts + Tool Name + Response

### 内存实现
- FAISS 本地嵌入 + Utility Model 总结
- 自动提取关键信息、压缩上下文
- 支持手动"memorize learning opportunities"

### 安全性
- 容器隔离 + 插件 AI 扫描 + Secrets 管理（`usr/secrets.env`）
- 整个框架无黑箱，源码可读性极高

## 五、设计取舍与启发

Agent Zero 的"Agent 自己创建工具"模式适合**开放探索任务**，但对于确定性管线（如固定内容生成流水线）效率不如预定义节点。但其 FAISS 记忆 + Skills 动态加载系统值得借鉴。

## Wikilinks

- [[superpowers]] — 同样基于 SKILL.md 标准的技能体系，可对比 Skills 设计哲学
- [[gstack]] — 同为 AI 编码 Agent 框架，可对比"预设工作流 vs 动态生成"
- [[agent-sandbox]] — 容器沙箱隔离方案，Agent Zero 的 Docker 沙箱运行需求相关
- [[a2a-protocol]] — Agent Zero 支持 A2A 跨实例协作
