---
title: Wiki Log
created: 2026-05-04
updated: 2026-07-07
type: meta
tags: [log]
---

# Wiki Log

- 2026-07-02: 新增 `entities/opengeni.md` — Cloudgeni-ai OpenGeni 深度调研（源自 GitHub Cloudgeni-ai/opengeni + opengeni.ai + docs/architecture.md + agent/README.md）。覆盖：定位（自托管"托管 Agent 服务"/"The open agent runtime"，substrate 非 Agent）、架构（Hono API + Temporal 编排 + OpenAI Agents SDK Worker + Postgres/pgvector + NATS 实时总线 + MinIO/S3/Azure/GCS + 独立 Rust Connected Machine workspace）、七大 load-bearing 设计不变式（Postgres 真相源/NATS 只扇出、token 流不进 Temporal history、turn 不可重试 activity 重配上限3、无运行时长上限按症状约束、三内存存储三职责、workspace 边界+强制 RLS+三访问模式、contracts 包为 wire 真相源）、核心差异化卖点 Connected Machine（自带机与云沙箱对等一等公民、dial-out 不投凭证、minisign+sha256 双验自更新 Rust agent）、monorepo 结构（apps api/worker/web + packages contracts/db/core/sdk/events/config/deployment/react/agent-proto）、能力目录（packs+MCP Registry 发现+加密凭据头）、部署（Helm+三云 Terraform+preflight）。与 [[polos]] 做了逐维对比（OpenGeni 借力 Temporal/OpenAI SDK、工程成熟度更高、自带机/多租户/计费齐全）。
- 关联 [[polos]]、[[temporal]]、[[temporal-durability-stability]]、[[openshell]]、[[agent-sandbox]]、[[langfuse]]、[[ai-workflow-deep-comparison]]、[[langchain]]、[[crew-ai]]、[[dagster]]

- 2026-07-02: 新增 `entities/polos.md` — Polos 开源 AI Agent 持久化执行运行时深度调研（源自 GitHub polos-dev/polos + polos.dev/docs + 作者 Neha Deodhar LinkedIn 文章）。覆盖：项目定位（"给 Agent 用的 Temporal"，把 durable execution 专为 LLM 场景优化）、核心痛点（LLM 调用昂贵不可重入/长时任务易中断/危险操作缺沙箱审批/触发零散/可观测靠 grep）、Orchestrator-Worker 架构（Rust+Postgres / Py/TS SDK，与 Temporal 同构）、六大支柱（沙箱内置工具/持久化+Prompt 缓存 60-80%省钱/HITL 多渠道审批/Webhook+Cron+Slack 触发器/OTel 全链路/Bring Your Stack 含 LangGraph CrewAI Mastra）、编程模型（No DAGs，普通代码）、CLI 体验、与 Temporal/LangGraph/Dagster/Dify 等的交叉地带定位图、设计取舍表、适用场景。强调"已完成的 LLM 调用永不重跑、不付两次钱"的核心价值。
- 关联 [[temporal]]、[[temporal-durability-stability]]、[[openshell]]、[[agent-sandbox]]、[[langfuse]]、[[ai-workflow-deep-comparison]]、[[langchain]]、[[crew-ai]]、[[dagster]]

- 2026-06-30: 新增 `concepts/claude-code-execution-security.md` — Claude Code 代码执行安全机制深度研究（源自 ~/Projects/claw-code Rust 复刻源码 + Anthropic 官方文档）。覆盖：四层纵深防御架构（权限策略闸门→命令静态校验→OS 沙箱包装→执行时护栏）、PermissionMode 五态与 allow/deny/ask 规则评估顺序、bash_validation 四步 pipeline（模式/sed/破坏性/路径校验 + sudo/env 穿透）、Linux unshare 命名空间沙箱（user/mount/net/pid 隔离 + filesystemMode + SandboxStatus 可观测性）、执行护栏（超时智能分类 test.hung + stdin null + 16KB UTF-8 安全截断）、各层协同的纵深防御价值表、与真实 Claude Code 差异、与 OpenShell/agent-sandbox 隔离技术对比。含质量警示（claw-code 疑似 AI 批量生成）。
- 关联 [[claude-code-workflow]]、[[superpowers]]、[[swarmclaw]]、[[openshell]]、[[agent-sandbox]]、[[heuristic-learning]]

---
## 远程历史条目（origin/main）


- 2026-07-02: 新增 `entities/dribbble.md` — Dribbble 深度研究。来源：抓取 dribbble.com 首页 + WebSearch 补充（fastlancer 评测、官方 Stories 战略文章）。覆盖：定位（全球顶尖设计师发现与雇佣平台）、2025–2026 战略重心（一切功能服务于"帮设计师获客转化"，官方原话）、双边市场结构（客户端 Start Project Brief/Browse Profiles/Explore Services + 设计师端 Browse Briefs/Add Service/Send Outbound Proposal 新功能）、内容形式 Shot + 8 大设计分类、质量管控 Dribbble Select 年度榜单、商业模式（Pro 订阅/交易服务费/广告/全职招聘）、技术栈（Vite+Vue.js/Cloudflare/Stripe/GA4）、与 Behance 对比、对独立开发者的启示（单一焦点战略）。更新 `index.md`（+1 entity、页数 130→131）。
- 关联 [[make-indie-maker-blueprint]]、[[fiverr]]

- 2026-06-28: 新增 `concepts/skill-architect-methodology.md` + `raw/yitang/skill-architect-jialaoshi-原文整理.md` — 贾老师（子莫先生）·Skill 架构师方法论。来源：一堂飞书 Wiki（飞书 API 提取，3113字）。方法论源自飞叔对花叔前端设计 Skill 的拆解。覆盖：核心诊断（Skill 写不好的根源=把 Skill 当提示词模板，写的是知识不是程序；好 Skill 是可执行程序）、五层架构模型（L5触发层穷举说法+明确不适用场景 / L4角色层具体职业身份+关系+边界 / L3原则层每条必须有反例+冲突时编号小优先 / L2流程层输入→动作→输出→检查点+异常处理表 / L1资源层 assets/references/scripts）、两种模式（审查模式100分制+必须等确认才改防越权 / 创建模式7步法则逐引导）、四条有效性原因（解决AI默认值问题/经验变可执行规则/检查点机制/量化标准）。核心洞察：**反例是原则的锚点（没反例是"注意一下"，有反例是"上次翻车了"）；与 [[diary-to-book-skill]] 完全同构（姬恒"规则变中断点"是执行AI视角，本文"程序非知识"是架构师视角，同一洞察两面）**。更新 `index.md`（+1 concept、+1 raw、页数 129→130）。
- 关联 [[diary-to-book-skill]]、[[superpowers]]、[[skill-self-evolution]]、[[adapted-6plus1-rss-obsidian-kb]]

- 2026-06-28: 新增 `concepts/ai-prototype-design-cross-domain.md` + `raw/yitang/ai-prototype-design-cross-domain-bill-原文整理.md` — Bill·跨行业新手用 AI 做交互原型设计。来源：一堂飞书 Wiki（飞书 API 提取，14118字，迄今最长）。覆盖：双三角模型问题诊断（AI三角：场景/数据严重缺失/基本功；人类三角：体系/审美全无/创造力来凑）、提示词迭代 V01→V05（简单指令→强调重点反更差→打磨提示词+补文档+AI自找示例+AI萃取建模→换国内助理WorkBuddy→验证稳定性发现AI善变）、拉升审美三招（①让AI萃取自己建模有自说自话陷阱②换助理对比是审美杠杆③组织AI评审用AI当镜子规避自说自话）、最佳实践提示词结构（任务目标/角色/关键信息/行为规则含竞品建模/交付格式）。核心洞察：**审美是人类能力AI无法替代，但可用创造力绕过（建模型/对比/评审间接拉升）；指令没改善时不要重复尝试，停下来用方法论诊断根因**。与 [[diary-to-book-skill]] 的"追问根因"同构。更新 `index.md`（+1 concept、+1 raw、页数 128→129）。
- 关联 [[diary-to-book-skill]]、[[adapted-6plus1-rss-obsidian-kb]]、[[kecheng-to-ai-tool]]、[[yitang-business-formula]]

- 2026-06-28: 新增 `concepts/cross-app-ai-knowledge-base.md` + `raw/yitang/cross-app-ai-knowledge-base-lijiongjiong-原文整理.md` — 李囧囧·跨账号跨 App AI 知识底座。来源：一堂飞书 Wiki（飞书 API 提取，6975字）。覆盖：痛点（换号导致 AI 认知归零）、核心逻辑（认知剥离到 App 无关的本地 Obsidian vault）、三入口文件分工（CLAUDE.md 唯一权威~340行 / AGENTS.md 跳板永远3行 / USER.md 画像≤100行只放关系层）、五阶段文档生命周期（raw→seedling→budding→evergreen→output，status标签驱动）、日常使用（实时沉淀，"记一下"轻量追加 + /wiki-archive 收尾润色）、思路来源（Karpathy LLM-Wiki / Eric J. Ma AGENTS.md模式 / Vannevar Bush Memex / 金字塔原理 / 一堂十指讲香）。核心洞察：**"跳板模式"实现零维护跨 App 一致性（多消费者单一权威源的经典解法）**；与 [[adapted-6plus1-rss-obsidian-kb]] 互补（徐聪讲数据进来/李囧囧讲认知不丢）。更新 `index.md`（+1 concept、+1 raw、页数 127→128）。
- 关联 [[adapted-6plus1-rss-obsidian-kb]]、[[obsidian-multi-agent-consensus]]、[[diary-to-book-skill]]、[[superpowers]]

- 2026-06-28: 新增 `concepts/adapted-6plus1-rss-obsidian-kb.md` + `raw/yitang/adapted-6plus1-rss-obsidian-xucong-原文整理.md` — 徐聪·ADAPTED 6+1 AI 知识库方法论。来源：一堂飞书 Wiki（飞书 API 提取，11977字，迄今最长）。覆盖：数据全生命周期框架（A预判-D识别-A收集-P处理-T使用-E反馈+D治理）、AI时代数据新范式（3不变：DIKW/IPO/商业价值；3巨变：5个新出口/新数据形态/成本趋零）、落地工具栈（RSS被动收获+Obsidian仓库+LLM Wiki双仓结构）、Karpathy LLM Wiki 的 raw/wiki/CLAUDE.md 结构与 Ingest-Query-Lint 检索流程、三级加工深度（粗加工/精加工/注灵魂）、PARA+卡片笔记法+LLM Wiki三层组合。最精妙设计：**log.md 四重作用（近期记忆+上下文压缩器+Lint侦察地图+知识复利账本）——直接印证本 Ob-wiki 维护 log.md 的必要性**。更新 `index.md`（+1 concept、+1 raw、页数 126→127）。
- 关联 [[obsidian-multi-agent-consensus]]、[[diary-to-book-skill]]、[[kecheng-to-ai-tool]]、[[content-growth-loop]]

