from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


def _patch_model_verbose(app_label: str, model_name: str, verbose_name, verbose_name_plural) -> None:
    """与 Unfold 侧栏命名对齐（第三方包内模型无迁移时在此补丁 Meta 展示名）。"""
    from django.apps import apps

    try:
        model = apps.get_model(app_label, model_name)
    except LookupError:
        return
    model._meta.verbose_name = verbose_name
    model._meta.verbose_name_plural = verbose_name_plural


class ProjectNameConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'project_name'

    def ready(self) -> None:
        _patch_model_verbose('auth', 'group', _('用户组'), _('用户组'))
        _patch_model_verbose('django_celery_results', 'taskresult', _('任务结果'), _('任务结果'))
        _patch_model_verbose('django_celery_beat', 'periodictask', _('定时任务'), _('定时任务'))
        _patch_model_verbose('constance', 'constance', _('系统设置'), _('系统设置'))
        _patch_model_verbose('authtoken', 'token', _('调试令牌'), _('调试令牌'))
        _patch_model_verbose('authtoken', 'tokenproxy', _('调试令牌'), _('调试令牌'))
        _patch_model_verbose('token_blacklist', 'outstandingtoken', _('生效令牌'), _('生效令牌'))
        _patch_model_verbose('token_blacklist', 'blacklistedtoken', _('失效令牌'), _('失效令牌'))
