---
title: "用 Codex 做 PPT（方振义）"
created: 2026-07-12
updated: 2026-07-12
type: concept
tags: [yitang, codex, ai-ppt, html-ppt, prompt-engineering, method]
sources: ["https://yitanger.feishu.cn/wiki/IIInwS7DYiMkwXkuBP0cr0QAn8g?from=from_copylink"]
confidence: high
---

# 用 Codex 做 PPT（方振义）

> 一堂专家分享（Lester / 方振义）。核心命题：把「做 PPT 初稿」从手工排版，变成一条**可被拆解、批量执行、集中验收、持续沉淀**的流程。两条路线（HTML / Image）不是谁取代谁，而是解决不同问题。

## 一、两条路线：HTML 版 vs Image 版

| 维度 | HTML 版 PPT | Image 版 PPT |
|---|---|---|
| 本质 | 内容/文字/布局/交互写在网页里，是一份可调试的中间稿 | 每一页主要由 GPT Image 生成，像一张设计海报 |
| 优势 | 可修改、可验证、可继续迭代 | 把构图/材质/配图/画面气质一次性压进一张图 |
| 适用 | 快速修改、现场演示、强视觉表达、内部迭代 | 发布、传播、需要完整画面感的场景 |
| 工具 | `guizang-ppt-skill`（支持 Claude Code / Codex / Cursor） | GPT Image 2 + Codex 内置 Image Gen Skill + Product Design 插件 |

核心判断：**HTML 像一个可以调试的工程，Image 像一张设计的海报**。先做 HTML 初稿快速验证内容，再用 Image 路线做最终传播版。

## 二、HTML 版 PPT：八步工作流

1. **安装 guizang-ppt-skill**：全局级或项目级 Skill（来源 https://github.com/op7418/guizang-ppt-skill）。Codex 提示安装 Skill 需要重启。
   验证：`$ Skill 名称` 或 `@Skill 名称` 列出；或到 Codex 技能面板确认。
2. **让 AI 读取项目资料**：把素材放进同一目录，在 Codex 指定该目录。先让 AI 看文件夹、讲清用哪些文件、作限制要求，**不要一开始就凭空设计**。
   - 边界提示词：「请不要编造没有提供的数据与内容」。
   - 两种视觉方向：电子杂志风（叙事/观点/个人风格）、瑞士国际主义（事实/产品/分析/方法论）。本课选瑞士国际主义。
3. **生成大纲 & 调试**：先出大纲第一版减少后面大改。建议开启**计划模式** + 高/超高推理。
   - 提示词：根据目录生成 10 页大纲，采用 Guizang PPT Skill。
4. **查看 HTML 初版**：产出 `index.html`（最核心）+ `assets/`（JS/CSS，未必每次生成）。用 Codex 内建浏览器或 Chrome/Edge 打开。
   - 检查：主题一致性、顺序合理、排版可接受、文字无缺漏、无不应出现信息、数据截图均来自参考资料。
5. **备份与风格变更**：先备份 `index.html` & `assets`（生成会覆盖）。换风格用提示词追加限制「不要覆盖现有资料」。
   - 推荐风格（来自 Skill）：电子杂志 × 电子墨水 + 靛蓝瓷 等。
6. **逐页修改：截图 + 注释辅助**：Codex 提供「注释」和「截图」两种反馈。
   - 修改铁律：不能只说「这页不好看」。要写清**页码 / 问题 / 期望 / 必须保留 / 允许调整 / 不能影响的页面**，成功率才高。
   - 注释步骤：点注释 icon → 调整 → 回车变「发送」→ 发送（同页可多批注）。
   - 截图步骤：点截图 icon（存剪贴板）→ Command/Ctrl+V 贴上 → 针对修改。
7. **导出 PDF / PPT**：确定无误后转 PDF（发布）或 PPT。内部可接受 HTML 则跳过。
   - 提示词要点：指定文件名、严格 16:9 横版、完整保留比例不裁切不拉伸、内容超出则等比例缩放适配。
8. **沉淀经验：项目级 AGENTS.md**：若流程会复用，把观察沉淀到**当前项目目录**的 AGENTS.md（非全局）。
   - 只更新项目级；不写全局 AGENTS.md（否则每次指令都参考，耗 Token）。
   - 内容：适用场景、操作步骤、格式要求、常见问题、避坑、下次规则。需持续迭代。

### 非覆盖式生成（关键约定）
- 新版本用新文件名：`index.html` → `index-editorial-indigo.html` → `.pdf`。不覆盖原文件。
- 临时脚本任务后删除（单一明确路径，不用通配符/递归）。
- 不引入源材料之外的数据/案例/价格/版本；可压缩标题、重组结构、统一术语，但不得增加新事实。
- 不改动原始 Word；追溯时在每页 HTML 前加隐藏来源注释 `<!-- Source: 文件名.docx -->`。

