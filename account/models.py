from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from covibe_server.models import BaseModel


class WeixinUser(BaseModel):
    """微信用户 OpenID，JSAPI 预下单必需。"""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='weixin_user',
        null=True,
        blank=True,
        default=None,
        verbose_name=_('用户'),
    )
    openid = models.CharField(
        _('OpenID'),
        max_length=128,
        unique=True,
        db_index=True,
    )
    unionid = models.CharField(
        _('UnionID'),
        max_length=128,
        default='',
        blank=True,
        db_index=True,
    )

    class Meta:
        verbose_name = _('微信用户')
        verbose_name_plural = _('微信用户')
        db_table = 'account_weixinuser'

    def __str__(self):
        return self.openid
