---
title: AI 算法刷题教练竞品调研
created: 2026-05-10
updated: 2026-05-10
type: comparison
tags: [competitive-analysis, leetcode, ai-tutor, coding-interview, education]
sources: [https://readmake.com/]
confidence: medium
---

# AI 算法刷题教练 — 竞品调研

> 调研目标：评估"AI 刷题教练"方向的竞争格局，找到差异化空间

## 一、竞品全景

### Tier 1：直接竞品（AI 辅助算法学习）

| 产品 | 定位 | AI 能力 | 定价 | 特色 |
|------|------|---------|------|------|
| **LeetCode 官方** | 刷题平台鼻祖 | AI 讨论区 + 2025年推出 LeetCode AI（解题助手） | Premium $35/月 或 $159/年 | 最大题库（3000+题）、最大用户群、企业合作 |
| **CodeSignal** | 在线编程评估 + 学习 | AI 驱动的自适应学习路径 | 免费 + 企业版 | 被很多公司用作面试工具，学习端较弱 |
| **Design Gurus** | 面试课程平台 | 无原生 AI，视频课程为主 | Grokking Coding $197（一次性） | "模式识别"教学法，按 24 个算法模式分类 |
| **AlgoExpert** | 高端刷题产品 | 无 AI 功能，纯视频讲解 | ~$99-250（产品包） | 200 精选题 + 100h 视频，9 语言，界面精美 |
| **Grind75 / Tech Interview Handbook** | 开源学习计划 | 无 AI，纯计划 + 链接 | 免费开源（GitHub 139k stars） | Blind 75 / Grind 75 题单，社区驱动 |
| **NeetCode** | 免费视频教程 | NeetCode Pro 有 AI 解题 | 免费视频 + Pro $10/月 | YouTube 大 V，NeetCode 150 题单很流行 |

### Tier 2：AI 编程助手（可间接用于刷题）

| 产品 | 说明 |
|------|------|
| **ChatGPT / Claude** | 直接粘贴题目即可获得讲解，零门槛 |
| **GitHub Copilot** | IDE 内自动补全，可直接在 LeetCode 页面使用 |
| **Cursor AI** | AI IDE，可以在其中刷题 |
| **各种 Chrome 插件** | GitHub 上有大量开源 LeetCode AI 助手插件 |

### Tier 3：面试准备平台（非纯算法）

| 产品 | 说明 | 定价 |
|------|------|------|
| **interviewing.io** | 真人 mock interview + AI Interviewer | 按次付费 |
| **Exponent** | 面试课程 + mock + AI 反馈 | 会员制 |
| **Pramp** | 免费 peer mock interview | 免费 |

### Tier 4：中国市场

| 产品 | 说明 |
|------|------|
| **牛客网** | 中国版 LeetCode，有 AI 讨论区但无专门 AI 教练功能 |
| **代码随想录** | 最火的中文算法学习路线（Carl 哥），视频 + PDF，无 AI |
| **力扣中国** | LeetCode 中文版，功能与国际版一致 |
| **labuladong** | 算法小抄，按框架/模式组织，无 AI |
| **各种 ChatGPT 刷题 prompt** | 小红书/知乎大量分享 |

## 二、关键发现

### 1. 没有一个产品真正做好"AI 教练"

现有产品分为两类：
- **给答案型**：ChatGPT、LeetCode AI、各种插件 → 直接输出完整代码和解题思路
- **不给 AI 型**：AlgoExpert、Design Gurus、代码随想录 → 纯视频/PDF 讲解

**缺失的中间地带：苏格拉底式 AI 教练** — 不直接给答案，而是通过提问引导用户自己思考。这是最大的差异化机会。

### 2. "模式识别"是最被验证的教学法

Design Gurus（Grokking 系列）和 NeetCode 都证明了一件事：**按算法模式（滑动窗口、双指针、BFS/DFS...）分类学习，比按题目顺序刷更高效**。但没有 AI 驱动的个性化模式识别。

### 3. 定价空间

- 免费：Grind75、NeetCode 视频、ChatGPT 基础版
- $10-15/月：NeetCode Pro
- $35/月：LeetCode Premium
- $99-197 一次性：AlgoExpert、Design Gurus
- **$5-15/月可能是 AI 教练的甜蜜定价点**

### 4. 痛点验证

刷题用户核心痛点（按频率排序）：
1. 刷了很多题但遇到新题还是不会（缺乏模式抽象能力）
2. 看懂了解析但自己写不出来（理解 ≠ 能写）
3. 不知道该刷哪些题、学习路径混乱
4. 坚持不下来，缺乏动力和节奏感
5. 时间紧，需要面试前快速突击

## 三、差异化方向分析

| 方向 | 竞争强度 | 可行性 | 差异化程度 |
|------|----------|--------|-----------|
| AI 给答案/解析 | **极高**（ChatGPT 免费做） | 低 | 无 |
| AI 学习路径规划 | 中（LeetCode Explore 已有） | 中 | 低 |
| **AI 苏格拉底式教练** | **低**（几乎无人做） | **高** | **高** |
| AI 薄弱点分析 + 选题 | 中（NeetCode Pro 部分） | 高 | 中 |
| 碎片化 5 分钟知识点 | 中（短视频、小红书） | 高 | 中 |
| AI 模拟面试 | 中（interviewing.io） | 中 | 中 |

## 四、结论

**最大差异化机会：AI 苏格拉底式教练**

- 不给答案，给提示和引导问题
- 根据用户的代码和思路实时调整引导策略
- 帮助用户从"看懂"跨越到"能写"
- 按算法模式组织，帮用户抽象出通用思维框架

这个方向竞争最小、价值最大、且是 ChatGPT 通用能力无法轻易替代的（需要专门的教学策略设计）。

## 五、下一步

1. 用自己的刷题经历验证痛点（你自己就是用户）
2. 手动做 MVP：每天一道题 + AI 教练式讲解发公众号/小红书
3. 验证有人愿意跟之后，再做成产品

## 相关页面
- [[make-indie-maker-blueprint]] — indie maker 方法论
- [[tanzhen]] — 当前创业项目（参考其调研方法）
- [[user-pain-points]] — 痛点验证方法论
