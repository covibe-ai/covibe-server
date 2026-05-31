from datetime import datetime, timedelta

from constance import config
from django.db import models
from django.utils import timezone

from project_name.models import BaseModel
from order.models import Order, PaymentPlatformOrder


class WechatPayTransaction(BaseModel):
    STATUS_SUCCESS = "SUCCESS"
    STATUS_REFUND = "REFUND"
    STATUS_NOTPAY = "NOTPAY"
    STATUS_CLOSED = "CLOSED"

    TRADE_STATUS_CHOICES = [
        (STATUS_SUCCESS, "支付成功"),
        (STATUS_REFUND, "转入退款"),
        (STATUS_NOTPAY, "未支付"),
        (STATUS_CLOSED, "已关闭"),
    ]

    SOURCE_API = "api"
    SOURCE_NOTIFY = "notify"
    SOURCE_CHOICES = [
        (SOURCE_API, "API查询"),
        (SOURCE_NOTIFY, "支付通知"),
    ]

    order = models.ForeignKey(Order, on_delete=models.SET_NULL, null=True, default=None, related_name="wxpay_transactions", verbose_name="关联订单")
    transaction_id = models.CharField(max_length=64, db_index=True, blank=True, default="", verbose_name="微信支付订单号")
    out_trade_no = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="微信支付商户订单号")
    total_minor = models.BigIntegerField(default=0, verbose_name="总金额(分)")
    payer_total_minor = models.BigIntegerField(default=0, verbose_name="用户支付金额(分)")
    trade_state = models.CharField(max_length=20, choices=TRADE_STATUS_CHOICES, default=STATUS_NOTPAY, verbose_name="交易状态")
    trade_state_desc = models.CharField(max_length=256, blank=True, default="", verbose_name="交易状态描述")
    success_time = models.DateTimeField(null=True, blank=True, default=None, verbose_name="支付完成时间")
    raw_data = models.TextField(default="", blank=True, verbose_name="原始数据")
    source = models.CharField(max_length=10, choices=SOURCE_CHOICES, verbose_name="交易单来源")

    class Meta:
        verbose_name = "微信支付单"
        verbose_name_plural = "微信支付单"
        ordering = ["-created_at"]
        db_table = "wechat_pay_transaction"

    def on_update(self):
        if self.order:
            self.order.on_payment_changed()

    @staticmethod
    def check_paid_list(transactions):
        paid_total = 0
        latest_success_time = None
        for transaction in transactions:
            if transaction.trade_state == WechatPayTransaction.STATUS_SUCCESS:
                paid_total += transaction.payer_total_minor
                if not latest_success_time or (transaction.success_time and transaction.success_time > latest_success_time):
                    latest_success_time = transaction.success_time
        return paid_total, latest_success_time

    @staticmethod
    def from_api_body(api_data, source):
        out_trade_no = api_data.get("out_trade_no", "")
        order = Order.objects.filter(uuid=out_trade_no).first()
        success_time = None
        if api_data.get("success_time"):
            success_time = datetime.strptime(api_data["success_time"], "%Y-%m-%dT%H:%M:%S%z")
        amount = api_data.get("amount", {})
        return WechatPayTransaction(
            order=order,
            transaction_id=api_data.get("transaction_id", ""),
            out_trade_no=out_trade_no,
            total_minor=int(amount.get("total") or 0),
            payer_total_minor=int(amount.get("payer_total") or 0),
            trade_state=(api_data.get("trade_state") or WechatPayTransaction.STATUS_NOTPAY).upper(),
            trade_state_desc=api_data.get("trade_state_desc", ""),
            success_time=success_time,
            raw_data=str(api_data),
            source=source,
        )

    @classmethod
    def apply_query_or_notify_body(cls, api_data: dict, *, source: str) -> "WechatPayTransaction":
        """
        将「商户订单号查询订单」或支付成功回调解密后的报文落库 ``WechatPayTransaction``，
        并调用 ``on_update()`` 与 notify 链路一致（推进 ``Order.on_payment_changed`` / ``make_paid``）。
        """
        tx = cls.from_api_body(api_data, source)
        obj, _ = cls.objects.update_or_create(
            out_trade_no=tx.out_trade_no,
            defaults={
                "order": tx.order,
                "transaction_id": tx.transaction_id,
                "total_minor": tx.total_minor,
                "payer_total_minor": tx.payer_total_minor,
                "trade_state": tx.trade_state,
                "trade_state_desc": tx.trade_state_desc,
                "success_time": tx.success_time,
                "raw_data": tx.raw_data,
                "source": tx.source,
            },
        )
        obj.on_update()
        return obj


