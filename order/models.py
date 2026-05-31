from __future__ import annotations

import traceback

from django.conf import settings
from django.db import models, transaction
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from project_name.models import BaseModel
from system.log import Log
from system.models import Log as LogModel


class OrderItem(BaseModel):
    """订单项。支付成功后由 ``Order.make_paid`` 调用 ``fulfill`` 履约。"""

    KIND_GENERIC = "generic"

    KIND_CHOICES = (
        (KIND_GENERIC, _("通用")),
    )

    EXECUTE_STATUS_PENDING = 10
    EXECUTE_STATUS_SUCCEEDED = 30
    EXECUTE_STATUS_CHOICES = (
        (EXECUTE_STATUS_PENDING, _("待履约")),
        (EXECUTE_STATUS_SUCCEEDED, _("已履约")),
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pay_order_items",
        verbose_name=_("买家"),
    )
    kind = models.CharField(max_length=64, choices=KIND_CHOICES, default=KIND_GENERIC, verbose_name=_("品类"))
    params = models.JSONField(default=dict, verbose_name=_("参数"))
    normalized_key = models.CharField(max_length=128, blank=True, default="", db_index=True, verbose_name=_("规范化键"))
    amount_minor = models.BigIntegerField(verbose_name=_("应付金额(分)"))
    original_amount_minor = models.BigIntegerField(default=0, verbose_name=_("原价(分)"))
    currency = models.CharField(max_length=3, default="CNY", verbose_name=_("货币"))
    execute_status = models.IntegerField(
        choices=EXECUTE_STATUS_CHOICES,
        default=EXECUTE_STATUS_PENDING,
        db_index=True,
        verbose_name=_("履约状态"),
    )

    class Meta:
        verbose_name = _("订单项")
        verbose_name_plural = _("订单项")
        db_table = "order_orderitem"

    def summary_without_uuid(self) -> str:
        title = self.params.get("title") if isinstance(self.params, dict) else None
        if title:
            return str(title)
        return self.get_kind_display()

    def __str__(self) -> str:
        body = self.summary_without_uuid()
        u = str(self.uuid) if getattr(self, "uuid", None) else ""
        return f"{body}（{u}）" if u else body

    def admin_summary_line(self) -> str:
        order = getattr(self, "order", None)
        u = str(order.uuid) if order is not None else (str(self.uuid) if getattr(self, "uuid", None) else "")
        return f"{self.summary_without_uuid()}（{u}）" if u else self.summary_without_uuid()

    @classmethod
    def build_normalized_key(cls, kind: str, params: dict) -> str:
        if isinstance(params, dict) and params.get("key"):
            return f"{kind}:{params['key']}"
        return kind

    def fulfill(self, order: "Order") -> None:
        """支付成功后履约。业务项目可在此扩展或 override。"""
        pass