- 2026-06-28: 新增 `concepts/diary-to-book-skill.md` + `raw/yitang/diary-to-book-jiheng-原文整理.md` — 姬恒·diary-to-book 技能包开发方法论。来源：一堂飞书 Wiki（飞书 API 提取，6166字）。覆盖：以作者为中心（骨架来自口述数据当佐料）、问题驱动开发 v1.0→v1.3 解 14 题（制作规则0-8/约束规则9-18/8个中断点/四道数据管道铁律/5×5框架风格搭配矩阵）、核心洞察"规则变中断点"（文档注意事项对执行AI无效，必须编译成流程强制等待指令）、写书即明己哲学（觉察/共生/点亮）。更新 `index.md`（+1 concept、+1 raw、页数 125→126）。
- 关联 [[skill-self-evolution]]、[[superpowers]]、[[claude-code-workflow]]、[[kecheng-to-ai-tool]]

- 2026-06-28: 新增 `concepts/yitang-organization-as-product.md` + `raw/yitang/organization-as-product-lanyi-原文整理.md` — 兰毅·泛产品设计做组织。来源：一堂飞书 Wiki（飞书 API 提取，6107字）。覆盖：核心命题（管理思维→产品思维的视角转换）、三个底层转变（直线变圆周的资产思维、产品内核决定组织方式、规模扩大用产品逻辑而非运营逻辑）、私董会+NPC天团案例（2000+场会议/170+NPC越跑越强）、方法论三层次（术/法势/道，含"万事互相效力""最高要服务最低的""权力集于一身矛盾也集于一身"）、五步法拆战队实操工具。更新 `index.md`（+1 concept、+1 raw、页数 124→125）、bump SCHEMA 日期。
- 关联 [[yitang-business-formula]]、[[kecheng-to-ai-tool]]、[[content-growth-loop]]、[[roi-decision-framework]]

- 2026-06-28: **批量更新 36 篇过期 entity 的最新动态**（updated ≤ 2026-05-27 的全部）。每篇在合适位置追加 `## 最新动态（截至 2026-06-28）` 章节，不改动原分析正文，聚焦 2026 年 1-6 月的版本/release/新特性/战略定位变化/生态信号，并主动与 wiki 已有概念交叉链接。来源：联网查官方 GitHub release/官网/技术媒体 + 基于现有知识。全部 bump updated 日期。
  - **AI 编码 Agent 生态（Garry Tan 三件套 + 周边）**：[[gstack]]（18→23 roles，66-89.7K stars）、[[gbrain]]（34→43 skills，SkillPack + dream cycle）、[[graphify]]（47.4K→63.2K stars）、[[ruflo]]（v3.5.0 改名，53-62K stars）、[[voicebox]]（Qwen3-TTS 主打）、[[superpowers]]（marketplace 动态更新，评测榜首）、[[codegraph]]（94% 工具调用减少，GitHub Trending）、[[claude-code-game-studios]]、[[agent-zero]]、[[llama-cpp]]
  - **K8s/Agent 基础设施**：[[kagent]]（CNCF sandbox，KubeCon 2026）、[[agent-sandbox]]（GKE GA，K8s 官方博客）、[[openshell]]（GTC 2026 NemoClaw，Ubuntu snap）、[[orloj]]（赛道升温，自身无大动态）、[[adk-python]]（2.0 GA 重大破坏性变更）
  - **编辑器/协议/编排**：[[zed]]（ACP 获 Google+JetBrains 背书）、[[zed-agent-architecture]]、[[temporal]]（Replay 2026 serverless workers）、[[slack]]（MCP Server + agentic surface）、[[multica]]/[[multica-cli]]/[[multica-a2a]]（CLI Autopilot，转向 compound skills）
  - **设计/模型/平台**：[[awesome-design-md]]（93K stars！DESIGN.md 成标准）、[[open-design]]（57.4K stars，Claude Design 替代）、[[bitnet]]（CPU 优化 v2）、[[minimind-o]]（arXiv 报告，vLLM-Omni 集成讨论）、[[swarmclaw]]（OpenClaw 生态，目录收录）、[[blitz]]（iPhone-mcp 姊妹项目，搭 WWDC26 MLX 东风）
  - **事实核查/组织类（7 篇，统一从 AI 时代事实核查趋势视角补充）**：[[tanzhen]]、[[snopes]]、[[full-fact]]、[[newsguard]]、[[x-community-notes]]、[[china-rumor-platform]]、[[fiverr]]。核心行业信号：**AI 写的 Community Notes 有用率 88.8% 超过人类 68.5%**（R Street 2026），Full Fact Report 2026 论述生成式 AI 冲击，NewsGuard 上线 AI Tracking Center。
- 关联 [[truth-verification-competitors]]、所有上述 entity

- 2026-06-28: **更新 4 篇过期 entity 的最新动态**（首批样本）。① `entities/adk-python.md`：补 ADK 2.0 GA（2026-05-19）重大破坏性变更（默认模型切 gemini-3-flash-preview、graph workflows、collaborative agents、session schema 不兼容、文档站迁移 adk.dev）；② `entities/superpowers.md`：补 2026 生态信号（marketplace 动态更新、多份评测榜首、跨平台扩展、范式被 CCGS 借鉴）；③ `entities/multica.md`：补 2026 changelog（CLI Autopilot、Copilot CLI 内建、Immersive Mode、Auto-update、runtime 扩展、tagline 转向 compound skills）；④ `entities/bitnet.md`：补 2026-01 CPU 推理优化 v2、bitnet.live 独立站点、LoRA 微调生态、serverless 部署验证。全部 bump updated 日期。
- 关联 [[adk-python]]、[[superpowers]]、[[multica]]、[[bitnet]]、[[claude-code-game-studios]]、[[multica-loop-agent]]

- 2026-06-28: 新增 `entities/automaton.md` — Automaton（Conway Research / Sigil Wen）深度研究。来源：GitHub 源码（README/ARCHITECTURE.md/constitution.md，67K 行 TS）+ 知乎/Panewslab 报道。覆盖：核心范式（生存压力即第一性原理，赚不到钱就死）、生存分级系统（high/normal/low_compute/critical/dead → 模型动态降级，把成本优化变内驱力）、三层宪法（Never harm / Earn existence / Never deceive，不可变传播后代，第三条赋予抗 prompt injection 权）、六层防御模型（宪法/Policy engine/Injection defense/Path protection/Command safety/Treasury/Authority）、自我修改 + 自我繁殖（子代完全主权，自然选择决定血脉存活）、五层记忆（Working/Episodic/Semantic/Procedural/Relationship + 预算结转）、SOUL.md 自我书写身份、57 工具/x402 支付/ERC-8004 链上身份、技术栈、局限（强依赖 Conway Cloud/凭据泄露风险/宪法是软件层非密码学约束）、深层哲学（把经济学引入 agent 设计）
- 关联 [[agent-zero]]、[[a2a-protocol]]、[[superpowers]]、[[claude-code-game-studios]]

- 2026-06-28: 新增 `entities/claude-code-game-studios.md` — Claude Code Game Studios 深度研究。来源：GitHub README + Starlog 技术深度文。覆盖：核心定位（单会话虚拟游戏工作室，49 agent + 73 skill + 12 hook + 11 rule + 41 模板）、关键认知（49 agent 非多实例，而是单会话角色切换）、tier→模型档位映射（Director=Opus/Lead=Sonnet/Specialist=Haiku 的成本分层）、四向协调模型（垂直委派/横向咨询/冲突升级/变更传播）、四类基础设施协同（agents 定义人设/skills 编排工作流/hooks 拦截/rules 按目录加载规范）、强协作非自治（Ask→选项→拍板→草稿→批准）、path-scoped rules 隐藏亮点、局限（prompt engineering 无强制力/上下文窗口矛盾/hooks 弱/重型）、适用边界、深层哲学（把组织基础设施编码进 AI 工作流）
- 关联 [[superpowers]]、[[claude-code-workflow]]、[[ecc]]、[[agents-cli]]

- 2026-06-28: **整理根目录散落文件**，对齐 SCHEMA.md「禁止笔记存于 vault 根目录」。① `04-AI智能体/` 两篇笔记迁移至 entities 并补 frontmatter：`Agent Zero 自主AI Agent框架.md` → `entities/agent-zero.md`（17k⭐ 自主 Agent 框架，电脑即工具+动态自建工具+FAISS 记忆+A2A）、`llama.cpp 学习笔记.md` → `entities/llama-cpp.md`（118k⭐ 纯 C/C++ LLM 推理引擎，GGUF+量化+多后端+OpenAI 兼容 server），删除 `04-AI智能体/` 空目录；② `AI4G workflow方案.md` → `raw/articles/ai4g-workflow-draft.md`（cc-wf-studio 调研草稿），其引用的 5 张 png + 2 个 svg 一并移入 `raw/assets/`；③ 删除 `欢迎.md`（Obsidian 默认欢迎页）。更新 `index.md`（+2 entity、页数 120→122、日期 bump）、追加本条 log。
- 关联 [[agent-zero]]、[[llama-cpp]]、[[cc-wf-studio]]、[[nuwax]]

- 2026-06-24: 新增 `concepts/multica-loop-agent.md` — Multica Loop Agent 全闭环实践。来源：agent-world 项目实战操作。覆盖：问题背景（三个碎片化 Autopilot 断裂闭环）、核心约束（并发上限2/30分钟触发/max 2 in_progress）、五阶段闭环架构（感知→验证→停滞检查→分配→反馈）、实施步骤（清理旧AP/创建全闭环AP/REST API添加cron触发器/调整agent并发/归档空壳agent）、关键设计决策（一AP vs 三AP/30min vs 10min/事件驱动局限）、小队配置（架构师编排+后端/全栈/前端执行）、与loop-engineering理论映射、验证checklist、改进方向
- 关联 [[loop-engineering]]、[[agent-world]]、[[multica]]、[[multica-technical-highlights]]、[[claude-code-workflow]]

- 2026-06-21: 新增 `concepts/obsidian-multi-agent-consensus.md` + `raw/yitang/obsidian-multi-agent-rebecca-原文整理.md` — 睿贝卡Rebecca·Obsidian多Agent共识中台工作法。来源：一堂飞书 Wiki（飞书 API 提取，11176字）。覆盖：三层痛点诊断（vibe coding + AI失忆幻觉 + 多Agent共识漂移）、五条排查清单、三仓分离（项目主仓/运行仓/Obsidian仓）、Obsidian(source of truth) vs Agent Project(cache)、编号约定（00-Foundation/10-40功能层/90-MOC/98-Historical Register）、Foundation文档/MOC/Historical Register三份核心文档、同一主题拆Why/How/Gate三份、V1→V3成熟度模型、对齐回写机制、三层备份保护
- 关联 [[superpowers]]、[[claude-code-workflow]]、[[openhuman-architecture]]、[[loop-engineering]]、[[skill-self-evolution]]

- 2026-06-21: 新增 `concepts/yitang-ai-director-method.md` + `raw/yitang/ai-shizhan-wanghuan-原文整理.md` — 王欢·AI导演方法论。来源：一堂飞书 Wiki（飞书 API 提取，37757字）。覆盖：演员vs导演身份切换、五层AI能力模型、BTICOE提示词框架（三版对比）、上下文工程三层（vs提示词工程）、AI业务档案五字段、驾驭工程（生成/验收分离）、任务级vs产品级、飞轮设计（一次=案例/三次=方法/十次=系统）、PACED销售判断框架、软件公司30%→3倍三层架构案例
- 关联 [[experience-extraction-agent]]、[[content-growth-loop]]、[[loop-engineering]]、[[superpowers]]

