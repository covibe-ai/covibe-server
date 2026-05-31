from datetime import timezone

from django.contrib.auth import get_user_model
from django.db import models
from django.utils.translation import gettext_lazy as _

from covibe_server.models import BaseModel

User = get_user_model()


class MemberTier(BaseModel):
    """会员等级配置。"""

    name = models.CharField(
        _('等级名称'),
        max_length=64,
        unique=True,
    )
    price_per_month_minor = models.BigIntegerField(
        _('月费（分）'),
        default=0,
        help_text=_('单位为分（1 元 = 100 分），免费为 0'),
    )
    max_sessions = models.IntegerField(
        _('最大会话数'),
        default=10,
    )
    max_workspaces = models.IntegerField(
        _('最大工作区数'),
        default=3,
    )
    max_idle_minutes = models.IntegerField(
        _('最大空闲分钟数'),
        default=30,
        help_text=_('超过此空闲时间将自动断开连接'),
    )
    sort_order = models.IntegerField(
        _('排序'),
        default=0,
        help_text=_('数字越小越靠前'),
    )
    is_default = models.BooleanField(
        _('默认等级'),
        default=False,
        help_text=_('新用户默认分配的等级'),
    )

    class Meta:
        verbose_name = _('会员等级')
        verbose_name_plural = _('会员等级')
        db_table = 'member_tier'
        ordering = ('sort_order', 'created_at')

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        # 确保只有一个默认等级
        if self.is_default:
            MemberTier.objects.filter(is_default=True).exclude(
                uuid=self.uuid if self.uuid else ''
            ).update(is_default=False)
        super().save(*args, **kwargs)


class Subscription(BaseModel):
    """用户订阅记录。"""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='subscriptions',
        verbose_name=_('用户'),
    )
    tier = models.ForeignKey(
        MemberTier,
        on_delete=models.PROTECT,
        related_name='subscriptions',
        verbose_name=_('会员等级'),
    )
    started_at = models.DateTimeField(
        _('开始时间'),
        db_index=True,
    )
    expired_at = models.DateTimeField(
        _('到期时间'),
        db_index=True,
    )
    paid_amount_minor = models.BigIntegerField(
        _('支付金额（分）'),
        default=0,
        help_text=_('单位为分（1 元 = 100 分）'),
    )

    class Meta:
        verbose_name = _('订阅记录')
        verbose_name_plural = _('订阅记录')
        db_table = 'member_subscription'
        ordering = ('-created_at',)

    def __str__(self):
        return f'{self.user} - {self.tier}'

    @property
    def is_active(self) -> bool:
        """订阅是否在有效期内。"""
        now = timezone.now()
        return self.started_at <= now <= self.expired_at