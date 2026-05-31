from __future__ import annotations

import logging
import time

from django.core.cache import cache
from rest_framework import mixins, status, viewsets
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from account.models import WeixinUser

from order.models import Order
from order.serializers import OrderCreateSerializer, OrderDetailSerializer

from system.log import Log, tb_for_log
from system.models import Log as LogModel

logger = logging.getLogger(__name__)

CHECK_PAYMENT_LOCK_TTL = 15
CHECK_PAYMENT_THROTTLE_SEC = 2.0


class OrderViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Order.objects.filter(buyer=self.request.user).select_related("item")

    def get_serializer_class(self):
        if self.action == "create":
            return OrderCreateSerializer
        return OrderDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = OrderCreateSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        Log.info(
            "订单已创建",
            f"order={order.uuid} buyer={order.buyer_id} item_kind={order.item.kind} "
            f"amount_minor={order.amount_minor} payment_platform={order.payment_platform}",
            LogModel.Module.ORDER,
        )
        return Response(
            OrderDetailSerializer(order).data,
            status=status.HTTP_201_CREATED,
        )

    @action(detail=True, methods=["post"], url_path="pay/wechat/prepay")
    def wechat_prepay(self, request, pk=None):
        order = self.get_object()
        try:
            if order.payment_platform == Order.PAYMENT_PLATFORM_WECHATPAY_JSAPI:
                wx = WeixinUser.objects.get(user=request.user)
                params = order.platform_order.create_prepay(openid=wx.openid)
            elif order.payment_platform == Order.PAYMENT_PLATFORM_WECHATPAY_NATIVE:
                params = order.platform_order.create_prepay()
            else:
                msg = f"order={order.uuid} platform={order.payment_platform}\n\n{tb_for_log()}"
                Log.warn("微信预支付：不支持的支付平台", msg, LogModel.Module.ORDER)
                Log.warn("微信预支付：不支持的支付平台", msg, LogModel.Module.WECHAT_PAY)
                return Response(
                    {"code": "PAYMENT_PLATFORM_NOT_SUPPORTED", "detail": "不支持的支付平台"},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except WeixinUser.DoesNotExist:
            Log.warn(
                "微信预支付：用户未绑定微信",
                f"order={order.uuid} buyer={request.user.pk}\n\n{tb_for_log()}",
                LogModel.Module.ORDER,
            )
            Log.warn(
                "微信预支付：用户未绑定微信",
                f"order={order.uuid} buyer={request.user.pk}\n\n{tb_for_log()}",
                LogModel.Module.WECHAT_PAY,
            )
            return Response(
                {"code": "WECHAT_USER_NOT_BOUND", "detail": "用户未绑定微信"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except ValueError as exc:
            detail = str(exc)
            Log.warn(
                "微信预支付：参数无效",
                f"order={order.uuid} detail={detail}\n\n{tb_for_log()}",
                LogModel.Module.ORDER,
            )
            Log.warn(
                "微信预支付：参数无效",
                f"order={order.uuid} detail={detail}\n\n{tb_for_log()}",
                LogModel.Module.WECHAT_PAY,
            )
            return Response(
                {"code": "PAYMENT_PARAM_INVALID", "detail": detail},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception as exc:
            logger.exception("预支付创建失败")
            tb = tb_for_log()
            Log.error(
                "微信预支付：创建失败",
                f"order={order.uuid}\n{tb}",
                LogModel.Module.ORDER,
            )
            Log.error(
                "微信预支付：创建失败",
                f"order={order.uuid}\n{tb}",
                LogModel.Module.WECHAT_PAY,
            )
            return Response(
                {"code": "WECHAT_PREPAY_CREATE_FAILED", "detail": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(params)

    @action(detail=True, methods=["post"], url_path="check_payment")
    def check_payment(self, request, pk=None):
        """
        按支付平台主动核对渠道支付状态；与回调共用平台侧落库与订单推进逻辑。
        同一订单 2s 内最多触发一次渠道查询（并发用 per-order 分布式锁）。
        不支持的平台返回 400，仍附带当前订单详情（与详情序列化一致）。
        渠道查询失败时记录日志并返回刷新后的订单详情（与 retrieve 相同结构）。
        """
        order = self.get_object()
        lock_key = f"order:check_payment:lock:{order.pk}"
        throttle_key = f"order:check_payment:throttle:{order.pk}"

        def detail_response(o: Order) -> Response:
            fresh = Order.objects.select_related("item").get(pk=o.pk)
            return Response(OrderDetailSerializer(fresh).data)

        if not cache.add(lock_key, "1", timeout=CHECK_PAYMENT_LOCK_TTL):
            return detail_response(order)

        try:
            if not order.supports_active_payment_check:
                fresh = Order.objects.select_related("item").get(pk=order.pk)
                payload = OrderDetailSerializer(fresh).data
                return Response(
                    {
                        "detail": "当前支付平台不支持主动查单",
                        "code": "CHECK_PAYMENT_PLATFORM_NOT_SUPPORTED",
                        "order": payload,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            payment_order = order.platform_order
            if payment_order is None:
                fresh = Order.objects.select_related("item").get(pk=order.pk)
                payload = OrderDetailSerializer(fresh).data
                return Response(
                    {
                        "detail": "当前支付平台不支持主动查单",
                        "code": "CHECK_PAYMENT_PLATFORM_NOT_SUPPORTED",
                        "order": payload,
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

            now = time.time()
            last_raw = cache.get(throttle_key)
            if last_raw is not None:
                try:
                    last_ts = float(last_raw)
                except (TypeError, ValueError):
                    last_ts = 0.0
                if now - last_ts < CHECK_PAYMENT_THROTTLE_SEC:
                    return detail_response(order)

            cache.set(throttle_key, str(now), timeout=120)

            try:
                payment_order.check_payment()
            except Exception:
                logger.warning(
                    "订单查单：支付渠道查询异常 order=%s",
                    order.pk,
                    exc_info=True,
                )

            return detail_response(order)
        finally:
            cache.delete(lock_key)

    @action(detail=True, methods=["post"], url_path="refunds")
    def refunds(self, request, pk=None):
        return Response({"detail": "Refund 本期暂未实现"}, status=status.HTTP_501_NOT_IMPLEMENTED)