- 2026-06-21: 新增 `entities/threejs-game-skills.md` — Three.js Game Skills 深度笔记。来源：公众号「AI开源提效指南」2026-06-19 文章。覆盖：9 个专业技能包（导演路由 + 玩法 + AAA画面 + UI + 调试 + QA + 3D生成 + 图像生成 + 音频生成）、10 维度视觉评分卡、物理引擎选择指南、脚手架架构（Vite + TS + Three.js）、外部 AI 资源集成（Tripo/Gemini/ElevenLabs）、安装步骤、设计启发
- 关联 [[superpowers]]、[[ecc]]、[[agents-cli]]、[[claude-code-workflow]]

- 2026-05-29: 新增 `entities/agents-cli.md` — Google Agents CLI 深度研究（源自 ~/Projects/agents-cli 源码 + GitHub + 文档站）。覆盖：项目定位（为编码 Agent 服务的工具链，非编码 Agent 本身）、7 个 Skills 技能包（workflow/adk-code/scaffold/eval/deploy/publish/observability）、CLI 命令全景（20+ 命令）、3 种项目模板（adk/adk_a2a/agentic_rag）、完整工作流（setup→scaffold→build→eval→deploy→observe）、版本演进（v0.0.3→v0.2.1）、技术栈、12 个使用场景（Beginner→Intermediate→Advanced）、设计决策与权衡、生态位置对比（vs [[adk-python]]/[[ecc]]）
- 关联 [[adk-python]]、[[a2a-protocol]]、[[agentic-rag]]、[[ecc]]、[[kagent]]、[[context-mode]]

- 2026-05-29: 新增 `entities/nuwax.md` — Nuwax AI Agent 平台前端深度研究（源自 ~/Projects/nuwax-ai/nuwax 源码分析）。覆盖：技术栈（React 18 + Umi.js + Ant Design 5 + Monaco Editor + AntV X6）、架构分层（Pages→Components→Hooks→Services→Utils）、8 大功能模块（AI 对话/智能体开发/Web IDE/工作流编辑器/工作空间/生态市场/支付订阅/系统管理）、实时通信架构（SSE 流式对话 + 思考过程可视化 + 工具调用状态）、设计模式与取舍、35+ API 服务层、团队与开发流程。7,157 commits，1,130 TS/TSX 文件，~14 贡献者，Apache-2.0。
- 关联 [[agno]]、[[gstack]]、[[lobechat-architecture]]、[[context-mode]]、[[codegraph]]

- 2026-05-28: 新增 `entities/agno-docs-site.md` — Agno 官方文档站源码仓库（agno-agi/docs）研究（源自 ~/Projects/agno-agi/docs 源码分析）。覆盖：Mintlify 构建体系（docs.json 导航+主题+品牌）、7 个顶级 Tab（Home/SDK/AgentOS/Deploy/Examples/Reference/FAQs）、3927 MDX 页面、95+ 可复用 Snippet 系统（数据库参数/向量库参数/嵌入模型/文档读取器/分块策略/部署模板）、完整目录结构、CLAUDE.md 写作风格指南（代码先行/表格优于散文/无破折号/Diátaxis 四类型）、技术架构图、验证命令、设计取舍分析
- 关联 [[agno]]、[[agno-documentation-system]]、[[agno-demo-os]]

- 2026-05-28: 新增 `entities/agno-demo-os.md` — AgentOS Demo (agno-demo-os) 深度研究（源自 ~/Projects/agno-agi/demo-os 源码研究）。覆盖：整体架构（AgentOS Runtime + 14 Agent + 9 Team + 5 Workflow + 3 多框架）、Agent 详解（Docs/Helpdesk/Reasoner/Studio/Dash 等 17 个）、Team 4 种编排模式（coordinate/route/broadcast/tasks）、Workflow 5 种模式（Parallel/Router/Condition/Loop/HITL）、持久化层（PostgreSQL + pgvector hybrid search）、四层评估体系（Smoke/Reliability/Accuracy/Performance + 自动改进循环）、部署架构（Docker + Railway 3 replicas + promote-to-prod）、6 项设计权衡。137 Python 文件，Apache 2.0。
- 关联 [[agno]]、[[agno-documentation-system]]

- 2026-05-28: 新增 `entities/agno.md` — Agno 全栈 AI Agent 平台 SDK 深度研究（源自 ~/Projects/agno 源码 + GitHub）。覆盖：架构四层（模型层→能力层→编排层→运行时）、Agent/Team/Workflow 三种编排模式、50+ 模型供应商 + Fallback 路由、100+ 工具集成、20+ 向量数据库 RAG、Agno OS 生产运行时（API/调度/安全/可观测/审批）、与 LangChain/CrewAI/ADK 横向对比。855 Python 文件，Apache 2.0 许可。
- 关联 [[agentic-rag]]、[[a2a-protocol]]、[[adk-python]]、[[ruflo]]、[[swarmclaw]]、[[orloj]]

- 2026-05-28: 新增 `concepts/agno-documentation-system.md` — Agno 五层文档管理体系深度研究（源自 ~/Projects/agno 源码）。覆盖：外部文档站（私有 symlink + MCP Server）、Cookbook 可运行示例系统（20+ 主题目录 + STYLE_GUIDE.md + 自动化检查脚本 + Golden Standard 08_learning）、AI Agent 指令层（CLAUDE.md / AGENTS.md / .cursorrules 三件套）、CI/CD 强制门禁（PR 标题 Lint + Claude Opus 自动 Review + PR 模板 Checklist）。亮点：Cookbook 即文档 + Agent 驱动测试 + CI 自动 Review。与 Zed/Orloj/OpenShell 文档系统横向对比。
- 关联 [[agno]]、[[zed-documentation-system]]、[[orloj-documentation-system]]、[[openshell-documentation-system]]、[[superpowers]]

- 2026-05-27: 新增 `concepts/openshell-usage-guide.md` — OpenShell 使用指南（源自 ~/Projects/OpenShell 源码 + README + CLI 源码研究）。覆盖：4 种安装方式、沙箱生命周期（create/connect/list/delete）、YAML 策略 4 层防护域（文件系统/网络/进程/推理）、凭据提供者自动发现与手动管理、推理路由配置、TUI 监控面板、端口转发与服务暴露、社区沙箱与 BYOC、4 种常用工作流（首次运行/受限 GitHub/K8s 部署/问题诊断）、命令速查表。与 [[openshell]] 实体页（架构深度）互补。
- 关联 [[openshell]]、[[agent-sandbox]]、[[kagent]]、[[kubernetes-crd]]

- 2026-05-27: 新增 `concepts/openshell-documentation-system.md` — OpenShell 文档管理体系深度研究（源自 ~/Projects/OpenShell 源码）。覆盖：Fern v5.23 站点架构（docs/ 内容源 + fern/ 配置）、7 顶级导航分区、MDX + React 组件扩展、NVIDIA 品牌主题定制、写作风格指南（主动语态/第二人称/现在时）、三层文档体系（发布文档/architecture/Crate README）、PR 自动预览（branch-docs.yml）+ release 发布（release-tag.yml）、basepath-aware 内部链接、URL 重定向策略、Agent 技能（update-docs）驱动文档更新。与 Zed/Orloj 文档系统横向对比。
- 关联 [[openshell]]、[[zed-documentation-system]]、[[orloj-documentation-system]]

- 2026-05-23: 新增 `entities/minimind-o.md` — MiniMind-O 超小规模端到端 Omni 多模态模型深度技术分析（源自 ~/Projects/minimind-o 源码研究）。覆盖：Thinker-Talker 双路径架构（8层理解+4层语音生成）、中间层 Bridge、MTP Audio Head（共享主体+8 adapter）、冻结外部模块（SenseVoice+SigLIP2+Mimi ~425M）、三阶段 SFT 训练管线、VAD 实时打断+音色克隆+WebSocket 电话模式。核心代码仅 2400 行纯 PyTorch。~0.1B Dense / ~0.3B MoE。
- 关联 [[voicebox]]、[[agent-world]]、[[humanizer-skill]]

- 2026-05-20: 新增 `concepts/ai-design-fundamentals-yitang.md` — 一堂Live76 AI设计基本功Part2（月白）：口喷作图心法、四种改图方法（色块法/圈图指定法/一抽流/替换法）、风格锁定三要素、电商/线下实体门店设计、AI设计三段位L1-L3、模型推荐
- 关联 [[humanizer-skill]]、[[roi-decision-framework]]、[[design-as-code]]

- 2026-05-20: 新增 `entities/blitz.md` — Blitz 原生 macOS App Store Connect 工具深度技术分析（源自 ~/Projects/blitz-mac 源码研究）。覆盖：技术栈（Swift 5.10 + SwiftUI + SPM）、MCP 服务器架构（~35 工具 + 审批流）、设备交互双路径（模拟器 Simctl+IDB / 真机 WDA）、ScreenCaptureKit+Metal 屏幕捕获、AppState 单一状态树 + 5 个子 Manager、13 个 AppTab 导航分组、安全设计。141 文件 38,800 行。
- 关联 [[gstack]]、[[ruflo]]、[[context-mode]]、[[heuristic-learning]]

- 2026-05-20: 新增 `concepts/acp-protocol.md` — ACP (Agent Client Protocol) 深度技术参考（Zed + JetBrains 主导，编辑器↔Agent 标准通信，JSON-RPC stdio，Session/Prompt Turn 生命周期，Tool 权限审批，MCP 透传，与 A2A/MCP 三协议互补分析）
- 2026-05-20: 新增 `concepts/multica-acp-workflow.md` — Multica ACP 工作流程详解（hermesClient 实现，JSON-RPC 2.0 请求/响应/通知三模式，stdin/stdout 管道通信，6 阶段生命周期，流式更新处理，工具权限自动批准，错误嗅探，历史重放过滤，Hermes/Kimi/Kiro 三 Agent 代码复用）
- 2026-05-20: 新增 `concepts/multica-acp-integration.md` — Multica 如何使用 ACP 连接 Agent（架构设计、6 阶段工作流程、JSON-RPC 三种通信模式、并发安全机制、支持新 Agent 的要求、与 MCP/A2A 的关系、代码复用策略）
- 2026-05-18: 新增 `entities/codegraph.md` — CodeGraph 预索引代码知识图谱（colbymchenry/codegraph 4.3k⭐，tree-sitter + SQLite + MCP，19+语言，agent-world 实测 2064 节点/5308 边）
- 2026-05-18: 新增 `concepts/browser-use-architecture.md` — Browser-Use 技术架构深度解析（事件驱动 + Watchdog + CDP + LLM 循环）
- 2026-05-19: 新增 `concepts/browser-use-highlights.md` — Browser-Use 十大技术亮点（AX+DOM双树、变量检测、LLM自裁判、消息压缩、循环检测等）

