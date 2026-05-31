from django.urls import path

from .views import WechatPayNotifyView, WechatRefundNotifyView

app_name = "wechat"

urlpatterns = [
    path("pay/notify/", WechatPayNotifyView.as_view(), name="pay_notify"),
    path("refund/notify/", WechatRefundNotifyView.as_view(), name="refund_notify"),
]
