from __future__ import annotations

import logging
import traceback
from datetime import timedelta
from io import StringIO

from celery import shared_task
from constance import config
from django.utils import timezone

from order.models import Order
from system.log import Log
from system.models import Log as LogModel

logger = logging.getLogger(__name__)


@shared_task(bind=True, soft_time_limit=50, time_limit=55)
def auto_close_expired_orders(self):
    """
    定时关闭超时未支付订单：
    1. 仅处理 PENDING 状态订单
    2. created_at + WECHAT_PAY_NATIVE_EXPIRE_MINUTES 到期后触发
    3. 调用统一的 order.make_closed()，复用查单/关单逻辑
    """
    expire_minutes = int(config.WECHAT_PAY_NATIVE_EXPIRE_MINUTES or 15)
    now = timezone.now()
    expire_before = now - timedelta(minutes=expire_minutes)

    orders = Order.objects.filter(
        status=Order.STATUS_PENDING,
        created_at__lte=expire_before,
    ).only("id", "uuid", "status", "created_at")

    checked = orders.count()
    closed = 0
    for order in orders.iterator():
        try:
            before = order.status
            order.make_closed()
            order.refresh_from_db(fields=["status"])
            if before != order.status and order.status == Order.STATUS_CLOSED:
                closed += 1
        except Exception:
            logger.exception("自动关单失败 order=%s", order.uuid)
            buf = StringIO()
            traceback.print_exc(file=buf)
            Log.error(
                "定时任务：自动关单失败",
                f"order={order.uuid}\n{buf.getvalue()}",
                LogModel.Module.ORDER,
            )

    if closed:
        Log.info(
            "定时任务：自动关单完成",
            f"扫描 {checked} 笔，关闭 {closed} 笔",
            LogModel.Module.ORDER,
        )

    return {"checked": checked, "closed": closed}
