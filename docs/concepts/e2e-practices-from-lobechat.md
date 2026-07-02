# LobeChat E2E 测试实践

> 从 LobeChat 项目中学习到的端到端测试实践方法。

## 技术栈

- **Cucumber (BDD)** + **Playwright** — 用 Gherkin 语法描述用户行为，Playwright 驱动浏览器
- **TypeScript** 编写 step definitions
- **tsx** 作为运行时（`requireModule: ['tsx/cjs']`）

## 核心架构

### 1. 目录结构 — 按功能域组织

```
e2e/
├── src/
│   ├── features/          # Gherkin .feature 文件
│   │   ├── journeys/      # 用户旅程测试（端到端完整流程）
│   │   │   ├── agent/     # Agent 对话相关
│   │   │   ├── page/      # 页面/文稿相关
│   │   │   └── ...
│   │   ├── smoke/         # 冒烟测试
│   │   └── community/     # 社区相关
│   ├── steps/             # Step definitions
│   │   ├── common/        # 通用步骤（auth、navigation）
│   │   ├── agent/         # Agent 领域步骤
│   │   └── hooks.ts       # Before/After 生命周期钩子
│   ├── mocks/             # Mock 框架
│   │   ├── llm/           # LLM 请求拦截 Mock
│   │   └── community/     # 社区 API Mock
│   └── support/           # 基础设施
│       ├── world.ts       # CustomWorld（封装 Playwright）
│       ├── webServer.ts   # Web 服务器启停管理
│       └── seedTestUser.ts # 测试用户数据准备
├── cucumber.config.js     # Cucumber 配置
└── CLAUDE.md              # AI Agent 开发指南
```

**关键点**：feature 文件和 steps 文件按**业务领域**组织，不是按技术层组织。journey 测试覆盖完整用户流程，smoke 测试快速验证核心功能。

### 2. CustomWorld — 封装 Playwright 上下文

```typescript
// world.ts
export class CustomWorld extends World {
  browser!: Browser;
  browserContext!: BrowserContext;
  page!: Page;
  testContext: TestContext;  // 存储 console 错误、JS 错误、最后响应等

  async init() {
    // 启动浏览器、创建 context、创建 page
    // 注册 pageerror / console 错误监听
  }

  async cleanup() {
    // 关闭 page、context、browser
  }

  async takeScreenshot(name: string): Promise<Buffer> {
    // 失败时截图保存到 screenshots/ 目录
  }
}
```

**要点**：
- 继承 Cucumber 的 `World`，每个 Scenario 拥有独立的 browser/page 实例
- `testContext` 收集运行时错误，用于断言页面无 JS 错误
- 封装了截图、清理等公共操作

### 3. Hooks — 测试生命周期管理

```typescript
// hooks.ts

BeforeAll:
  1. seedTestUser() — 向数据库插入测试用户
  2. startWebServer() — 启动 Next.js 生产服务器（如未提供外部 BASE_URL）
  3. 一次性登录获取 session cookies 并缓存

Before (每个 Scenario):
  1. this.init() — 初始化浏览器
  2. 注入缓存的 session cookies（跳过重复登录）
  3. 可选：设置 API mocks

After (每个 Scenario):
  1. 失败时：截图 + 保存 HTML + 记录 JS 错误 → attach 到报告
  2. this.cleanup() — 关闭浏览器

AfterAll:
  1. 停止 Web 服务器（CI 环境）
```

**要点**：
- Session cookie 缓存是性能关键优化 — 只登录一次，每个 scenario 复用 cookie
- 失败时自动截图和保存 HTML，方便调试
- Web 服务器管理支持跨进程协调（文件锁）

### 4. 测试用户管理 — 直接操作数据库

```typescript
// seedTestUser.ts
export const TEST_USER = {
  email: 'e2e-test@lobehub.com',
  password: 'TestPassword123!',
  id: 'user_e2e_test_user_001',
  // ...
};

// BeforeAll 调用：向 PostgreSQL 插入用户、账户记录
export async function seedTestUser(): Promise<void> {
  // 使用 ON CONFLICT DO NOTHING 处理并发
  // 设置 onboarding 为已完成（跳过引导流程）
}

// 创建 session token（直接写入 auth_sessions 表）
export async function createTestSession(): Promise<string | null> {
  // 返回 session token 字符串
}
```

**要点**：
- 使用固定 ID + `ON CONFLICT` 处理并发 worker 场景
- 两种登录方式：UI 表单登录（慢但真实） vs Session 注入（快，跳过 UI）
- 测试结束后可清理测试数据

