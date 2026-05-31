from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _

from covibe_server.models import BaseModel


class User(AbstractUser, BaseModel):
    username = None
    email = models.EmailField(_("邮箱"), unique=True)
    nickname = models.CharField(_("昵称"), max_length=128, blank=True, default="")
    avatar = models.URLField(_("头像"), blank=True, default="")

    oidc_sub = models.CharField(_("OIDC sub"), max_length=512, blank=True, default="", db_index=True)
    oidc_issuer = models.CharField(_("OIDC issuer"), max_length=256, blank=True, default="")
    oidc_provider = models.CharField(_("OIDC provider"), max_length=64, blank=True, default="")

    # tier field removed - computed from active Subscription via property

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
        return self.nickname or self.email

    @property
    def effective_max_sessions(self):
        if self.max_sessions_override is not None:
            return self.max_sessions_override
        if self.tier:
            return self.tier.max_sessions
        return 1

    @property
    def effective_max_workspaces(self):
        if self.max_workspaces_override is not None:
            return self.max_workspaces_override
        if self.tier:
            return self.tier.max_workspaces
        return 1

    @property
    def effective_idle_minutes(self):
        if self.tier:
            return self.tier.max_idle_minutes
        return 30


class WeixinUser(BaseModel):
    """微信用户 OpenID，JSAPI 预下单必需。"""

    user = models.OneToOneField(
        User,
        on_delete=models.SET_NULL,
        related_name="weixin_user",
        null=True, blank=True, default=None,
        verbose_name=_("用户"),
    )
    openid = models.CharField(
        _("OpenID"), max_length=128, unique=True, db_index=True,
    )
    unionid = models.CharField(
        _("UnionID"), max_length=128, default="", blank=True, db_index=True,
    )

    class Meta:
        verbose_name = _("微信用户")
        verbose_name_plural = _("微信用户")
        db_table = "account_weixinuser"

    def __str__(self):
        return self.openid
