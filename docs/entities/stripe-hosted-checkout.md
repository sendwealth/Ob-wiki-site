---
title: Stripe Hosted Checkout
created: 2026-06-07
updated: 2026-06-07
type: entity
tags: [payment, stripe, saas, integration, marketplace]
sources:
  - name: Stripe 官方文档
    url: https://docs.stripe.com/payments/checkout
confidence: high
---

> Stripe 提供的预构建支付页面，客户跳转到 Stripe 托管的页面完成支付再跳回。低代码、PCI 自动合规、125+ 支付方式，是独立开发者和 SaaS 的默认最佳选择。

# Stripe Hosted Checkout

## 是什么

Stripe 四种支付 UI 方案之一（按代码量递增）：

| 方案 | 代码量 | 适用 |
|------|--------|------|
| Payment Links | 零代码 | 无网站，发链接收款 |
| **Hosted Checkout** | ~50 行 | 大多数场景默认选择 |
| Embedded Checkout | 中等 | 嵌入自己页面 |
| Elements | ~200+ 行 | 完全自定义 UI |

## 工作流程

```
用户点"购买"
  → 后端 POST /v1/checkout/sessions（传商品、金额、success_url）
  → 返回 Session URL（checkout.stripe.com/c/pay/cs_...）
  → 重定向用户到该 URL
  → 用户在 Stripe 页面完成支付
  → 跳回 success_url
  → 同时 Stripe 发 checkout.session.completed webhook
  → 后端 webhook 处理器更新订单
```

**关键**：用 webhook 确认支付，不依赖 success_url（用户可能关页面）。

## 费用

Checkout 本身无额外费用，标准交易费率：

| 类型 | 费率 |
|------|------|
| 国内卡 | 2.9% + $0.30 |
| 国际卡 | +1.5% |
| 货币转换 | +1% |
| 自定义域名 | $10/月 |

无月费、无设置费。

## 核心功能

**开箱即用**：
- 125+ 支付方式（信用卡、支付宝、微信支付、Apple Pay、Google Pay）
- PCI 合规（卡号不经过你的服务器）
- 移动端自适应、多语言、SCA 合规
- 反欺诈（Stripe Radar）

**可配置**：品牌定制、自定义域名、订阅+一次性混合购物车、优惠券、自动税费、放弃购物车恢复。

**三种模式**：`payment`（一次性）、`subscription`（订阅）、`setup`（保存支付方式）。

## 最简集成（Python）

```python
import stripe
from flask import Flask, redirect, request

stripe.api_key = 'sk_test_...'

# 创建支付会话
@app.route('/checkout', methods=['POST'])
def checkout():
    session = stripe.checkout.Session.create(
        line_items=[{
            'price_data': {
                'currency': 'usd',
                'product_data': {'name': '产品名'},
                'unit_amount': 2000,  # $20.00，单位：分
            },
            'quantity': 1,
        }],
        mode='payment',
        success_url='https://yoursite.com/success',
        cancel_url='https://yoursite.com/cancel',
    )
    return redirect(session.url, code=303)

# Webhook 确认支付
@app.route('/webhook', methods=['POST'])
def webhook():
    event = stripe.Webhook.construct_event(
        request.data, request.headers['Stripe-Signature'], endpoint_secret
    )
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        # 更新数据库、发邮件等
    return '', 200
```

## 平台市场模式（Stripe Connect）

对于双边市场（如 [[truthverifier]]），用 Checkout + Connect 做分账：

```python
session = stripe.checkout.Session.create(
    line_items=[...],
    mode='payment',
    payment_intent_data={
        'application_fee_amount': 500,  # 平台抽成
        'transfer_data': {
            'destination': 'acct_provider_123',  # 服务提供者账户
        },
    },
)
```

## 优缺点

**优点**：几小时上线、PCI 自动合规、125+ 支付方式、订阅/税费/反欺诈内置、无额外成本。

**缺点**：UI 定制有限（能改颜色/logo 不能改布局）、用户跳出网站（跳转体验）、Session 24h 过期、复杂多步流程不好做。

## 选择建议

- **默认用 Hosted Checkout**（90% 场景最佳平衡）
- 需要像素级控制支付 UI 时才用 Elements
- 没网站或想零代码时用 Payment Links

## 中国相关

- Stripe 支持中国企业注册
- 支付宝、微信支付均支持
- 支持 CNY 和 Adaptive Pricing 自动货币转换
- 无中国商业主体可用 Stripe Atlas 注册美国公司

## 关联

- [[truthverifier]] — 探真悬赏验证平台，可用 Checkout + Connect 做支付分账
- [[content-growth-loop]] — 内容增长闭环，同样涉及 SaaS 工具选型思维
