---
title: OpenShell 使用指南
created: 2026-05-27
updated: 2026-05-27
type: concept
tags: [ai, platform, guide, active, openshell]
sources:
  - ~/Projects/OpenShell (源码研究)
  - https://docs.nvidia.com/openshell/latest/
  - https://github.com/NVIDIA/OpenShell
confidence: high
---

# OpenShell 使用指南

> OpenShell 是 NVIDIA 开源的 AI Agent 安全沙箱平台。本指南覆盖从安装到日常使用的完整流程：沙箱管理、策略配置、凭据提供者、推理路由和 TUI 监控。面向希望在本地安全运行 AI Agent 的开发者。

---

## 1. 安装

### 前置条件

- **操作系统**：macOS、Windows WSL 2、Linux
- **容器运行时**：Docker 或 Podman（需运行中）；或 host virtualization（MicroVM）
- **GPU 支持**（实验性）：NVIDIA 驱动 + NVIDIA Container Toolkit

### 安装方式

```bash
# 方式一：官方安装脚本（推荐）
curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh

# 方式二：PyPI（需 uv）
uv tool install -U openshell

# 方式三：指定版本
OPENSHELL_VERSION=x.y.z curl -LsSf https://raw.githubusercontent.com/NVIDIA/OpenShell/main/install.sh | sh
uv tool install openshell==x.y.z

# 方式四：Kubernetes Helm 部署（实验性）
helm install openshell oci://ghcr.io/nvidia/openshell/helm-chart
```

安装后确认：

```bash
openshell --version
```

---

## 2. 核心概念速览

| 概念 | 说明 |
|------|------|
| **Gateway** | 控制平面，管理沙箱生命周期、策略和凭据 |
| **Sandbox** | 隔离的 Agent 执行环境（独立容器） |
| **Policy** | YAML 声明式安全策略（文件系统/网络/进程/推理） |
| **Provider** | 凭据提供者（API Key 等敏感信息的安全注入） |
| **Inference Route** | `inference.local` 虚拟端点 → 模型后端映射 |
| **Supervisor** | 沙箱内本地安全边界，代理所有出站连接 |

架构概览：[[openshell]]

---

## 3. 沙箱管理（sandbox）

### 创建沙箱

```bash
# 基础用法：自动命名，启动 Claude Code
openshell sandbox create -- claude

# 指定名称
openshell sandbox create --name my-agent -- claude

# 选择其他 Agent
openshell sandbox create -- opencode     # OpenCode
openshell sandbox create -- codex        # Codex
openshell sandbox create -- copilot      # GitHub Copilot CLI

# 自定义资源限制
openshell sandbox create --cpu 500m --memory 2Gi -- claude

# GPU 直通（实验性）
openshell sandbox create --gpu --from gpu-enabled-sandbox -- claude

# 从社区目录创建
openshell sandbox create --from gemini             # 社区目录
openshell sandbox create --from ./my-sandbox-dir   # 本地 Dockerfile
openshell sandbox create --from registry.io/img:v1 # 容器镜像
```

沙箱默认包含：`python 3.14`、`node 22`、`gh`、`git`、`vim`、`curl`、网络诊断工具。

### 连接沙箱

```bash
# SSH 连接到默认沙箱（最近使用的）
openshell sandbox connect

# 连接到指定沙箱
openshell sandbox connect my-agent
```

### 列出和删除

```bash
# 查看所有沙箱
openshell sandbox list

# 删除沙箱
openshell sandbox delete my-agent
```

---

## 4. 网络策略（policy）

每个沙箱创建后默认**最小出站权限**。需要通过 YAML 策略开放访问。

### 策略文件结构

```yaml
version: 1

# 文件系统策略（创建时锁定）
filesystem_policy:
  include_workdir: true
  read_only: [/usr, /lib, /proc, /dev/urandom, /app, /etc, /var/log]
  read_write: [/sandbox, /tmp, /dev/null]
landlock:
  compatibility: best_effort

# 进程策略（创建时锁定）
process:
  run_as_user: sandbox
  run_as_group: sandbox

# 网络策略（运行时热重载）
network_policies:
  github_api:
    name: github-api-readonly
    endpoints:
      - host: api.github.com
        port: 443
        protocol: rest
        enforcement: enforce
        access: read-only
    binaries:
      - { path: /usr/bin/curl }
```

### 策略管理命令

```bash
# 应用策略到运行中的沙箱（热重载，无需重启）
openshell policy set my-agent --policy policy.yaml --wait

# 查看当前策略
openshell policy get my-agent

# 查看完整策略（JSON 格式）
openshell policy get my-agent --full -o json

# 删除沙箱级策略（回退到全局）
openshell policy delete my-agent --yes

# 删除全局策略
openshell policy delete --global --yes
```