class Order(BaseModel):
    PAYMENT_PLATFORM_WECHATPAY_JSAPI = "wechatpay_jsapi"
    PAYMENT_PLATFORM_WECHATPAY_NATIVE = "wechatpay_native"
    PAYMENT_PLATFORM_WECHATPAY_XPAY = "wechatpay_xpay"
    PAYMENT_PLATFORM_ALIPAY = "alipay"
    PAYMENT_PLATFORM_CHOICES = (
        (PAYMENT_PLATFORM_WECHATPAY_JSAPI, _("微信支付(JSAPI)")),
        (PAYMENT_PLATFORM_WECHATPAY_NATIVE, _("微信支付(Native)")),
        (PAYMENT_PLATFORM_WECHATPAY_XPAY, _("微信支付(XPay)")),
        (PAYMENT_PLATFORM_ALIPAY, _("支付宝")),
    )

    STATUS_PENDING = 10
    STATUS_PAID = 30
    STATUS_CLOSED = 90
    STATUS_CHOICES = (
        (STATUS_PENDING, _("待支付")),
        (STATUS_PAID, _("已支付")),
        (STATUS_CLOSED, _("已关闭")),
    )

    buyer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name="pay_orders",
        verbose_name=_("买家"),
    )
    item = models.OneToOneField(OrderItem, on_delete=models.PROTECT, related_name="order", verbose_name=_("订单项"))
    status = models.IntegerField(choices=STATUS_CHOICES, default=STATUS_PENDING, db_index=True, verbose_name=_("订单状态"))
    payment_platform = models.CharField(
        max_length=32,
        choices=PAYMENT_PLATFORM_CHOICES,
        default=PAYMENT_PLATFORM_WECHATPAY_NATIVE,
        verbose_name=_("支付平台"),
    )
    amount_minor = models.BigIntegerField(verbose_name=_("应付金额(分)"))
    original_amount_minor = models.BigIntegerField(default=0, verbose_name=_("原价(分)"))
    paid_amount_minor = models.BigIntegerField(default=0, verbose_name=_("实收金额(分)"))
    currency = models.CharField(max_length=3, default="CNY", verbose_name=_("货币"))
    paid_at = models.DateTimeField(null=True, blank=True, verbose_name=_("支付时间"))
    closed_at = models.DateTimeField(null=True, blank=True, verbose_name=_("关闭时间"))

    class Meta:
        verbose_name = _("订单")
        verbose_name_plural = _("订单")
        db_table = "order_order"

    def fulfillment_items(self):
        return [self.item]

    @property
    def supports_active_payment_check(self) -> bool:
        return self.payment_platform in (
            self.PAYMENT_PLATFORM_WECHATPAY_JSAPI,
            self.PAYMENT_PLATFORM_WECHATPAY_NATIVE,
        )

    @property
    def platform_order(self):
        if self.payment_platform in (
            self.PAYMENT_PLATFORM_WECHATPAY_JSAPI,
            self.PAYMENT_PLATFORM_WECHATPAY_NATIVE,
        ):
            from wechat.models import WechatOrder

            return WechatOrder.get_wechat_order(self)
        return None

    def on_payment_changed(self):
        payment_order = self.platform_order
        if not payment_order:
            return
        paid_total_minor, latest_success_time = payment_order.get_paid_amount()
        self.paid_amount_minor = paid_total_minor
        self.paid_at = latest_success_time or self.paid_at
        self.save(update_fields=["paid_amount_minor", "paid_at", "updated_at"])
        if self.status != self.STATUS_CLOSED and paid_total_minor >= self.amount_minor:
            self.make_paid()

    def make_paid(self):
        if self.status != self.STATUS_PENDING:
            return

        with transaction.atomic():
            order = Order.objects.select_for_update().select_related("item").get(pk=self.pk)
            if order.status != Order.STATUS_PENDING:
                return
            order.status = Order.STATUS_PAID
            if not order.paid_at:
                order.paid_at = timezone.now()
            order.save(update_fields=["status", "paid_at", "updated_at"])
            for line in order.fulfillment_items():
                try:
                    line.fulfill(order)
                    line.execute_status = OrderItem.EXECUTE_STATUS_SUCCEEDED
                    line.save(update_fields=["execute_status", "updated_at"])
                except Exception:
                    Log.error(
                        "订单履约失败",
                        f"order={order.uuid} item={line.uuid} kind={line.kind}\n{traceback.format_exc()}",
                        LogModel.Module.ORDER,
                    )
                    raise
            Log.info(
                "订单已支付并完成履约",
                f"order={order.uuid} buyer={order.buyer_id} amount_minor={order.amount_minor}",
                LogModel.Module.ORDER,
            )
        self.refresh_from_db()

    def make_closed(self):
        if self.status != self.STATUS_PENDING:
            return
        payment_order = self.platform_order
        if payment_order and not payment_order.before_order_closed():
            return
        self.status = self.STATUS_CLOSED
        self.closed_at = timezone.now()
        self.save(update_fields=["status", "closed_at", "updated_at"])
        if payment_order:
            payment_order.on_order_closed()

    def __str__(self) -> str:
        ou = str(self.uuid) if getattr(self, "uuid", None) else ""
        try:
            body = self.item.summary_without_uuid()
        except OrderItem.DoesNotExist:
            body = "订单"
        return f"{body}({ou})" if ou else body


class PaymentPlatformOrder(BaseModel):
    order = models.OneToOneField(Order, on_delete=models.PROTECT, related_name="%(class)s_obj", verbose_name=_("订单"))

    class Meta:
        abstract = True

    def check_payment(self) -> None:
        return None

    def get_paid_amount(self):
        return 0, None

    def before_order_closed(self):
        return True

    def on_order_closed(self):
        return None


class Refund(BaseModel):
    STATUS_DRAFT = "draft"
    STATUS_CHOICES = ((STATUS_DRAFT, _("草稿")),)

    order = models.ForeignKey(Order, on_delete=models.PROTECT, related_name="refunds", verbose_name=_("订单"))
    refund_amount_minor = models.BigIntegerField(default=0, verbose_name=_("退款金额(分)"))
    status = models.CharField(max_length=16, default=STATUS_DRAFT, choices=STATUS_CHOICES, verbose_name=_("退款状态"))
    reason = models.TextField(blank=True, default="", verbose_name=_("退款原因"))

    class Meta:
        verbose_name = _("退款")
        verbose_name_plural = _("退款")
        db_table = "order_refund"

    def __str__(self):
        return f"{self.uuid}:{self.status}"
