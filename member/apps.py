from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class MemberConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'member'
    verbose_name = _('会员管理')