"""与 hksd/backend 一致的独立事务日志门面；落库 `system.models.Log`。"""

from __future__ import annotations

import logging
import sys
import traceback
from functools import wraps

from django.db import transaction

from system.models import Log as LogModel

_logger = logging.getLogger(__name__)


def tb_for_log(exc: BaseException | None = None) -> str:
    """
    写入 Log.content 时附加的 traceback / 栈：优先 ``exc`` 的链；否则当前 ``sys.exc_info()``；
    若均无活动异常则附加 ``format_stack``（便于非 except 分支的告警定位）。
    """

    if exc is not None and exc.__traceback__ is not None:
        return "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    if sys.exc_info()[0] is not None:
        return traceback.format_exc()
    parts = traceback.format_stack(limit=50)
    if parts:
        parts = parts[:-1]
    return "\n" + "".join(parts)


def atomic_log(func):
    """
    确保日志写入使用独立 atomic，避免随外层业务事务回滚而丢失。
    """

    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            with transaction.atomic():
                return func(*args, **kwargs)
        except Exception as e:
            _logger.exception("Error saving system.Log: %s", e)

    return wrapper


class Log:
    """用法: ``Log.info("标题", "内容", module=LogModel.Module.ORDER)`` 或 ``module="order"``。"""

    @classmethod
    @atomic_log
    def _log(cls, level: str, title: str, content: str, module: str):
        return LogModel.objects.create(level=level, title=title, content=content, module=module)

    @classmethod
    def info(cls, title: str, content: str, module: str):
        return cls._log(LogModel.Level.INFO, title, content, module)

    @classmethod
    def warn(cls, title: str, content: str, module: str):
        return cls._log(LogModel.Level.WARNING, title, content, module)

    @classmethod
    def error(cls, title: str, content: str, module: str):
        return cls._log(LogModel.Level.ERROR, title, content, module)

    warning = warn
    err = error
    info_log = info
    warn_log = warn
    error_log = error