### 5. LLM Mock — 拦截 AI 请求

这是该项目最有特色的部分。E2E 测试不能依赖真实 LLM API（不稳定、慢、费钱），所以用 Playwright 的 `page.route()` 拦截请求：

```typescript
// mocks/llm/index.ts
class LLMMockManager {
  async setup(page: Page) {
    await page.route('**/webapi/chat/**', async (route) => {
      // 解析请求中的 messages
      // 根据用户消息匹配预设响应
      // 构建 SSE 流式响应返回
    });
  }

  // 注册自定义响应
  setResponse(trigger: string, response: string) { ... }
}
```

**SSE 流格式**（必须严格匹配 LobeChat 的协议）：
```
event: data    → 初始消息元数据
event: text    → 文本分块（多个）
event: stop    → "end_turn"
event: usage   → token 用量统计
event: stop    → "message_stop"
```

**要点**：
- 不需要 Mock server，直接用 Playwright 路由拦截
- 支持根据用户输入内容匹配不同预设响应
- 模拟真实的 SSE 流式输出

### 6. Feature 文件写法 — 体验驱动的 BDD

```gherkin
@journey @agent @conversation
Feature: Agent 对话用户体验链路
  作为用户，我希望能够与 AI 助手进行流畅的对话

  Background:
    Given 用户已登录系统

  @AGENT-CHAT-001 @P0 @smoke
  Scenario: 使用 Lobe AI 发送消息并获得回复
    Given 用户进入 Lobe AI 对话页面
    When 用户发送消息 "hello"
    Then 用户应该收到助手的回复
    And 回复内容应该可见
```

### 7. 标签系统 — 控制执行范围

| 标签 | 含义 |
|------|------|
| `@journey` | 用户旅程测试 |
| `@smoke` | 冒烟测试 |
| `@P0` / `@P1` / `@P2` | 优先级 |
| `@agent` / `@page` / `@community` | 业务模块 |

执行策略：
```bash
# CI — 每次只跑 P0 冒烟
--tags "@smoke and @P0"

# Nightly — 所有用户旅程
--tags "@journey"

# 发版前 — 完整回归
--tags "@P0 or @P1"
```

## 可以借鉴的模式

### 1. Cucumber + Playwright 组合

BDD 风格让测试用例成为**活文档**，产品、QA、开发都能读懂。Playwright 提供可靠的浏览器自动化。Cucumber 的 Before/After hooks 管理生命周期。

### 2. Session Cookie 缓存

只在 BeforeAll 登录一次，所有 Scenario 复用 cookie。这比每个测试都走登录流程快很多。

### 3. LLM Mock via Route Interception

对于 AI 产品，不能在 E2E 测试中调用真实 API。Playwright 的 `page.route()` 提供了一种轻量级的 Mock 方案，不需要额外启动 Mock server。

### 4. 数据库直接操作

用 SQL 直接准备测试数据（用户、session），比 UI 操作更快更稳定。配合 `ON CONFLICT` 处理并发。

### 5. Web Server 自动管理

测试框架自己管理被测应用的启停，支持：
- 检测已有服务复用
- 文件锁协调多 worker
- 超时和错误处理

### 6. 失败诊断

失败时自动：
- 截图保存到文件
- 保存 HTML 快照
- 收集 console 错误
- 全部 attach 到 Cucumber HTML 报告

### 7. 按业务域组织

Steps 不是按 "Given/When/Then" 分文件，而是按业务域（agent/、page/、common/）。同一个领域的 feature + steps 放在一起，方便维护。

## Cucumber 配置要点

```javascript
// cucumber.config.js
export default {
  format: ['progress-bar', 'html:reports/cucumber-report.html'],
  parallel: 1,              // 串行执行（避免并发问题）
  paths: ['src/features/**/*.feature'],
  require: ['src/steps/**/*.ts', 'src/support/**/*.ts'],
  requireModule: ['tsx/cjs'],  // 用 tsx 直接运行 TS
  tags: 'not @skip',
  timeout: 30_000,
};
```

## 运行方式

```bash
# 本地调试（显示浏览器）
HEADLESS=false pnpm exec cucumber-js --config cucumber.config.js --tags "@AGENT-CHAT-001"

# CI
pnpm exec cucumber-js --config cucumber.config.js --tags "@smoke and @P0"

# 特定模块
pnpm exec cucumber-js --config cucumber.config.js src/features/community/
```
