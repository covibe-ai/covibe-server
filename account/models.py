from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from covibe_server.models import BaseModel


class User(AbstractUser, BaseModel):
    """用户模型。
    
    登录标识统一用 email（USERNAME_FIELD）。
    手机号用户：通过 phone 字段关联，django 后台用 email 管理。
    第三方登录用户：通过 SocialLogin 表关联，登录时会自动生成 email。
    """
    username = None
    email = models.EmailField(_("邮箱"), unique=True)
    phone = models.CharField(_("手机号"), max_length=20, blank=True, default="", db_index=True)
    phone_verified = models.BooleanField(_("手机已验证"), default=False)
    nickname = models.CharField(_("昵称"), max_length=128, blank=True, default="")
    avatar = models.URLField(_("头像"), blank=True, default="")

    # 配额覆盖（null = 用会员等级的默认值）
    max_sessions_override = models.IntegerField(_("最大 session 数(覆盖)"), null=True, blank=True)
    max_workspaces_override = models.IntegerField(_("最大 workspace 数(覆盖)"), null=True, blank=True)

    def __init__(self, *args, **kwargs):
        kwargs.pop('username', None)
        super().__init__(*args, **kwargs)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []

    class Meta:
        verbose_name = _("用户")
        verbose_name_plural = _("用户")
        db_table = "account_user"
        ordering = ["-date_joined"]

    def __str__(self):
        return self.nickname or self.email or self.phone or str(self.uuid)

    @property
    def active_subscription(self):
        """当前有效的会员订阅（未过期、正在进行的）。"""
        now = timezone.now()
        return self.subscriptions.filter(
            started_at__lte=now, expired_at__gte=now
        ).select_related('tier').first()

    @property
    def effective_max_sessions(self):
        if self.max_sessions_override is not None:
            return self.max_sessions_override
        sub = self.active_subscription
        if sub:
            return sub.tier.max_sessions
        return 1

    @property
    def effective_max_workspaces(self):
        if self.max_workspaces_override is not None:
            return self.max_workspaces_override
        sub = self.active_subscription
        if sub:
            return sub.tier.max_workspaces
        return 1

    @property
    def effective_idle_minutes(self):
        sub = self.active_subscription
        if sub:
            return sub.tier.max_idle_minutes
        return 30


class SocialLogin(BaseModel):
    """第三方登录绑定。一个用户可以有多个社交账号。"""
    user = models.ForeignKey(
        User, on_delete=models.CASCADE,
        related_name="social_logins",
        verbose_name=_("用户"),
    )
    provider = models.CharField(_("登录源"), max_length=32, db_index=True,
        help_text=_("如 google, github, wechat, apple, email"))
    sub = models.CharField(_("外部用户 ID"), max_length=512, db_index=True)
    username = models.CharField(_("外部用户名"), max_length=256, blank=True, default="")
    avatar_url = models.URLField(_("外部头像"), blank=True, default="")

    class Meta:
        verbose_name = _("第三方登录")
        verbose_name_plural = _("第三方登录")
        db_table = "account_social_login"
        unique_together = [("provider", "sub")]
        indexes = [
            models.Index(fields=["provider", "sub"], name="social_provider_sub_idx"),
        ]

    def __str__(self):
        return f"[{self.provider}] {self.username or self.sub}"


class WeixinUser(BaseModel):
    """微信用户 OpenID（微信支付 JSAPI 预下单必需）。"""

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        related_name="weixin_user",
        null=True, blank=True, default=None,
        verbose_name=_("用户"),
    )
    openid = models.CharField(_("OpenID"), max_length=128, unique=True, db_index=True)
    unionid = models.CharField(_("UnionID"), max_length=128, default="", blank=True, db_index=True)

    class Meta:
        verbose_name = _("微信用户")
        verbose_name_plural = _("微信用户")
        db_table = "account_weixinuser"

    def __str__(self):
        return self.openid