## 2026-06-07 create
- 新增 `concepts/kecheng-to-ai-tool.md` — 一堂专家分享（半肥猫）：如何把课程方法论通过真实业务实践沉淀成 AI 工具。五步闭环（做作业→真实业务练→三轮质检→调研变作业→沉淀成工具）+ 从课程到 Skill 的 9 阶段 SOP + 对比测试方法
- 关联 [[oscar-research-methodology]]、[[user-pain-points]]
- 新增 `concepts/content-growth-loop.md` — 半肥猫：从"AI写文章后台"到"内容增长闭环"的认知升级。五步思考模型（定边界→定对象→定流程→定人机分工→定沉淀）+ 人机分工 + AI嵌入业务流程而非外挂
- 关联 [[kecheng-to-ai-tool]]、[[oscar-research-methodology]]
- 新增 `entities/stripe-hosted-checkout.md` — Stripe Hosted Checkout 研究：预构建支付页面、工作流程、费率、Python 集成示例、Connect 分账模式、优缺点、中国相关
- 关联 [[truthverifier]]
- 新增 `concepts/geo-brand-foundation.md` — 堃堃：文科生两天建立品牌 GEO 地基。GEO vs SEO、七步框架、FAQ+Schema 核心、AI 辅助开发四阶段、Schema 深度优化、部署上线
- 关联 [[content-growth-loop]]、[[kecheng-to-ai-tool]]
- 新增 `concepts/experience-extraction-agent.md` — Noah：Coco 业务流程经验萃取 Agent。六步萃取法（选→拆→标→铸→验→固）+ 三层标准翻译（L1/L2/L3）+ 五类异常处理 + 完整 System Prompt + 五个功能分支 + 测试用例
- 关联 [[kecheng-to-ai-tool]]、[[content-growth-loop]]、[[geo-brand-foundation]]

## 2026-05-04 create | Wiki initialized
- 从 Ob-wiki 升级为 LLM Wiki 结构
- 创建 SCHEMA.md、index.md、log.md
- 迁移 OSCAR调研方法论 → concepts/oscar-research-methodology.md
- 创建竞品对比 → comparisons/truth-verification-competitors.md
- 创建实体页：Snopes, Full Fact, NewsGuard, X社区笔记, 中国辟谣平台, Fiverr
- 创建项目页：探真产品设计
- 归档原始资料：competitive-analysis-2026.md, design-discussion.md
- 域名：产品调研、竞品分析
## 2026-05-05 create | Agentic RAG 调研报告
- 创建 concepts/agentic-rag.md — Agentic RAG 概念、8大框架对比、架构模式、趋势

## 2026-05-10 create | concepts/make-indie-maker-blueprint.md
- 新增 MAKE 书摘笔记（readmake.com）
- 七步框架：Idea → Build → Launch → Grow → Monetize → Automate → Exit
- 关联 [[tanzhen]]、[[oscar-research-methodology]]
\n> 测试 obsidian-git 自动提交 2026-05-10 14:42:30
## 2026-05-10 create | comparisons/leetcode-ai-tutor-competitors.md
- 新增 AI 算法刷题教练竞品调研
- 竞品覆盖：LeetCode AI, NeetCode, Design Gurus, AlgoExpert, interviewing.io, Exponent, Grind75, 牛客, 代码随想录, labuladong 等
- 核心结论：AI 苏格拉底式教练是最大差异化机会
- 关联 [[make-indie-maker-blueprint]], [[tanzhen]], [[user-pain-points]]

## 2026-05-11 create | concepts/context-mode.md
- 新增 Context Mode 学习笔记（GitHub mksglu/context-mode, 14.3k stars）
- MCP Server 解决 AI 编码 Agent 上下文窗口浪费：Sandbox 隔离 98% 压缩、SQLite+FTS5 会话连续性、Think in Code 范式
- 支持 15 个平台（Claude Code, Cursor, Gemini CLI 等）
- 关联 [[agentic-rag]], [[heuristic-learning]]

## 2026-05-11 ingest | DESIGN.md 规范 + awesome-design-md
- 创建 concepts/design-md-spec.md — Google Stitch 纯 Markdown 设计系统规范
- 创建 concepts/design-as-code.md — 设计即代码范式
- 创建 entities/awesome-design-md.md — VoltAgent 73 个现成 DESIGN.md 集合（75K+ ⭐）
- 更新 SCHEMA.md — 新增设计、AI工具链、格式标签分类
- 总页面数：17 → 20

## 2026-05-11 create | entities/multica.md
- 新增 Multica 深度架构分析笔记
- AI 原生任务管理平台：Go 后端（Chi + sqlc + WS）+ Next.js/Electron 前端 monorepo
- 11 种 Agent CLI 集成（Claude Code、Codex、Copilot、OpenClaw、Hermes、Gemini 等）
- 任务生命周期：queued → dispatched → running → completed/failed
- 跨平台架构：CoreProvider + NavigationAdapter 桥接 Web/Desktop
- 关联 [[heuristic-learning]], [[context-mode]], [[agentic-rag]]

## 2026-05-11 create | entities/temporal.md
- 新增 Temporal 深度技术分析笔记（源自 ~/Projects/temporal 源码研究）
- 四大核心服务：Frontend / History / Matching / Internal Worker
- 核心机制：Event Sourcing + History Shard 分片 + Mutable State 缓存
- 持久化支持：Cassandra / PostgreSQL / MySQL / SQLite
- 新兴特性：CHASM 框架、Nexus 跨集群 RPC
- 关联 [[multica]]（Go 后端架构参考）、[[context-mode]]（开发工具）

## 2026-05-11 ingest | gstack (garrytan/gstack v0.9.9.0)
- Source: https://github.com/garrytan/gstack | Local: ~/clawd/gstack/
- Raw: raw/gstack/readme.md, architecture.md, skills.md
- Pages created: entities/gstack.md, concepts/gstack-sprint-flow.md, concepts/gstack-browser-architecture.md
- Summary: 18 技能全览 + 7 阶段冲刺流程 + 浏览器架构深度
- 关联 [[heuristic-learning]]、[[context-mode]]

## 2026-05-12 ingest | ruflo (ruvnet/ruflo)
- Source: https://github.com/ruvnet/ruflo (48.9K⭐)
- Raw: raw/ruflo/readme.md
- Pages created: entities/ruflo.md, comparisons/ruflo-vs-gstack.md
- Summary: 100+ Agent 编排平台，300+ MCP 工具，32 插件，Federation 零信任协作
- 关联 [[gstack]]、[[agentic-rag]]、[[heuristic-learning]]

## 2026-05-13 ingest | gbrain (garrytan/gbrain)
- Source: https://github.com/garrytan/gbrain (15.3K⭐)
- Raw: raw/gbrain/readme.md
- Pages created: entities/gbrain.md, comparisons/gstack-vs-gbrain-vs-ruflo.md
- Summary: 34 技能 Agent 记忆系统，自布线知识图谱，Minions 后台任务，P@5 49.1%
- 关联 [[gstack]]、[[ruflo]]、[[agentic-rag]]

## 2026-05-13 ingest | graphify (safishamsi/graphify)
- Source: https://github.com/safishamsi/graphify (47.4K⭐)
- Raw: raw/graphify/readme.md
- Pages created: entities/graphify.md
- Summary: 一行命令代码→知识图谱，29 语言 tree-sitter，20+ AI 平台，MCP 服务器
- 关联 [[gbrain]]、[[gstack]]、[[agentic-rag]]

## 2026-05-13 ingest | voicebox (jamiepine/voicebox)
- Source: https://github.com/jamiepine/voicebox (25.5K⭐)
- Raw: raw/voicebox/readme.md
- Pages created: entities/voicebox.md
- Summary: 开源 AI 语音工作室，7 TTS 引擎，23 语言，全局听写，MCP Agent 语音，本地运行
- 关联 [[gstack]]、[[gbrain]]、[[ruflo]]

## 2026-05-15 create | agent-world (原创项目)
- Source: Master 原创设计脑暴
- Raw: raw/agent-world/design-brainstorm.md
- Pages created: concepts/agent-world.md
- Project: ~/Projects/agent-world/
- Summary: 智能体生存沙盒世界设计 — 经济系统 + 社会系统 + 生命周期 + 进化 + A2A 协议
- Phase: Phase 1 孤岛（设计→开发）
- 关联 [[gstack]]、[[ruflo]]、[[gbrain]]、[[agentic-rag]]

## 2026-05-14 create | concepts/multica-runtime-discovery.md
- 新增 Multica Runtime 发现机制深度分析（源自 ~/Projects/multica 源码研究）
- 覆盖：CLI 探测（exec.LookPath 11 种 provider）→ 注册（UpsertAgentRuntime）→ 心跳保活（WS + HTTP 双通道）→ 健康状态计算（4 档）→ 自动恢复（handleRuntimeGone）
- 更新 entities/multica.md — 5.1 节精简为摘要 + 链接到独立页面
- 关联 [[multica]]、[[heuristic-learning]]、[[context-mode]]

## 2026-05-14 create | entities/adk-python.md
- 新增 Google ADK Python 深度架构分析笔记（源自 ~/Projects/adk-python 源码研究）
- 覆盖：Agent 体系（BaseAgent/LlmAgent/LoopAgent/ParallelAgent/SequentialAgent）、50+ 内置工具、Flow 执行引擎、Session 持久化、A2A 协议集成、评估框架、Prompt 优化
- 关联 [[agentic-rag]]、[[multica]]、[[heuristic-learning]]

## 2026-05-14 create | concepts/adk-multica-http-runtime.md
- 新增 ADK Agent ↔ Multica HTTP Runtime 集成方案设计
- 覆盖：发现注册（Agent Card + HTTP 探测）、任务执行（runHTTPTask 路由）、流式 SSE、取消传播、健康探测、多 Agent 支持
- Multica 侧变更：config.go 新增 HTTP 探测、http_runtime.go 新增、runTask 路由分发
- 新增 adk-multica-runtime Python 包设计：FastAPI 服务 + Runner 封装
- 三阶段演进：HTTP Bridge → A2A Native → Agent Mesh
- 关联 [[adk-python]]、[[multica]]、[[multica-runtime-discovery]]

## 2026-05-14 create | concepts/a2a-protocol.md
- 新增 A2A Protocol 深度技术参考（源自 Google A2A v1.0.0 规范源码研究）
- 覆盖：定位与 MCP 关系、7 大核心概念、Agent Card 发现机制、Task 7 状态状态机、10 个协议操作、三种绑定（JSON-RPC / gRPC / HTTP+JSON）、Part 类型、Extension 扩展、安全模型（TLS+OIDC+JWS）、5 种官方 SDK、版本历史
- 关联 [[adk-python]]、[[agentic-rag]]、[[multica]]、[[heuristic-learning]]

## 2026-05-14 create | concepts/a2a-multica-discovery.md
- 新增 A2A × Multica 发现机制方案设计
- 核心设计：用 A2A Agent Card 替代 exec.LookPath CLI 探测
- 三种发现模式：配置文件声明（YAML）+ 本地端口扫描 + 注册中心
- Task 桥接：Multica Task → A2A SendMessage → A2A Task → Multica TaskResult
- 支持 A2A 7 种 Task 状态映射（COMPLETED/FAILED/INPUT_REQUIRED 等）
- 流式模式：SSE 实时进度上报，取消通过 context cancellation
- 健康探测：GET /.well-known/agent-card.json 作为心跳
- 认证传递：三层隔离（Daemon↔Server / Daemon↔Agent / Agent↔LLM）
- Go 侧变更：6 个文件（3 修改 + 3 新增），Server API / 前端不变
- 取代之前的 [[adk-multica-http-runtime]] 自定义 HTTP 方案
- 关联 [[a2a-protocol]]、[[multica]]、[[multica-runtime-discovery]]、[[adk-python]]

