from typing import Union

from django.contrib import admin, messages
from django.http import HttpRequest
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from account.models import WeixinUser
from covibe_server.admin import BaseModelAdmin
from order.models import Order
from unfold.decorators import action

from .api import WechatAPIException
from .models import WechatOrder, WechatPayRefund, WechatPayTransaction


@admin.register(WechatOrder)
class WechatOrderAdmin(BaseModelAdmin):
    ordering = ("-created_at",)

    class Media:
        js = ("wechat/js/wechatorder_change_native_qr.js",)

    actions_detail = ["query_wechat_pay_result", "refresh_wechat_prepay"]
    list_display = (
        "uuid",
        "order",
        "prepay_id",
        "prepay_id_expires",
        "native_code_url_short",
        "native_code_url_expires",
        "created_at",
    )
    search_fields = ("uuid", "order__uuid", "prepay_id", "native_code_url")
    autocomplete_fields = ("order",)
    readonly_fields = ("uuid", "created_at", "updated_at")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "order",
                    "prepay_id",
                    "prepay_id_expires",
                    "native_code_url",
                    "native_code_url_expires",
                    ("uuid", "created_at", "updated_at"),
                )
            },
        ),
    )

    @admin.display(description=_("Native code_url"))
    def native_code_url_short(self, obj: WechatOrder) -> str:
        u = (obj.native_code_url or "").strip()
        if not u:
            return "-"
        if len(u) > 48:
            return f"{u[:48]}…"
        return u

    @action(
        description=_("主动查询微信订单"),
        url_path="query-wechat-pay-result",
        permissions=["query_wechat_pay_result"],
    )
    def query_wechat_pay_result(self, request: HttpRequest, object_id: Union[str, int]):
        wo = WechatOrder.objects.select_related("order").get(pk=object_id)
        try:
            data = wo.query_and_sync_pay_result()
        except WechatAPIException as exc:
            messages.error(request, _("查询失败：%(err)s") % {"err": exc})
            return redirect(reverse("admin:wechat_wechatorder_change", args=(object_id,)))
        state = (data.get("trade_state") or "").upper()
        messages.success(request, _("已同步微信订单，trade_state=%(s)s") % {"s": state or "—"})
        return redirect(reverse("admin:wechat_wechatorder_change", args=(object_id,)))

    def has_query_wechat_pay_result_permission(self, request: HttpRequest, object_id: Union[str, int]) -> bool:
        return request.user.has_perm("wechat.change_wechatorder")

    @action(
        description=_("重新预下单"),
        url_path="refresh-wechat-prepay",
        permissions=["refresh_wechat_prepay"],
    )
    def refresh_wechat_prepay(self, request: HttpRequest, object_id: Union[str, int]):
        wo = WechatOrder.objects.select_related("order").get(pk=object_id)
        order = wo.order
        openid = ""
        if order.payment_platform == Order.PAYMENT_PLATFORM_WECHATPAY_JSAPI:
            wu = WeixinUser.objects.filter(user=order.buyer).first()
            if not wu or not wu.openid:
                messages.error(
                    request,
                    _("JSAPI 预下单需要买家已绑定微信且存在 openid；当前无法自动获取。"),
                )
                return redirect(reverse("admin:wechat_wechatorder_change", args=(object_id,)))
            openid = wu.openid
        try:
            wo.create_prepay(openid=openid)
        except ValueError as exc:
            messages.error(request, _("预下单失败：%(err)s") % {"err": exc})
            return redirect(reverse("admin:wechat_wechatorder_change", args=(object_id,)))
        except WechatAPIException as exc:
            messages.error(request, _("预下单失败：%(err)s") % {"err": exc})
            return redirect(reverse("admin:wechat_wechatorder_change", args=(object_id,)))
        except Exception as exc:
            messages.error(request, _("预下单失败：%(err)s") % {"err": exc})
            return redirect(reverse("admin:wechat_wechatorder_change", args=(object_id,)))
        messages.success(request, _("已向微信重新下单并更新本地预支付信息。"))
        return redirect(reverse("admin:wechat_wechatorder_change", args=(object_id,)))

    def has_refresh_wechat_prepay_permission(self, request: HttpRequest, object_id: Union[str, int]) -> bool:
        return request.user.has_perm("wechat.change_wechatorder")


@admin.register(WechatPayTransaction)
class WechatPayTransactionAdmin(BaseModelAdmin):
    ordering = ("-created_at",)
    list_display = ("uuid", "out_trade_no", "transaction_id", "trade_state", "payer_total_minor", "created_at")
    search_fields = ("uuid", "out_trade_no", "transaction_id", "order__uuid")
    autocomplete_fields = ("order",)


@admin.register(WechatPayRefund)
class WechatPayRefundAdmin(BaseModelAdmin):
    ordering = ("-created_at",)
    list_display = ("uuid", "wx_refund_id", "created_at")
    search_fields = ("uuid", "wx_refund_id")
    autocomplete_fields = ("refund",)
