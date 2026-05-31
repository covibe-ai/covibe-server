# 微信支付流程文档

本文档描述本模板（源自 `free3dkit-backend`）的微信支付实现，覆盖 `wechatpay_jsapi` 与 `wechatpay_native` 两种平台值。  
订单创建默认 `payment_platform=wechatpay_native`（见 `order` 模型与创建序列化器）；需 JSAPI 时创建订单须显式传入 `wechatpay_jsapi`。  
订单域通用流程见 `order.md`。

---

## 1. 支付架构

### 1.1 参与模块

- `order` app：订单创建、状态机、统一预支付入口。
- `wechat` app：微信 APIv3 调用、支付流水落库、回调处理。

### 1.2 关键对象

- `WechatOrder`：平台订单对象（挂载在 `Order.platform_order`）。
- `WechatPayTransaction`：支付交易流水（回调/API 查单都会写入）。
- `WechatPayRefund`：退款流水占位模型（本期未完整打通）。

---

## 2. 对外接口

前缀：`/api/v1/`

## 创建微信预支付

- **路径**: `POST /api/v1/orders/{id}/pay/wechat/prepay/`
- **认证**: 必填

### 返回体（统一）

| 字段 | 类型 | 说明 |
|------|------|------|
| `payment_platform` | string | `wechatpay_jsapi` 或 `wechatpay_native` |
| `params` | object | 平台对应的支付参数 |

### `params` 说明

- 当 `payment_platform=wechatpay_jsapi`：
  - 返回 JSAPI 调起参数：`appId`、`timeStamp`、`nonceStr`、`package`、`signType`、`paySign`
- 当 `payment_platform=wechatpay_native`：
  - 返回 Native 下单结果，核心为 `code_url`

### 可能错误

- `PAYMENT_PLATFORM_NOT_SUPPORTED`
- `WECHAT_USER_NOT_BOUND`
- `PAYMENT_PARAM_INVALID`
- `WECHAT_PREPAY_CREATE_FAILED`

---

## 支付回调通知

- **路径**: `POST /api/v1/payments/wechat/pay/notify/`
- **认证**: 无（微信服务端回调）

### 处理逻辑

1. 读取回调请求头中的签名字段。
2. `verify_notify_signature` 验签（平台证书已配置时）。
3. 用 APIv3 Key 解密 `resource`。
4. 写入/更新 `WechatPayTransaction`。
5. 调用 `Order.on_payment_changed()` 推进订单状态。

### 回调应答

- 成功：`{"code":"SUCCESS","message":"成功"}`
- 失败：`{"code":"FAIL","message":"..."}`（HTTP 200）

---

## 退款回调通知（占位）

- **路径**: `POST /api/v1/payments/wechat/refund/notify/`
- **认证**: 无
- **状态**: 当前仅做验签与解密通路，退款业务状态机待补完。

---

## 3. JSAPI 流程

## 3.1 前端 -> 后端

1. 前端创建订单并显式指定 `payment_platform=wechatpay_jsapi`（默认 Native 见上文）。
2. 前端调用 `POST /orders/{id}/pay/wechat/prepay/`。

## 3.2 后端 -> 微信

1. 后端校验并获取用户 `openid`。
2. 调微信 `POST /v3/pay/transactions/jsapi`（下单，获取 `prepay_id`）。
3. 后端本地生成 JSAPI 调起签名参数并返回给前端。

## 3.3 前端支付 & 结果确认

1. 前端使用 `params` 拉起微信支付。
2. 后端通过回调更新订单状态。
3. 前端查询订单详情确认最终状态。

---

## 4. Native 流程

## 4.1 前端 -> 后端

1. 前端创建订单（可不传 `payment_platform`，默认即为 `wechatpay_native`；亦可显式传 `payment_platform=wechatpay_native`）。
2. 前端调用 `POST /orders/{id}/pay/wechat/prepay/`。

## 4.2 后端 -> 微信

1. 后端调用 `POST /v3/pay/transactions/native` 下单。
2. 请求体可带 `time_expire`（由 `WECHAT_PAY_NATIVE_EXPIRE_MINUTES` 控制）。
3. 返回 `code_url` 给前端。

## 4.3 前端支付 & 结果确认

1. 前端把 `code_url` 转二维码展示。
2. 用户扫码支付。
3. 支付成功后由微信回调驱动订单状态更新。
4. 前端查询订单详情确认最终状态。

---

## 5. 定时关单

- 任务：`order.tasks.auto_close_expired_orders`
- 调度：`CELERY_BEAT_SCHEDULE`（默认 60 秒一次）
- 规则：
  - 订单状态为 `PENDING`
  - 超过 `WECHAT_PAY_NATIVE_EXPIRE_MINUTES`
- 执行动作：调用 `order.make_closed()`，内部会触发平台查单与关单逻辑。

---

## 6. 关键配置（Constance）

- `WECHAT_PAY_APP_ID`
- `WECHAT_PAY_MCH_ID`
- `WECHAT_PAY_SERIAL_NO`
- `WECHAT_PAY_PRIVATE_KEY`
- `WECHAT_PAY_API_V3_KEY`
- `WECHAT_PAY_VERIFY_PUBLIC_KEY_PEM`
- `WECHAT_PAY_VERIFY_KEY_ID`
- `WECHAT_PAY_NOTIFY_URL`
- `WECHAT_PAY_REFUND_NOTIFY_URL`
- `WECHAT_PAY_NATIVE_EXPIRE_MINUTES`

---

## 7. 当前边界

- 退款业务流（申请、查询、状态推进）尚未完整打通。
- 微信接口应答签名校验与证书轮换能力可继续增强。