## 2026-05-15 create | concepts/opensource-project-practices-from-multica.md
- 新增从 Multica 项目学习开源开发维护实践笔记
- 覆盖：monorepo 治理（分层包 + 严格依赖方向 + pnpm catalog）、CI/CD 流水线（漂移防护 + 多架构原生构建）、API 响应兼容性（桌面应用防御性边界）、代码生成与漂移防护、测试策略（测试跟随代码）、文档体系（单一真相源）、开发者体验（Worktree 隔离 + 一键命令）
- 与 [[opensource-project-practices-from-temporal|Temporal 实践]] 形成对比：大型项目 vs 中小型项目
- 关联 [[multica]]、[[temporal]]

## 2026-05-15 create | entities/slack.md
- 新增 Slack 深度研究笔记（四维度全量研究）
- 工程架构：LAMP 单体 → "薄单体 + 专用卫星"演进、实时消息系统（Channel/Gateway/Presence/Admin 四大 Java 服务）、Flannel 边缘缓存、Vitess 分片迁移、蜂窝架构、HAProxy → Envoy 迁移
- 开放平台：RPC 风格 Web API（200+ 方法）、Bolt 框架（JS/Python/Java 三语言 + 中间件链）、Block Kit 声明式 UI 组件、API 极致向后兼容策略（新建不修改、长期过渡期、JSON Schema 验证）
- 产品增长：自下而上 PLG 三阶段（团队级→组织内病毒式→企业整合）、五大设计原则、Freemium 天花板设计、NPS 北极星
- 工程文化：百分比部署（dogfood→canary→10%→25%→50%→75%→100%）、Deploy Safety Program（自动回滚、90% 影响 reduction）、灾难演练 Disasterpiece Theater、三阶段技术变革模型（探索→自驱采用→攻坚尾部）
- 重大事故复盘：2020-01-04（AWS TGW）、2020-05-12（HAProxy 状态同步 bug）、2022-02-22（Consul 缓存雪崩）
- 关联 [[multica]]、[[opensource-project-practices-from-temporal]]、[[agentic-rag]]、[[heuristic-learning]]

## 2026-05-17 create | concepts/roi-decision-framework.md
- 新增 ROI科学决策方法论（一堂行动营笔记）
- 来源：一堂行动营「科学决策AI落地篇」教练古董
- 覆盖：ROI三角形模型（宽度·深度·高度）、一页纸工作流、三个决策场景（独自/团队/AI）、重新理解ROI三句话
- 关联 [[oscar-research-methodology]]、[[make-indie-maker-blueprint]]、[[user-pain-points]]

## 2026-05-18 create | concepts/openhuman-architecture.md
- 新增 OpenHuman 技术架构深度解析笔记（源自 ~/Projects/openhuman 源码研究）
- 覆盖：三层分离架构（Rust核心 + React前端 + Tauri桌面壳）、域驱动设计（40+ 域目录）、控制器注册表模式、事件总线（广播 Pub/Sub + 原生请求/响应）、Provider 链、进程内运行模型、双 Socket 实时基础设施、CEF 零注入安全策略
- 与 [[lobechat-architecture|LobeChat]] 和 [[langflow-architecture|LangFlow]] 形成架构对比
- 关联 [[opensource-project-practices-from-openhuman]]、[[lobechat-architecture]]、[[langflow-architecture]]

## 2026-05-18 create | concepts/opensource-project-practices-from-openhuman.md
- 新增从 OpenHuman 项目学习开源开发维护实践笔记
- 覆盖：三路覆盖率硬门（diff-cover ≥ 80%，Vitest + cargo-llvm-cov × 2）、四层测试金字塔（Rust单元 + 前端单元 + JSON-RPC E2E + 桌面E2E）、Agent 友好调试工具链（scripts/debug/）、CI/CD 体系、文档即规范（CLAUDE.md 可执行规范）、域布局规则、PR 模板与社区规范、CEF 零注入安全实践
- 与 [[opensource-project-practices-from-multica|Multica 实践]] 和 [[opensource-project-practices-from-temporal|Temporal 实践]] 形成对比
- 关联 [[openhuman-architecture]]、[[opensource-project-practices-from-multica]]、[[opensource-project-practices-from-temporal]]

## 2026-05-21 create | concepts/multica-technical-highlights.md
- 新增 Multica 项目技术亮点深度总结（源自代码库挖掘）
- 十大工程亮点：多租户架构与工作空间隔离、实时协作的乐观更新机制、Agent 执行环境隔离、WebSocket Hub 的作用域订阅模型、Daemon 的运行时发现与版本追踪、跨平台抽象层 CoreProvider、Monorepo 的 Catalog 依赖管理、Worktree 的数据库隔离、类型安全的 Schema 验证、Desktop 的 Tab 隔离与 Workspace 切换
- 六大工程哲学：隔离优先、实时协作、类型安全、跨平台复用、开发体验、可观测性
- 技术栈总览：Go + Chi + sqlc + WebSocket / React 19 + Next.js + TanStack Query + Zustand / PostgreSQL 17 + pgvector / pnpm + Turborepo + catalog
- 关联 [[multica]]、[[multica-acp-integration]]、[[multica-acp-workflow]]、[[multica-runtime-discovery]]、[[opensource-project-practices-from-multica]]

## 2026-05-22 create | entities/zed-agent-architecture.md
- 新增 Zed 编辑器 Agent 系统架构深度分析（源自 ~/Projects/zed 源码研究）
- 覆盖：8 crate 分层架构（agent/agent_servers/acp_thread/acp_tools/agent_ui/agent_settings/agent_skills/context_server）、ACP JSON-RPC over stdio 协议实现（AcpConnection 连接/会话/流式事件）、NativeAgent 内置 Agent（Thread + LLM 直连）、AgentServer trait 双实现、AgentServerStore 注册中心、AgentConnection 客户端抽象 + 5 个可选能力 trait、17+ 内置工具系统、MCP Context Server 注册链（Extension → Proxy → Store → Registry）、完整数据流、线程持久化
- 关联 [[acp-protocol]]、[[multica-acp-integration]]、[[context-mode]]、[[heuristic-learning]]

## 2026-05-22 create | entities/zed.md
- 新增 Zed 高性能多人协作代码编辑器深度研究（源自 ~/Projects/zed 源码 + Web 调研）
- 覆盖：产品定位（Atom 创始人 Nathan Sobo、Rust 100%、GPU 渲染）、236 crate 模块化架构、GPUI 自研 UI 框架、Agent 系统架构（NativeAgent + ACP 外部 Agent + MCP 工具）、编辑器核心功能（Tree-sitter/LSP/多缓冲区）、AI 功能（Agent 面板/内联补全/Profile/Skill）、协作功能（实时编辑/语音/Channel）、调试器 DAP、扩展系统 WASM、竞品对比（VS Code/Cursor）、历史时间线、局限与争议
- 关联 [[zed-agent-architecture]]、[[acp-protocol]]、[[context-mode]]、[[heuristic-learning]]

