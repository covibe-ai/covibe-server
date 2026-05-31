import logging

from django.http import JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from .api import WechatAPI, WechatAPIException
from .models import WechatPayTransaction
from system.log import Log, tb_for_log
from system.models import Log as LogModel

logger = logging.getLogger(__name__)


def _notify_headers(request):
    m = request.META
    return {
        "Wechatpay-Signature": m.get("HTTP_WECHATPAY_SIGNATURE", ""),
        "Wechatpay-Timestamp": m.get("HTTP_WECHATPAY_TIMESTAMP", ""),
        "Wechatpay-Nonce": m.get("HTTP_WECHATPAY_NONCE", ""),
        "Wechatpay-Serial": m.get("HTTP_WECHATPAY_SERIAL", ""),
    }


@method_decorator(csrf_exempt, name="dispatch")
class WechatPayNotifyView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        raw = request.body.decode("utf-8")
        headers = _notify_headers(request)
        try:
            body = WechatAPI().verify_and_decrypt_notify(headers, raw)
            WechatPayTransaction.apply_query_or_notify_body(
                body, source=WechatPayTransaction.SOURCE_NOTIFY
            )
        except WechatAPIException as exc:
            Log.error(
                "微信支付回调：业务异常",
                f"{exc}\nraw_prefix={raw[:800]}\n\n{tb_for_log(exc)}",
                LogModel.Module.WECHAT_PAY,
            )
            return JsonResponse({"code": "FAIL", "message": str(exc)[:180]}, status=200)
        except Exception:
            logger.exception("微信支付回调处理失败")
            tb = tb_for_log()
            Log.error("微信支付回调：处理失败", tb, LogModel.Module.WECHAT_PAY)
            Log.error("微信支付回调：处理失败（订单域）", tb, LogModel.Module.ORDER)
            return JsonResponse({"code": "FAIL", "message": "internal error"}, status=200)
        return JsonResponse({"code": "SUCCESS", "message": "成功"})


@method_decorator(csrf_exempt, name="dispatch")
class WechatRefundNotifyView(APIView):
    authentication_classes = []
    permission_classes = [AllowAny]

    def post(self, request):
        # 退款流程后续补充；先保持回调可用并验签/解密通过
        raw = request.body.decode("utf-8")
        headers = _notify_headers(request)
        try:
            WechatAPI().verify_and_decrypt_notify(headers, raw)
        except WechatAPIException as exc:
            Log.error(
                "微信退款回调：业务异常",
                f"{exc}\nraw_prefix={raw[:800]}\n\n{tb_for_log(exc)}",
                LogModel.Module.WECHAT_PAY,
            )
            return JsonResponse({"code": "FAIL", "message": str(exc)[:180]}, status=200)
        except Exception:
            logger.exception("微信退款回调处理失败")
            tb = tb_for_log()
            Log.error("微信退款回调：处理失败", tb, LogModel.Module.WECHAT_PAY)
            Log.error("微信退款回调：处理失败（订单域）", tb, LogModel.Module.ORDER)
            return JsonResponse({"code": "FAIL", "message": "internal error"}, status=200)
        return JsonResponse({"code": "SUCCESS", "message": "成功"})