### 策略生效演示

```bash
# 1. 创建沙箱 — 默认所有出站被阻止
openshell sandbox create --name demo

# 2. 进入沙箱测试 — 被 403 拦截
openshell sandbox connect demo
sandbox$ curl -sS https://api.github.com/zen
curl: (56) Received HTTP code 403 from proxy after CONNECT

# 3. 在宿主机应用策略
sandbox$ exit
openshell policy set demo --policy policy.yaml --wait

# 4. 重新连接 — GET 允许，POST 被 L7 拦截
openshell sandbox connect demo
sandbox$ curl -sS https://api.github.com/zen
Anything added dilutes everything else.

sandbox$ curl -sS -X POST https://api.github.com/repos/octocat/hello-world/issues
{"error":"policy_denied","detail":"POST not permitted by policy"}
```

### 四层防护域

| 层 | 保护内容 | 何时生效 |
|----|----------|----------|
| Filesystem | 读写路径限制 | 创建时锁定 |
| Network | 出站连接控制 | 运行时热重载 |
| Process | 特权升级和危险 syscall | 创建时锁定 |
| Inference | 模型 API 调用重路由 | 运行时热重载 |

### 自动化演示

```bash
bash examples/sandbox-policy-quickstart/demo.sh
```

---

## 5. 凭据提供者（provider）

Agent 需要 API Key 等凭据。OpenShell 自动发现已知 Agent 的凭据，也支持手动创建。

### 自动发现

CLI 自动从环境变量检测以下 Agent 凭据：

| Agent | 环境变量 |
|-------|----------|
| Claude Code | `ANTHROPIC_API_KEY` |
| OpenCode | `OPENAI_API_KEY` / `OPENROUTER_API_KEY` |
| Codex | `OPENAI_API_KEY` |
| GitHub Copilot | `GITHUB_TOKEN` / `COPILOT_GITHUB_TOKEN` |

凭据不会写入沙箱文件系统，通过环境变量安全注入。

### 手动管理

```bash
# 创建提供者
openshell provider create --name my-provider --type openai --credential OPENAI_API_KEY=sk-xxx

# 从现有环境变量创建
openshell provider create --type openai --from-existing

# 列出所有提供者
openshell provider list

# 刷新凭据（OAuth2 等场景）
openshell provider refresh configure my-provider --strategy oauth2-client-credentials
openshell provider refresh status my-provider
openshell provider refresh rotate my-provider
```

---

## 6. 推理路由（inference）

配置沙箱内 `inference.local` 虚拟端点映射到实际模型后端。隐私路由器会剥离调用者凭据、注入后端凭据、转发请求。

```bash
# 设置推理路由
openshell inference set --provider openai --model gpt-4

# 查看当前配置
openshell inference get

# 更新模型
openshell inference update --model gpt-4-turbo
```

Agent 代码中访问 `http://inference.local/...` 即可，路由由平台透明处理。

---

## 7. 日志与监控

### 查看日志

```bash
# 流式查看沙箱日志
openshell logs --tail

# 查看指定沙箱日志
openshell logs my-agent --tail

# 包含安全标记事件
openshell logs my-agent --include-security-flagged
```

### Terminal UI（TUI）

```bash
openshell term
```

实时终端面板，类 k9s 风格：

| 按键 | 功能 |
|------|------|
| `Tab` | 切换面板 |
| `j` / `k` | 上下移动 |
| `Enter` | 选中 |
| `:` | 命令模式 |

Gateway 健康状态和沙箱状态每 2 秒自动刷新。

### OCSF 结构化日志

沙箱安全事件以 OCSF v1.7.0 格式输出，支持 7 种事件类型（网络活动、HTTP 活动、SSH 活动、进程活动、安全发现、配置变更、应用生命周期）。输出格式：Shorthand（可读）+ JSONL（机器解析，可外发）。

---

## 8. Gateway 管理

```bash
# 列出已注册 Gateway
openshell gateway list

# YAML 格式输出
openshell gateway list -o yaml

# 健康检查
openshell doctor check
```

---

## 9. 端口转发与服务暴露

```bash
# 端口转发到沙箱
openshell forward connect my-agent --remote-port 8080 --local-port 8080

# 暴露沙箱服务
openshell service expose my-agent 8080 api
```

---

## 10. 设置管理

```bash
# 查看/设置配置项
openshell settings get log_level
openshell settings set --key log_level --value debug

# 全局设置
openshell settings set --global --key log_level --value info

# 删除设置
openshell settings delete --key log_level --yes
```