### 浏览器验收清单
- **静态检查**：`<section class="slide">` 数量 = 目标页数；来源注释与 1–2 页映射正确；占位符（`[必填]`/`SLIDES_HERE`）为零；本地 `assets/motion.min.js` 存在；主题变量与预设一致；原文件哈希不变。
- **视觉检查**：至少查 1920×1080 与 1366×768，逐页看文字/元素是否溢出（低高度屏最易暴露）。
- **交互检查**：左右方向键翻页、滚轮/触屏、ESC 索引、B 静态模式、Pipeline 页逐步点亮、控制台零错误。

## 三、Image 版 PPT：六步工作流

1. **项目目录**：把原稿/图片/logo/参考图/规则/输出全放进一个文件夹（建议 `素材/` `视觉素材/` `需求/` `模板/` `风格样板图/` `输出图片/` `输出 PPT/` `.agents/skills`）。顺序可用 `01_` `02_` 前缀。
2. **让 Codex 盘点资料**：生成 `asset_inventory.md`（素材盘点 + 10 页映射 + 待补充清单）。限制：不使用 guizang-ppt-skill、不生成图片、不改原文件、不编造。
3. **Product Design 做风格设计**：
   - Step1 ASCII 内容线框 `ascii_content_layout.md`（先定文字排版位置）。
   - Step2 风格设计：让 Product Design 出 3 套方案 + 风格样板图。
   - Step3 生成 `visual_style_guide.md` 视觉风格文件。
4. **Image Gen 生成图片**：Codex 调用 Image Gen 生图；真实截图（UI/配置/价格）优先用源文档裁切脱敏，不让模型重画可读文字。
5. **批量生成 Image PPT**：用 ChatGPT / Codex 批量生图提示词。
6. **逐页修改**：截图 + 批注迭代。

### Image Gen 统一约束
- 16:9 横版、主体不贴边、留安全区。
- 不在生成图里要求可读中文/代码/价格/平台按钮/产品 UI。
- 不生成品牌 Logo、不伪造 Claude Code/阿里云/飞书/OpenClaw/ClawHub 界面。
- 概念主视觉「无文字」，标题/中文/文件名/代码由 PPT 后期叠加。
- 价格/优惠/版本/数量统一标「待人工核验」。

## 四、映射一堂双三角

| 三角 | 维度 | 在 Codex 做 PPT 中的体现 |
|---|---|---|
| 人类三角 | 审美 | 你知道什么叫清楚、好看、能代表你 |
| 人类三角 | 体系 | 附件映射、提示词、Skill、版本、QA |
| 人类三角 | 创造力 | 同一份内容可选 HTML / Image / 混合 |
| AI三角 | 场景 | 你知道何时该用 HTML、何时该用 Image |
| AI三角 | 数据 | 素材盘点、1–2 页映射、来源注释 |
| AI三角 | 基本功 | guizang-ppt-skill、Image Gen、Product Design、Presentations 插件 |

## 五、核心洞察与可迁移 Checklist

- **路线选择**：HTML = 可调试工程（快速验证/迭代）；Image = 设计海报（传播/画面感）。先 HTML 后 Image。
- **把判断变流程**：让 Codex 把「资料读取→页面规划→提示词组织→批量生图→版本管理→导出交付」标准化，而不是让 AI 一次替你做完所有判断。
- **非覆盖式 + 来源注释**：永远新文件名、保留原文件哈希、隐藏来源注释——保证可回溯、可追责。
- **项目级 AGENTS.md 沉淀**：复用型流程写成项目级规则，持续迭代，AI 越来越懂你的风格。
- **验收靠真浏览器**：不能只看源码；静态/视觉/交互三类检查缺一不可。

## 六、工具与资源

- `guizang-ppt-skill`：https://github.com/op7418/guizang-ppt-skill（Claude Code / Codex / Cursor）
- Codex（OpenAI）、GPT Image 2、Codex 内置 Image Gen Skill、Product Design 插件、Presentations 插件
- 回放：https://air.yitang.top/live/2riXCGpyF1

---

关联：
- [[yitang-dual-triangle]] — 本课结尾明确用双三角解释「审美/体系/创造力 × 场景/数据/基本功」
- [[kecheng-to-ai-tool]] — 半肥猫：把课程方法论沉淀成 AI 工具/Skill 的同构思路
- [[skill-architect-methodology]] — 贾老师：Skill 是可执行程序、每条原则必须有反例（guizang-ppt-skill 即此类 Skill）
- [[diary-to-book-skill]] — 姬恒：「规则变中断点」——本课「项目级 AGENTS.md 把经验编译成流程」同一洞察
- [[raw/yitang/codex-ai-ppt-fangzhenyi-原文整理|全文原文]]