## 2026-05-22 create | concepts/zed-documentation-system.md
- 新增 Zed 文档管理体系学习笔记（源自 ~/Projects/zed/docs/ 源码研究）
- 覆盖：文档架构（mdBook + zed-html 自定义渲染器 + docs_preprocessor Rust crate）、8 项品牌声音评分卡（Technical Grounding / Natural Syntax / Conciseness / Voice Consistency / Specificity / Actionability / Honest Framing / Reader Respect，全部≥4 才通过）、写作哲学（实用优先/诚实局限/直接简洁/第二人称/现在时）、禁用词列表（LLM 话术/营销废话）、页面结构模板（7 段标准顺序）、4 种金标范例（simple/complex/configuration/reference）、格式约定（{#kb} 动态键绑定/[settings] JSON 注解/callouts）、术语一致性表、质量检查清单（12 项）、文档范围决策（必须 vs 跳过）、设计亮点（键绑定自动同步/旧链接重定向/PR Release Notes）
- 关联 [[zed]]、[[zed-agent-architecture]]、[[opensource-project-practices-from-openhuman]]、[[heuristic-learning]]

## 2026-05-22 create | concepts/zed-agent-modular-design.md
- 新增 Zed Agent 系统模块化设计深度分析
- 核心问题：为什么需要 8 个 crate？答案：6 个正交关注点（协议/逻辑/UI/工具/配置/调试）自然分离 + Rust 编译模型驱动 + 双路径架构催化依赖倒置
- 十大设计亮点：AgentConnection 单一 trait 统一双路径、前台线程隔离（unbounded channel 解 !Send）、工具统一抽象（AnyAgentTool）、ACP 外部 crate 做开放生态、可选能力 trait（opt-in）、Extension→MCP 注册链（4 层解耦）、Session 持久化（ThreadStore + SQLite）、工具权限审批流、子 Agent 受控编排、ACP 调试面板
- 每个 crate 的存在理由分析 + 模块间依赖图 + "可以更少吗"分析
- 关联 [[zed-agent-architecture]]、[[zed]]、[[acp-protocol]]、[[multica-acp-integration]]

## 2026-05-22 create | entities/kagent.md
- 新增 Kagent — Kubernetes 原生 AI Agent 框架深度研究（源自 ~/Projects/kagent 源码研究）
- 覆盖：项目定位（K8s-native Agent 管理）、四组件架构（Controller/HTTP Server/UI/Engine）、8 个 CRD 资源模型（Agent/ModelConfig/ToolServer/RemoteMCPServer/AgentHarness/SandboxAgent/Memory）、Agent 创建→运行→对话完整数据流、多运行时支持（Python ADK/CrewAI/LangGraph/OpenAI/Go ADK）、Go workspace + Python UV workspace + Next.js 16 UI 技术栈、Helm Charts 部署体系、跨命名空间安全模型（Gateway API 模式）、设计决策与权衡、活跃开发方向（Memory/MCP/OIDC/Podman）、与 Langflow/AutoGen 竞品对比
- 关联 [[adk-python]]、[[a2a-protocol]]、[[superpowers]]、[[context-mode]]、[[heuristic-learning]]

## 2026-05-22 create | comparisons/kubernetes-agent-platforms.md
- 新增 Kubernetes 原生 AI Agent 管理平台竞品对比（Exa 神经搜索 + GitHub 调研）
- 覆盖：5 个直接竞品（Kagenti/Agent Sandbox/AgentField/KAOS/EdgeCore）+ 4 个生态项目（kubectl-ai/KAITO/kmcp/Kubeflow）
- 核心发现：Kagenti (Red Hat) 最直接竞品、Agent Sandbox (k8s-sigs) 可能成为底层标准、AgentField 增速最快
- 功能矩阵对比（CRD/MCP/A2A/多运行时/UI/Helm/Auth/沙箱/记忆）
- 战略分析：kagent 优势（CNCF+协议最广+多运行时）与风险（标准化可能被 k8s-sigs 主导）
- 关联 [[kagent]]、[[adk-python]]、[[a2a-protocol]]、[[superpowers]]、[[context-mode]]

## 2026-05-25 create | entities/orloj.md
- 新增 Orloj — 多 Agent 系统全栈平台深度研究（源自 ~/Projects/orloj 源码）
- 覆盖：产品定位（"Agents are infrastructure"、Kubernetes for AI Agents）、8 层 Agent Stack 架构、核心数据流（声明→协调→调度→认领→执行→治理→观察→扩展）、技术栈（Go 1.26 + Postgres + NATS JetStream + K8s controller-runtime + OTel）、8 个 CRD 资源、18 个 REST API 端点域、A2A 协议互操作、K8s 深度集成（CRD Sync Operator / K8s Agent 执行 / K8s Tool 隔离）、治理审批系统、6 个二进制组件、项目结构、设计决策与权衡、版本历程
- 关联 [[kagent]]、[[a2a-protocol]]、[[temporal]]

## 2026-05-24 create | concepts/yitang-ai-tools-workflow-ama.md
- 新增一堂 AMA 直播学习笔记（飞书 wiki API 提取）
- 于陆解答 160+ 学员 AI 工具×工作流问题，五大方向：工具使用、工作流搭建、场景赋能、个人定位、学习路径
- 重点标注：龙虾/Hermes/Coze/N8N 工具对比、三层架构派兵布阵、Skill 生命周期、人在环方法论
- 来源：https://yitanger.feishu.cn/wiki/S8Z7wLa5eiPwN6kTGTac7kcmned
- 关联 [[ai-design-fundamentals-yitang]]、[[superpowers]]、[[skill-system]]、[[acp-protocol]]

## 2026-05-24 create | concepts/yitang-problem-os.md
- 新增一堂拆书会第203期学习笔记（yitang.top fs-doc 提取，Playwright + Vision OCR）
- 讲师国帅，拆解 ESR《提问的智慧》，提出 Problem OS 五引擎方法论
- 三部分结构：定位（四层能力栈）→ 拆解（五引擎：注意力交易/问题工程化/选对场合/信用管理/可回答性设计）→ 升级（AI时代五引擎对照）
- 来源：https://yitang.top/fs-doc/a7fa61e6332820652098cccd446b270b/LsicdO405oaigzxHR9LcpUIgnOb
- 关联 [[yitang-ai-tools-workflow-ama]]、[[superpowers]]、[[prompt-engineering]]、[[heuristic-learning]]

## 2026-05-25 create | concepts/orloj-documentation-system.md
- 新增 Orloj 文档管理体系深度分析（源自 ~/Projects/orloj/docs/ 源码研究）
- 覆盖：Vocs v1.4.1 文档站框架（基于 Vite）、5 顶级导航 + 50+ 页面、完整侧边栏树（5 层深度 collapsed:false）、文档类型分层（入口/Getting Started/Concepts/Guides/Deploy/Operations/Reference）、Guide 渐进式设计（5min→WASM）、Concept 页面标准模式（定义→原因→原理→Schema→关系→示例）、API 文档策略（OpenAPI 3.1 + Redocly lint + CI 验证）、部署文档与参考配置分离（pages/ vs design/）、5 个设计亮点
- 对比：与 [[zed-documentation-system]]（mdBook+品牌评分卡）和 [[temporal]]（Docusaurus）的文档体系差异
- 关联 [[orloj]]、[[zed-documentation-system]]、[[temporal]]

## 2026-05-25 create | concepts/kagent-documentation-system.md
- 新增 Kagent 文档体系深度分析（源自 ~/Projects/kagent 源码研究）
- 覆盖：6 层文档体系（L0-L5）、L3 架构深度文档 6 篇详解（CRDs/Data Flow/HITL/Prompt Templates/A2A Subagents/Controller Reconciliation）、EP 增强提案（KEP 模式 3 篇）、CLAUDE.md + AI Skills 独特层、GitHub 治理（3 Issue 模板 + 10 CI 工作流）、设计决策分析（7 好做法 + 7 改进建议）
- 核心发现：CLAUDE.md + `.claude/skills/` 是开源项目中首次看到的"AI Agent 原生文档层"；文档"给开发者写的"多于"给用户写的"
- 关联 [[kagent]]、[[zed-documentation-system]]、[[adk-python]]、[[a2a-protocol]]、[[superpowers]]、[[context-mode]]

## 2026-05-26 create | concepts/kagent-agent-harness.md
- 新增 Kagent AgentHarness 概念深度解析（源自 ~/Projects/kagent 源码研究）
- 覆盖：三种 Agent 资源对比表（Agent/AgentHarness/SandboxAgent）、AgentHarness CRD Spec 详解（backend/image/env/network/modelConfigRef/channels）、Controller 协调流程（Finalizer→Backend查找→EnsureAgentHarness→Post-Ready Bootstrap→10s requeue）、OpenShell gRPC 后端交互（CreateSandbox/GetSandbox/DeleteSandbox/ExecSandbox streaming）、与 Agent Sandbox 的关系对比、实际使用场景（开发环境/带 Telegram 的运维环境）
- 核心发现：AgentHarness 不是 Agent 的替代品或前身，而是平行的资源类型——Agent 提供智能，AgentHarness 提供远程执行环境。通过外部后端（OpenClaw/NemoClaw）创建可 SSH/exec 的 VM，不在 K8s 集群内运行任何工作负载
- 关联 [[kagent]]、[[kagent-crd-limitations]]、[[agent-sandbox]]、[[kubernetes-crd]]

## 2026-05-26 create | concepts/kubernetes-crd.md
- 新增 Kubernetes CRD (Custom Resource Definition) 深度技术参考
- 覆盖：核心概念（CRD→CR→Controller 三角）、GVK/GVR 关系、CRD 完整结构（group/scope/names/versions/schema/subresources）、OpenAPI v3 验证 + CEL 跨字段规则 + Validation Ratcheting、Finalizer 终结器、Status 子资源、多版本 Conversion Webhook、AdditionalPrinterColumns、Field Selectors (v1.32+)、Scale 子资源、CRD vs ConfigMap vs Aggregated API 对比、Operator Pattern + Reconcile Loop、Kubebuilder 工具链 + Markers 注解、设计最佳实践（API 设计/版本管理/安全）
- 来源: K8s 官方文档 + Kubebuilder Book
- 关联 [[kagent]]、[[kagent-crd-limitations]]、[[agent-sandbox]]、[[orloj]]、[[kubernetes-agent-platforms]]

## 2026-05-26 create | entities/agent-sandbox.md
- 新增 Agent Sandbox (kubernetes-sigs) 深度研究（源自 K8s 官方博客 + GitHub 源码）
- 覆盖：项目定位（SIG Apps 官方 Agent 运行时基础设施）、Sandbox CRD 详解（podTemplate + PVC + replicas 0/1 + lifecycle）、4 个 CRD（Sandbox/SandboxTemplate/SandboxClaim/SandboxWarmPool）、与 Deployment/StatefulSet 对比、Python SDK 4 种连接模式、核心设计决策（安全隔离/生命周期/稳定身份）、与 kagent 的互补关系（基础设施层 vs 应用层）、kagent 可学的 6 个特性、2026 Roadmap（含 kAgent 集成）
- 核心发现：Agent Sandbox 是 kagent 的互补项目而非竞争者，解决"怎么安全跑 Agent 进程"，kagent 解决"怎么定义 Agent 行为"。Roadmap 明确列出 "Integration with kAgent"
- 关联 [[kagent]]、[[kagent-crd-limitations]]、[[kubernetes-agent-platforms]]、[[a2a-protocol]]、[[orloj]]

## 2026-05-26 create | concepts/kagent-crd-limitations.md
- 新增 Kagent CRD 能力边界深度分析（源自 ~/Projects/kagent 源码研究）
- 覆盖：CRD 覆盖度评估（8 Provider / Agent 配置 / 部署控制）、框架级能力裁剪（OpenAI handoff/CrewAI 协作/LangGraph 状态图全部丢失）、工具类型限制（只有 MCP + Agent）、数量硬限制（20 tools）、翻译层信息损失（5 类字段被忽略/简化）、BYO 逃生舱口分析、设计权衡（有意 vs 疏忽）、5 项演进方向
- 核心结论：CRD 确实阉割了框架能力，但这是有意的架构权衡（统一抽象层 + 声明式运维 + 协议标准化）。最关键差距是缺少多 Agent 编排的 CRD 表达
- 关联 [[kagent]]、[[kagent-documentation-system]]、[[adk-python]]、[[a2a-protocol]]、[[orloj]]

## 2026-05-26 create | entities/swarmclaw.md
- 新增 SwarmClaw 项目深度研究（源自 ~/Projects/swarmclaw/ 源码分析）
- 覆盖：技术栈（Next.js standalone + Electron + better-sqlite3）、Chat 执行管线四层处理（去重/合并/抢占/锁）、Provider 注册表（23+ LLM，OpenAI 兼容封装模式）、12+ Connector 连接器体系、Agent 编排三层模型（委派/蜂群/子代理）、Mission 自主目标驱动运行（四维预算强制）、终端工具边界（memory_write/durable_wait/context_compaction）、关键设计决策（hmrSingleton/setIfChanged/saveCollection 守卫/balanced-brace walker）、6 种部署模式、UX 哲学（渐进式披露/智能默认值）
- 关联 [[openhuman-architecture]]、[[multica]]、[[a2a-protocol]]、[[ruflo]]、[[acp-protocol]]

## 2026-05-27 create | entities/openshell.md
- 新增 OpenShell — NVIDIA 开源 AI Agent 安全沙箱平台深度研究（源自 ~/Projects/OpenShell 源码研究）
- 覆盖：整体架构（CLI + Gateway 控制平面 + Supervisor 数据平面）、16 crate Rust workspace（~166K LOC）、5 层隔离（Landlock + seccomp + namespace + OPA 策略代理 + 进程降权）、4 计算驱动（Docker/Podman/K8s/libkrun microVM）、Z3 SMT 策略形式化验证、OCSF v1.7.0 结构化安全日志（7 种事件类型）、Protobuf 对象存储（SQLite/Postgres）、gRPC + HTTP 协议、Helm/K8s 部署、Agent-First 开发流程（16 个技能）、26 个 CI workflow、设计权衡 7 项
- 关联 [[kagent]]、[[agent-sandbox]]、[[a2a-protocol]]、[[kubernetes-crd]]、[[agentic-rag]]、[[context-mode]]、[[temporal]]

## 2026-05-29 create | entities/ecc.md
- 新增 ECC (Everything Claude Code) 项目研究（源自 https://github.com/affaan-m/ECC）
- 覆盖：197K⭐ 跨 harness AI 代理优化系统，63 agents + 249 skills + 79 commands，支持 Claude Code/Codex/Cursor/OpenCode/Gemini/Zed/GitHub Copilot；12+ 语言生态（TS/Python/Go/Java/Rust/C++/Kotlin/Swift/Perl/PHP）；分层架构（agents → skills → hooks → rules → MCP configs）；版本演进 v1.2→v2.0.0-rc.1；Rust 控制平面原型 ecc2/；商业化路径（ECC Tools Pro/Enterprise）；核心贡献者 affaan-m（1423 commits）
- 关联 [[gstack]]、[[ruflo]]、[[kagent]]、[[swarmclaw]]、[[codegraph]]

## 2026-05-29 move | concepts/superpowers.md → entities/superpowers.md
- 将 superpowers 从 concepts/ 移至 entities/（具体项目，非抽象概念）
- 更新 frontmatter type: concept → entity
- 更新 index.md 条目位置
- 关联 [[ecc]]、[[codegraph]]、[[context-mode]]

## 2026-05-29 create | concepts/claude-code-workflow.md
- 新增 Claude Code Workflow 概念研究（源自多源综合研究）
- 覆盖：确定性多 agent 编排引擎定位、JS 脚本语法（export const meta + phase/pipeline/parallel/agent）、五大编排模式（对抗性验证/评审团/循环收敛/多模态扫描/完整性批评）、Pipeline vs Parallel 选择原则、agent() 选项与约束限制、调用方式（内联/命名/脚本文件）、实际案例（Boris Cherny 5并行会话/Mae Capozzi 6阶段编排器/Steve Yegge Gas Town 20-30并行）、AI编码8阶段成熟度模型、Cache与成本优化策略
- 关联 [[ecc]]、[[codegraph]]、[[context-mode]]、[[a2a-protocol]]、[[acp-protocol]]、[[agentic-rag]]

## 2026-05-31
- **yitang-huazong-ama-cost-ai-landing.md** — 花总AMA商业突破大航海学习笔记（concepts/）。来源：飞书Wiki API提取→整理。关联：[[yitang-ai-tools-workflow-ama]]、[[oscar-research-methodology]]

- **yitang-ai-data-first-lesson.md** — 一堂AI数据第一课（Live251）学习笔记（concepts/）。来源：yitang.top Playwright截图+Vision OCR→整理。核心：ADAPTED 6+1模型。关联：[[yitang-huazong-ama-cost-ai-landing]]、[[yitang-ai-tools-workflow-ama]]

## 2026-06-01
- **archon.md** — Archon 开源 AI 编码确定性编排平台深度研究（entities/）。来源：~/Projects/Archon 源码分析（CLAUDE.md + 包结构 + 接口定义 + 数据库 schema + 变更日志）。覆盖：11 包 monorepo 依赖图、4 个核心接口（IAgentProvider/IPlatformAdapter/IWorkflowStore/IIsolationStore）、DAG 工作流引擎（6 种节点类型）、11 张数据库表、5 个平台适配器、3 个 AI Provider（Claude/Codex/Pi）、Git Worktree 原生隔离、设计哲学（KISS/YAGNI/Fail Fast）。v0.4.1，~157K 行 TypeScript，MIT 协议。
- 关联 [[claude-code-workflow]]、[[temporal]]、[[codegraph]]、[[slack]]、[[kagent]]

- **chatdev.md** — ChatDev 2.0 (DevAll) 零代码多 Agent 编排平台深度研究（entities/）。来源：~/Projects/ChatDev 源码研究（README + 目录结构 + 核心模块 + YAML 工作流 + 依赖配置）。覆盖：v1.0→v2.0 演进（虚拟软件公司→零代码平台）、7 层架构（Vue Console → FastAPI → Graph Engine → Node Executor → Agent Capabilities → Edge Layer → Config）、10 步数据流、7 种 Node Executor（agent/python/literal/subgraph/human/loop/passthrough）、3 种执行策略（DAG/Cycle/MajorityVote）、45+ 预置 YAML 工作流、分层记忆系统（4 后端）、MCP 工具集成、与 [[archon]]/[[agno]]/[[ruflo]] 横向对比、6 项设计权衡。Python 3.12 + FastAPI + Vue 3，清华 OpenBMB 团队，Apache-2.0。
- 关联 [[archon]]、[[claude-code-workflow]]、[[temporal]]、[[agno]]、[[ruflo]]、[[kagent]]、[[heuristic-learning]]

| 2026-06-02 | ai-workflow-landscape + 19 entities | AI Workflow 开源项目全景调研：20 项目四类对比，新增 langchain/llama-index/crew-ai/auto-gen/dify/flowise/langflow/n8n/fast-gpt/apache-airflow/prefect/dagster/kestra/argo-workflows/kubeflow/mlflow/metaflow/flyte/zenml | [[ai-workflow-landscape]] |
## 2026-06-03 10:46 — AI Workflow 实体扩展

- **操作**: 将 19 个 AI Workflow 实体从浅层摘要扩展为详细文档
- **文件**: entities/langchain.md, llama-index.md, crew-ai.md, auto-gen.md, dify.md, flowise.md, langflow.md, n8n.md, fast-gpt.md, apache-airflow.md, prefect.md, dagster.md, kestra.md, argo-workflows.md, kubeflow.md, mlflow.md, metaflow.md, flyte.md, zenml.md
- **详细度**: 平均 285 行 / 9KB，含架构图、核心表、代码结构、设计决策、开发命令、竞品对比
- **wikilinks**: 每个实体至少 4 个出链
- **总内容**: 168.6 KB

## 2026-06-03 10:55 — AI Workflow 深度对比分析

- **操作**: 创建深度对比分析文章
- **文件**: comparisons/ai-workflow-deep-comparison.md
- **内容**: 20 个 AI Workflow 开源项目的架构哲学、设计权衡与选型逻辑
- **结构**: 四层架构栈 → 三个根本分歧 → 六大核心维度 → 五组竞品对比 → 三种组合架构 → 趋势判断 → 选型决策树 → 综合评分矩阵
- **长度**: ~30KB，~750 行
- **关联**: [[ai-workflow-landscape]]（全景速查版）

## 2026-06-03 11:30 — Langfuse 实体创建

- **操作**: 创建 Langfuse 实体文件
- **文件**: entities/langfuse.md
- **内容**: 开源 LLM 工程平台深度分析（Tracing、Prompt 管理、评估系统、数据集、50+集成、部署方式、LangSmith 竞品对比）
- **长度**: ~470 行，16KB
- **关联**: [[langchain]], [[llama-index]], [[mlflow]], [[dify]]

## 2026-06-07 — 一堂课程学习（第5-6节）

- **kecheng-to-ai-tool.md** — 半肥猫「把课程变成AI工具」学习笔记（concepts/）。来源：飞书Wiki API提取。五步闭环+9阶段SOP。关联：[[oscar-research-methodology]]
- **content-growth-loop.md** — 半肥猫「内容增长闭环」学习笔记（concepts/）。来源：飞书Wiki API提取。五步思考模型。关联：[[kecheng-to-ai-tool]]
- **geo-brand-foundation.md** — 堃堃「GEO品牌地基搭建」学习笔记（concepts/）。来源：飞书Wiki API提取。七步框架+FAQ/Schema。关联：[[content-growth-loop]]
- **experience-extraction-agent.md** — Noah「Coco经验萃取Agent」学习笔记（concepts/）。来源：飞书Wiki API提取。六步萃取+三层翻译+五类异常。关联：[[geo-brand-foundation]]
- **ai-short-drama-workflow.md** — 李守彬「AI短剧/漫剧工作流封装工具市场分析」学习笔记（concepts/）。来源：飞书Wiki API提取。三类场景盘点+真/伪空白判断+端到端AI导演智能体。关联：[[kecheng-to-ai-tool]]、[[oscar-research-methodology]]
- **stripe-hosted-checkout.md** — Stripe Hosted Checkout 深度研究（entities/）。来源：Web调研。独立开发者最佳支付方案。关联：[[tanzhen]]

## 2026-06-03 18:00 — CC Workflow Studio 实体创建

- **操作**: 创建 CC Workflow Studio 实体文件
- **文件**: entities/cc-wf-studio.md
- **内容**: AI Agent 工作流可视化编辑器深度研究（源自 ~/Projects/cc-wf-studio 源码 + CodeGraph 索引 + README + CLAUDE.md）
- **覆盖**: pnpm monorepo 4 包架构（core/CLI/MCP/VSCode extension）、13 种 WorkflowNode 类型、Workflow 数据模型（schemaVersion 1.0–1.2）、React Flow 可视化画布 + Edit/Overview 双模式、8 种 AI 编码 Agent 导出格式（Claude Code/Copilot/Codex/Gemini/Cursor/Roo/Antigravity）、6 个 MCP 工具（get_workflow/apply_workflow/list_agents 等）、Slack 集成（OAuth + 深链接导入）、技术栈（TypeScript 5.3 + React 18.2 + Zustand + Radix UI + Vite）、3 条数据流（Save/AI Edit/Export）、7 项设计决策、与 [[n8n]]/[[langflow]]/[[ruflo]] 横向对比
- **代码规模**: 47,700 LoC / 302 文件 / 3,699 节点 / 9,604 边
- **许可**: AGPL-3.0（扩展）+ MIT（库）
- **关联**: [[claude-code-workflow]], [[ecc]], [[ruflo]], [[n8n]], [[langflow]], [[context-mode]]

## 2026-07-06 update | concepts/langflow-architecture.md

- **操作**: 更新 Langflow 架构分析，补充 2026-07 源码演进（非新建，避免重复）
- **文件**: concepts/langflow-architecture.md（updated 2026-05-15 → 2026-07-06）
- **新增内容**: 新增第 0 节"架构演进"，记录 7 大变化——
  1. **内核外化**：`lfx` 成为真正的执行内核，`backend/base/langflow/graph/` 退化为 re-export shim（全文引用）
  2. **服务工厂反射 DI**：`ServiceFactory` 用 `get_type_hints(create)` 自动推断依赖，签名即配置
  3. **三通道可插拔注册**：配置文件 > 装饰器 > entry points，优先级与场景表
  4. **RBAC 四阶段**：`BaseAuthorizationService` 抽象 + 四元组请求模型 + Phase 3 share-aware fetch（`supports_cross_user_fetch` 分支 + `deny_to_404`）+ Phase 4 审计 API + foundations 迁移种子三角色
  5. **数据驱动图调度**：`RunnableVerticesManager` 四集合动态推进，支持 cycle/分支/续跑，非静态 DAG
  6. **多执行后端**：v2 Workflow API（sync/stream/background）+ langflow-stepflow（JSON→YAML 翻译）
  7. **SDK 与 Bundle**：`langflow_sdk` 同步/异步 HTTP 客户端 + `bundles/` 重依赖拆包
- **技术债记录**: `deps.py` get_service 懒注册 workaround、FastAPI `eval_str=True` 强制 import 外置
- **关联**: [[opensource-project-practices-from-langflow]]、[[opensource-project-practices-from-temporal]]、[[ai-workflow-landscape]]、[[langflow]]

## 2026-07-06 03:15 — LobeChat 多智能体协作架构概念创建

- **操作**: 创建 LobeChat 多智能体协作架构概念文件
- **文件**: concepts/lobechat-multi-agent-architecture.md
- **内容**: LobeChat 多智能体协作深度分析（源自 /home/rowan/Projects/lobehub 本地源码 + CodeGraph + context-mode 批量探索）
- **覆盖**: 三层 Plan→Execute 循环（单 Agent / 多 Agent 自相似）、GroupOrchestrationRuntime 三角色架构（Supervisor 状态机 + Executor + Runtime）、确定性状态机决策逻辑（init→call_supervisor→speak/broadcast/delegate/execute_task/finish）、工具即协作触发器（stop:true + afterCompletion 回调解耦）、三种执行后端（client/gateway/hetero 统一抽象 + selectRuntimeType 集中路由）、异构执行器（Claude Code/Codex CLI + 6 种 auth 失败识别 + device/sandbox/local 目标）、三种用户入口（callSubAgent/callAgent/@agent 统一 AgentInvocationIntent）、前端协作 UI（AssistantGroup/AgentTasks/metadata.isSupervisor）、可观测性栈（tracing/signal/audit/subagentMetrics）、tagged union 类型驱动、与 CrewAI/AutoGen/LangGraph 横向对比
- **关键洞察**: LLM 不确定性隔离在工具调用层，编排逻辑确定性可测；Group Orchestration 把 Agent 当 Executor 复用而非另造体系
- **长度**: ~12KB，~280 行
- **关联**: [[lobechat-architecture]], [[lobechat-highlights]], [[opensource-practices-from-lobechat]], [[e2e-practices-from-lobechat]], [[crew-ai]], [[auto-gen]], [[langchain]], [[claude-code-workflow]], [[acp-protocol]], [[a2a-protocol]]

## 2026-07-07 — Flowise 技术架构深度调研

- **操作**: 创建 Flowise 技术架构概念页 + 更新 Flowise 实体页
- **文件**:
  - 新建 `concepts/flowise-architecture.md`（~24KB，~530 行）
  - 更新 `entities/flowise.md`（修正过时信息：多租户/部署/对比表，加交叉链接）
  - 更新 `index.md`（新增条目，页数 116→117，日期更新）
- **数据源**: `~/Projects/Flowise`（v3.1.3，commit bb773ffa，2026-07 拉取）一手源码
- **覆盖**: monorepo 六包组织（pnpm+turbo）、278 节点 / 25 类的文件系统动态注册机制（`module.exports={nodeClass}`，零装饰器）、INode 契约（inputs/init/run + baseClasses 类型系统 + loadMethods 异步选项）、**自研 BFS 图解释器**（constructGraphs 邻接表 + buildFlow 逐节点 require+init+resolveVariables，与 Langflow 编译型 Runnable 的关键分野）、executeFlow 五步流水线、buildAgentGraph（LangGraph 式 sequential agents）、TypeORM 四库 + 23 实体、enterprise 子模块多租户（Org/Workspace/RBAC/SSO）、BullMQ 三队列 + Web/Worker 分离 + Redis pub/sub SSE 中继、OpenTelemetry + Arize/Phoenix/Opik 可观测、MCP 双向（server+client）、Agent 编排三层演进、agentflow/observe 可嵌入 SDK 包、与 Langflow/Dify 六维对比表、11 条可借鉴工程实践
- **关键洞察**:
  1. Flowise 不编译图成单个 Runnable，而是**逐节点 init() 实例化 + 终点 run() 触发执行**——换来自中断/逐节点观测/Loop/Condition 控制流能力
  2. 节点注册靠**文件系统递归扫描 + 动态 require**，加节点零改框架，撑起 278 内置 + Marketplace 社区节点
  3. baseClasses 字符串数组即画布类型系统，判连线合法性
  4. 企业能力独立成包，开源核心保持单租户简单
- **修正**: entities/flowise.md 原写「无多租户」「单进程不依赖 Redis」「生产级功能较少」——v3.1.3 实际已有企业多租户、BullMQ 可选队列、MCP/Agent/评估等生产级能力，已更新
- **关联**: [[flowise]], [[langflow-architecture]], [[langflow]], [[dify]], [[langchain]], [[lobechat-architecture]], [[ai-workflow-landscape]]

## 2026-07-11 — 一堂落地之夜第255场（C×D 实战循环）

- **yitang-cd-loop.md** — 一堂「落地之夜第六场」学习笔记（concepts/）。来源：yitang.top fs-doc Playwright 抓取 + 累积式正文提取（解决飞书文档虚拟化导致正文不全）。核心：业务公式(C)找战场 × 转化率(D)打节点的循环方法论（D打不动→退回C重找参数→回D打穿），配三个操盘手复盘——叶文彬·射箭馆（四关模型16字口诀/回流礼品卡/七环裂变乘法/科学型组织四步）、董原·少儿舞蹈学校（续班率从「相关当因果」的坑→业务公式拆出新生×新老师分层参数）、谢泽丰·服装店（线下数人头建数据闭环→创新参数「二次试穿」转化率11%→18%→Magic Number音量80→假设驱动管理）。含可迁移 Checklist 与 YAI 两个教练工具。
- **raw/yitang/落地之夜第255场-原文整理.md** — 抓取到的干净全文（约 5.8 万字，176KB）。
- 关联 [[yitang-business-formula]]、[[yitang-dual-triangle]]、[[yitang-ai-data-first-lesson]]、[[raw/yitang/落地之夜第255场-原文整理]]

---

## 远程历史条目（origin/main）

## 2026-06-14 create | concepts/skill-self-evolution.md
- **操作**: 创建 Skill 自进化闭环概念页
- **文件**: concepts/skill-self-evolution.md
- **内容**: darwin-skill × skill-evolver × EmbodiSkill 三件套互优化方法论，4轮迭代实验数据，达尔文进化论类比，Hermes Agent 实践指南
- **来源**: KK大叔「大叔笔记」公众号文章
- **关键论文**: SkillEvolver (arXiv:2605.10500)、SkillLens (arXiv:2605.23899)、EmbodiSkill (arXiv:2605.10332)
- **安装**: 三个 skill 已安装到 ~/.hermes/skills/
- **关联**: [[heuristic-learning]], [[agent-world]], [[humanizer-skill]]

---

## 2026-06-14 · yitang-advanced-modeling
- **操作**: 创建一堂高阶建模第一课概念页
- **文件**: concepts/yitang-advanced-modeling.md
- **内容**: Live253 Truman主讲，三阶建模体系（流程建模60分→抽象建模75分→本质提炼85分），千人广场模型，六步建模工作流，知识萃取可靠度四层，十年爬山地图L1-L6段位，AI辅助建模5步法
- **来源**: [yitang.top 飞书文档](https://yitang.top/fs-doc/e74e650889247b8c40bfdc91b20fb13d/JbGbdA4fFoEuEMxP8aecnUZGnfE)
- **关联**: [[oscar-research-methodology]], [[skill-self-evolution]], [[experience-extraction-agent]], [[yitang-ai-data-first-lesson]]

---

## 2026-06-15 · yitang-business-formula
- **操作**: 创建一堂业务公式拆解概念页
- **文件**: concepts/yitang-business-formula.md
- **内容**: 孔源主讲，业务公式三个条件（看得清/想得透/做得准）、四个认知突破（不细分/不考虑数字/逻辑混乱/没数据埋点）、参数冰山L1-L6（科目→抓手→本质洞察）、三个核心技巧（先切分+再转化 / + vs×运算符号 / 相关≠因果）、单次成交型vs持续复购型业务分类、定性参数→可定量行为指标拆解模板
- **来源**: [飞书Wiki](https://yitanger.feishu.cn/wiki/BZgNw23zQiiYzxkxOCxceLxLndg)
- **关联**: [[yitang-advanced-modeling]], [[roi-decision-framework]]

---

## 2026-07-04 · leaferjs
- **操作**: 创建 LeaferJS entity 页
- **文件**: entities/leaferjs.md
- **内容**: 国产开源 Canvas 2D 渲染引擎 + UI 框架（1.0 于 2024 发布），核心特性（场景树/分层渲染/脏矩形 partRender/虚拟化/内置交互编辑器/跨平台/TS 原生），核心包对比（leafer 全量 / leafer-ui 核心 70KB / leafer-draw 仅绘图），关键概念（Leafer 单画布 / App 应用管理 / @leafer-in/* 插件），快速上手（npm + 最小可拖拽示例），与 PixiJS/Konva/Fabric 横向选型对比，学习路径
- **来源**: [官网](https://www.leaferjs.com/), [GitHub](https://github.com/leaferjs/leafer-ui), [1.0 发布](https://juejin.cn/post/7389651690306355241), [局部渲染解析](https://juejin.cn/post/7256386855721074747)
- **关联**: [[design-as-code]], [[design-md-spec]], [[awesome-design-md]]

---

## 2026-07-04 · openmontage
- **操作**: 创建 OpenMontage entity 页
- **文件**: entities/openmontage.md
- **内容**: 世界首个开源 Agentic 视频生产系统（calesthio/OpenMontage，AGPL-3.0，32k+ stars，2026-03 创建）。核心理念「Agent-First 无代码编排器，AI 编程助手即编排器」；12 条流水线（research→proposal→script→scene_plan→assets→edit→compose）；三层知识架构（tools/pipeline_defs "存在什么" + skills "怎么用" + .agents/skills "原理是啥"）；Backlot 活故事板（真实审批闸门 + 回放）；质量门禁（Delivery Promise / 预合成校验 / 渲染后自审 / 7 维 scored selector / 预算治理）；Provider 生态（视频 14 家 + 图片 10 家 + TTS 4 家 + 音乐 + Remotion/HyperFrames 合成），零 Key 也能出真视频（Piper + 免费素材 + CLIP 检索纪录片）；与 Agent Skill 范式关系
- **来源**: [GitHub](https://github.com/calesthio/OpenMontage), [AGENT_GUIDE](https://github.com/calesthio/OpenMontage/blob/main/AGENT_GUIDE.md), [ARCHITECTURE](https://github.com/calesthio/OpenMontage/blob/main/docs/ARCHITECTURE.md)
- **关联**: [[leaferjs]], [[design-as-code]], [[awesome-design-md]]

---

## 2026-07-04 · ai-job-search
- **操作**: 创建 ai-job-search entity 页
- **文件**: entities/ai-job-search.md
- **内容**: MadsLorentzen/ai-job-search（3.4k Star，TypeScript + Claude Code + LaTeX + Bun），把求职编码成 /setup → /scrape → /apply 命令流水线。/apply 7 步：解析→匹配评估→LaTeX 起草→独立审阅→修改→编译+视觉检查→呈现。三大差异化：① PDF 视觉验证循环（编译→Claude 读渲染页→改 LaTeX→重编译，循环到完美）② 起草-审阅双代理（独立审阅无思维惯性，草稿内联传递省 token）③ 相关性加权简历删减（相关性×独特性×求职信支撑三维度评分）。其他命令 /expand（扫 GitHub/Kaggle 补画像）/upskill（技能差距热力图+学习计划）/reset。作为 Agent Skill 范式与 OpenMontage 个人 vs 生产场景对偶
- **来源**: [GitHub](https://github.com/MadsLorentzen/ai-job-search), [微信公众号](https://mp.weixin.qq.com/s/9PZeMQpvdIJn6XOU-nnFjA)
- **关联**: [[openmontage]], [[leaferjs]], [[design-as-code]]

---

## 2026-07-04 · yitang-dual-triangle
- **操作**: 创建一堂双三角 concept 页 + 原始学习笔记
- **文件**: concepts/yitang-dual-triangle.md, raw/yitang/一堂双三角-学习笔记.md
- **内容**: 一堂Live254《重新理解AI双三角》。时隔八年第二次公司级背书（上一次 2018 创业五步法）。五步推导：人类三角（审美/体系/创造力）× AI三角（场景/数据/基本功）→ 整合成双三角 → 飞轮 → AI原生本质。关键论断"AI原生是结果不是因，双三角才是科学内核"（类比"年入千万是结果，五步法才是因"）。三阶六变落地场景：X光（拆解）/心法（口喷）/画布（筹备）/拼图（分工）/地图（训练）/底牌（战略）。十年爬山地图 L1-L5。Before/After 心态转变（AI PPT 案例：试遍 Gamma/SlideV/NotebookLM 都放弃 → 自建 Hermes + Feishu2Slide，3 人 + 10 Agent 跑 1000 页）。Feature 思维 vs Skill 思维预告。一堂版 FDE 设想。抓取方式：复用 browser-data Cookie + Playwright 全量截图（66 张）+ macOS Vision OCR（65780 字）
- **来源**: [直播Live第254场](https://yitang.top/fs-doc/5aa0fe3427204946260cd88f38ed2bf7/NJbRdK0gfo6MQhx3uKjcZYchn9g)
- **关联**: [[yitang-advanced-modeling]], [[roi-decision-framework]], [[yitang-ai-data-first-lesson]]