---

## 11. 社区沙箱与 BYOC

OpenShell 社区目录提供预构建沙箱镜像：

```bash
# 查看可用沙箱
# https://github.com/NVIDIA/OpenShell-Community

# 从社区目录创建
openshell sandbox create --from ollama    # Ollama 本地推理
openshell sandbox create --from pi        # Pi Agent

# 自定义容器镜像
openshell sandbox create --from ./my-dir  # 本地 Dockerfile
```

参考 [BYOC 示例](https://github.com/NVIDIA/OpenShell/tree/main/examples/bring-your-own-container) 构建自定义沙箱。

---

## 12. 常用工作流

### 工作流 A：首次运行 Claude Code

```bash
export ANTHROPIC_API_KEY=sk-xxx
openshell sandbox create -- claude
# 自动进入沙箱，Claude Code 已配置好 API Key
```

### 工作流 B：受限 GitHub 访问

```bash
# 1. 创建沙箱
openshell sandbox create --name github-agent -- claude

# 2. 编写策略（只读 GitHub API）
# 参考 examples/sandbox-policy-quickstart/policy.yaml

# 3. 应用策略
openshell policy set github-agent --policy policy.yaml --wait

# 4. 连接使用
openshell sandbox connect github-agent
```

### 工作流 C：Kubernetes 集群部署

```bash
# 部署 Gateway
helm install openshell oci://ghcr.io/nvidia/openshell/helm-chart

# 配置 kubectl 上下文后使用 CLI
openshell gateway list
openshell sandbox create -- claude
```

### 工作流 D：诊断问题

```bash
# 系统检查
openshell doctor check

# 查看日志
openshell logs --tail

# TUI 实时监控
openshell term

# Agent 技能诊断（在项目目录下）
# 让你的 Agent 加载 .agents/skills/ 下的技能：
# - openshell-cli: CLI 使用帮助
# - debug-openshell-cluster: Gateway 部署诊断
# - debug-inference: 推理路由诊断
```

---

## 13. 命令速查表

| 命令 | 别名 | 说明 |
|------|------|------|
| `openshell sandbox create -- <agent>` | `sb` | 创建沙箱并启动 Agent |
| `openshell sandbox connect [name]` | | SSH 连接沙箱 |
| `openshell sandbox list` | | 列出所有沙箱 |
| `openshell sandbox delete [name]` | | 删除沙箱 |
| `openshell policy set <name> --policy <file>` | | 应用策略（热重载） |
| `openshell policy get <name>` | | 查看当前策略 |
| `openshell provider create --type <t>` | | 创建凭据提供者 |
| `openshell provider list` | | 列出提供者 |
| `openshell inference set --provider <p> --model <m>` | | 配置推理路由 |
| `openshell inference get` | | 查看推理配置 |
| `openshell logs [name] --tail` | `lg` | 流式查看日志 |
| `openshell forward connect` | `fwd` | 端口转发 |
| `openshell service expose` | `svc` | 暴露沙箱服务 |
| `openshell settings get/set` | | 配置管理 |
| `openshell gateway list` | | 列出 Gateway |
| `openshell term` | | TUI 监控面板 |
| `openshell doctor check` | `dr` | 系统诊断 |
| `openshell completions <shell>` | | 生成 shell 补全 |

---

## 14. 注意事项

- **Alpha 阶段**：单用户模式，面向个人开发环境
- **策略替换语义**：`policy set` 替换整个策略，必须包含 `filesystem_policy` 和 `process` 段
- **安全敏感**：凭据通过环境变量注入，不出现在文件系统中
- **GPU 实验性**：需要 NVIDIA 驱动 + Container Toolkit，沙箱镜像需自带 GPU 库
- **K8s 实验性**：Helm chart 可能有不兼容变更

---

## 相关链接

- [官方文档](https://docs.nvidia.com/openshell/latest/)
- [GitHub](https://github.com/NVIDIA/OpenShell)
- [社区沙箱目录](https://github.com/NVIDIA/OpenShell-Community)
- [快速入门教程](https://docs.nvidia.com/openshell/latest/get-started/quickstart)
- [GitHub 沙箱教程](https://docs.nvidia.com/openshell/latest/tutorials/github-sandbox)
- [支持矩阵](https://docs.nvidia.com/openshell/latest/reference/support-matrix)
- [Roadmap](https://github.com/orgs/NVIDIA/projects/233)

---

**关联页面**：[[openshell]] | [[agent-sandbox]] | [[kagent]] | [[kubernetes-crd]] | [[acp-protocol]] | [[context-mode]]
