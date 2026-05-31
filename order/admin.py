from decimal import Decimal

from django.contrib import admin
from django.http import HttpRequest
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _
from unfold.contrib.filters.admin import (
    AutocompleteSelectFilter,
    ChoicesDropdownFilter,
    RangeDateTimeFilter,
)

from covibe_server.admin import BaseModelAdmin

from .models import Order, OrderItem, Refund


def _minor_to_yuan_display(minor: int | None) -> str:
    if minor is None:
        return "-"
    q = (Decimal(int(minor)) / Decimal(100)).quantize(Decimal("0.01"))
    return format(q, "f")


@admin.register(OrderItem)
class OrderItemAdmin(BaseModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "uuid",
        "buyer",
        "kind",
        "display_amount_minor",
        "currency",
        "execute_status",
        "created_at",
    )
    list_filter = (
        ("buyer", AutocompleteSelectFilter),
        ("kind", ChoicesDropdownFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("uuid", "normalized_key", "buyer__username", "buyer__email")
    autocomplete_fields = ("buyer",)

    @admin.display(description=_("应付(元)"), ordering="amount_minor")
    def display_amount_minor(self, obj: OrderItem) -> str:
        return _minor_to_yuan_display(obj.amount_minor)


@admin.register(Order)
class OrderAdmin(BaseModelAdmin):
    ordering = ("-created_at",)
    list_display = (
        "display_order_summary",
        "uuid",
        "buyer",
        "status",
        "display_amount_minor",
        "display_paid_amount_minor",
        "currency",
        "payment_platform",
        "paid_at",
        "created_at",
    )
    list_filter = (
        ("buyer", AutocompleteSelectFilter),
        ("item__kind", ChoicesDropdownFilter),
        ("status", ChoicesDropdownFilter),
        ("payment_platform", ChoicesDropdownFilter),
        ("created_at", RangeDateTimeFilter),
    )
    search_fields = ("uuid", "buyer__username", "buyer__email")
    autocomplete_fields = ("buyer", "item")
    readonly_fields = ("uuid", "created_at", "updated_at", "view_wechat_order_link")
    fieldsets = (
        (
            None,
            {
                "fields": (
                    "buyer",
                    "item",
                    "status",
                    "payment_platform",
                    ("amount_minor", "paid_amount_minor", "currency"),
                    ("paid_at", "closed_at"),
                )
            },
        ),
        (_("微信支付"), {"fields": ("view_wechat_order_link",)}),
        (_("时间戳"), {"fields": ("uuid", "created_at", "updated_at")}),
    )

    @admin.display(description=_("应付(元)"), ordering="amount_minor")
    def display_amount_minor(self, obj: Order) -> str:
        return _minor_to_yuan_display(obj.amount_minor)

    @admin.display(description=_("实收(元)"), ordering="paid_amount_minor")
    def display_paid_amount_minor(self, obj: Order) -> str:
        return _minor_to_yuan_display(obj.paid_amount_minor)

    @admin.display(description=_("微信支付订单"))
    def view_wechat_order_link(self, obj: Order | None) -> str:
        if obj is None or not getattr(obj, "pk", None):
            return "-"
        if obj.payment_platform not in (
            Order.PAYMENT_PLATFORM_WECHATPAY_JSAPI,
            Order.PAYMENT_PLATFORM_WECHATPAY_NATIVE,
            Order.PAYMENT_PLATFORM_WECHATPAY_XPAY,
        ):
            return "-"
        from wechat.models import WechatOrder

        wo = WechatOrder.objects.filter(order=obj).first()
        if wo is None:
            return "-"
        url = reverse("admin:wechat_wechatorder_change", args=[wo.pk])
        return format_html(
            '<a href="{}" class="border border-base-200 bg-white font-medium px-2.5 py-1.5 rounded-md '
            'shadow-sm text-gray-700 text-xs hover:bg-gray-50 dark:bg-gray-800 dark:border-gray-600 '
            'dark:text-gray-200 dark:hover:bg-gray-700">{}</a>',
            url,
            _("打开微信支付订单"),
        )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related("item", "buyer")

    @admin.display(description=_("订单摘要"), ordering="uuid")
    def display_order_summary(self, obj: Order) -> str:
        try:
            return obj.item.admin_summary_line()
        except Exception:
            return str(obj.uuid)

    def lookup_allowed(self, lookup: str, value: str, request: HttpRequest | None = None) -> bool:
        if lookup in ("item__kind__exact", "item__kind"):
            return True
        return super().lookup_allowed(lookup, value, request)


@admin.register(Refund)
class RefundAdmin(BaseModelAdmin):
    ordering = ("-created_at",)
    list_display = ("uuid", "order", "refund_amount_minor", "status", "created_at")
    list_filter = (("status", ChoicesDropdownFilter), ("created_at", RangeDateTimeFilter))
    search_fields = ("uuid", "order__uuid")
    autocomplete_fields = ("order",)
