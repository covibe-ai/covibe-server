from django.db import models
from django.utils.translation import gettext_lazy as _

from project_name.models import BaseModel


class Log(BaseModel):
    """业务系统日志（独立事务写入，见 system.log.Log）。"""

    class Level(models.TextChoices):
        INFO = "INFO", _("信息")
        WARNING = "WARNING", _("警告")
        ERROR = "ERROR", _("错误")

    class Module(models.TextChoices):
        ORDER = "order", _("订单")
        WECHAT_PAY = "wechat_pay", _("微信支付")
        CREDIT = "credit", _("积分与会员")

    title = models.CharField(_("日志标题"), max_length=255)
    content = models.TextField(_("日志内容"))
    level = models.CharField(
        _("日志级别"),
        max_length=10,
        choices=Level.choices,
        default=Level.INFO,
    )
    module = models.CharField(
        _("模块"),
        max_length=20,
        choices=Module.choices,
        db_index=True,
    )

    class Meta:
        verbose_name = _("系统日志")
        verbose_name_plural = verbose_name
        ordering = ["-created_at"]
        db_table = "system_log"
        indexes = [
            models.Index(fields=["created_at"], name="system_log_created_at_idx"),
            models.Index(fields=["module", "created_at"], name="system_log_module_created_idx"),
        ]

    def __str__(self):
        return f"[{self.get_level_display()}] {self.title}"