class WechatPayRefund(BaseModel):
    refund = models.ForeignKey("order.Refund", on_delete=models.SET_NULL, null=True, default=None, related_name="wxpay_refunds", verbose_name="关联退款单")
    wx_refund_id = models.CharField(max_length=64, unique=True, db_index=True, verbose_name="微信支付退款单号")
    raw_data = models.TextField(default="", blank=True, verbose_name="原始数据")

    class Meta:
        verbose_name = "微信退款记录"
        verbose_name_plural = verbose_name
        db_table = "wechat_pay_refund"


class WechatOrder(PaymentPlatformOrder):
    prepay_id = models.CharField(max_length=128, blank=True, default="", verbose_name="预支付ID")
    prepay_id_expires = models.DateTimeField(null=True, blank=True, default=None, verbose_name="预支付ID过期时间")
    native_code_url = models.TextField(blank=True, default="", verbose_name="Native code_url")
    native_code_url_expires = models.DateTimeField(
        null=True, blank=True, default=None, verbose_name="Native code_url 过期时间"
    )

    class Meta:
        verbose_name = "微信支付订单"
        verbose_name_plural = verbose_name
        db_table = "wechat_order"

    @classmethod
    def get_wechat_order(cls, order: Order):
        obj, _ = cls.objects.get_or_create(order=order)
        return obj

    def create_prepay(self, openid: str = ""):
        from .api import WechatAPI

        wechat_api = WechatAPI()
        if self.order.payment_platform == Order.PAYMENT_PLATFORM_WECHATPAY_JSAPI:
            if not openid:
                raise ValueError("JSAPI下单必须提供openid")
            body = wechat_api.get_pay_prepay_id(
                order_id=str(self.order.uuid),
                openid=openid,
                total_fee_minor=self.order.amount_minor,
                description=f"订单{self.order.uuid}",
            )
            self.prepay_id = body["prepay_id"]
            self.prepay_id_expires = timezone.now() + timedelta(hours=2)
            self.save(update_fields=["prepay_id", "prepay_id_expires", "updated_at"])
            return {
                "payment_platform": self.order.payment_platform,
                "params": wechat_api.get_pay_sign(self.prepay_id),
            }

        if self.order.payment_platform == Order.PAYMENT_PLATFORM_WECHATPAY_NATIVE:
            expire_minutes = int(config.WECHAT_PAY_NATIVE_EXPIRE_MINUTES or 15)
            expire_at = timezone.now() + timedelta(minutes=expire_minutes)
            body = wechat_api.get_native_code_url(
                order_id=str(self.order.uuid),
                total_fee_minor=self.order.amount_minor,
                description=f"订单{self.order.uuid}",
                time_expire=expire_at,
            )
            self.native_code_url = (body.get("code_url") or "").strip()
            self.native_code_url_expires = expire_at
            self.save(update_fields=["native_code_url", "native_code_url_expires", "updated_at"])
            return {
                "payment_platform": self.order.payment_platform,
                "params": body,
            }

        raise ValueError(f"不支持的支付平台: {self.order.payment_platform}")

    def check_payment(self) -> None:
        """主动查微信单并同步 ``WechatPayTransaction`` / ``Order``（与回调共用落库逻辑）。"""
        self.query_and_sync_pay_result()

    def query_and_sync_pay_result(self) -> dict:
        """
        主动调用「[商户订单号查询订单](https://pay.weixin.qq.com/doc/v3/merchant/4012791880)」
        GET ``/v3/pay/transactions/out-trade-no/{out_trade_no}``，将应答与 notify 共用落库与推进订单逻辑。
        """
        from .api import WechatAPI

        data = WechatAPI().get_pay_transaction(str(self.order.uuid))
        WechatPayTransaction.apply_query_or_notify_body(data, source=WechatPayTransaction.SOURCE_API)
        return data

    def get_paid_amount(self):
        transactions = self.order.wxpay_transactions.all()
        return WechatPayTransaction.check_paid_list(transactions)

    def before_order_closed(self):
        from .api import WechatAPIException

        try:
            data = self.query_and_sync_pay_result()
        except WechatAPIException:
            return False
        if data.get("trade_state", "").upper() == WechatPayTransaction.STATUS_SUCCESS:
            return False
        return True

    def on_order_closed(self):
        from .api import WechatAPI, WechatAPIException

        wechat_api = WechatAPI()
        try:
            wechat_api.close_pay_transaction(str(self.order.uuid))
        except WechatAPIException:
            return
