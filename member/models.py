from datetime import timezone

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone
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
        if self.is_default:
            MemberTier.objects.filter(is_default=True).exclude(
                uuid=self.uuid if self.uuid else ''
            ).update(is_default=False)
        super().save(*args, **kwargs)


class Subscription(BaseModel):
    """用户订阅记录。
    
    购买逻辑（在 payment 履约时调用）：
    1. 查找当前用户的 active subscription（started_at <= now <= expired_at）
    2. 如果存在：延长 expired_at（不删除旧的，两个记录都保留，但只有一个 active）
    3. 如果不存在：创建新的 subscription（started_at=now, expired_at=now+天数）
    4. 折抵计算：剩余天数 = (old.expired_at - now).days
                折抵金额 = 剩余天数 * (old.tier.price / 30)
                新金额 = max(0, 新价格 - 折抵金额)
    """

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
        now = timezone.now()
        return self.started_at <= now <= self.expired_at

    @classmethod
    def extend_or_create(cls, user, tier, days: int, amount_minor: int):
        """购买会员。
        
        规则：
        - 只能购买同级或更高级；低级 → 拒绝（调用方拦截）
        - 同级：不折抵，延长原有 expired_at
        - 更高级：旧会员立即到期，新会员立即生效 + 送 1 天
        - 旧记录保留不动（历史追溯用）
        
        Returns:
            (new_subscription, old_subscription_or_None)
        """
        now = timezone.now()
        active = cls.objects.filter(
            user=user, started_at__lte=now, expired_at__gte=now
        ).select_related('tier').first()

        if active:
            old_tier = active.tier
            if tier.sort_order == old_tier.sort_order:
                # 同级：延长
                new_start = active.expired_at
                new_end = active.expired_at + timezone.timedelta(days=days)
                return cls.objects.create(
                    user=user, tier=tier,
                    started_at=new_start, expired_at=new_end,
                    paid_amount_minor=amount_minor,
                ), active
            else:
                # 更高级：旧会员立即到期，新会员立即生效 + 送 1 天
                # active 记录保留（但 expired_at < now 就不再 active）
                new_start = now
                new_end = now + timezone.timedelta(days=days + 1)  # +1 赠送当天
                return cls.objects.create(
                    user=user, tier=tier,
                    started_at=new_start, expired_at=new_end,
                    paid_amount_minor=amount_minor,
                ), active
        else:
            # 无旧会员：新建
            new_start = now
            new_end = now + timezone.timedelta(days=days)
            return cls.objects.create(
                user=user, tier=tier,
                started_at=new_start, expired_at=new_end,
                paid_amount_minor=amount_minor,
            ), None

