from django.utils.translation import gettext_lazy as _
from unfold.contrib.constance.settings import UNFOLD_CONSTANCE_ADDITIONAL_FIELDS

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_DATABASE_CACHE_BACKEND = None

CONSTANCE_ADDITIONAL_FIELDS = {
    **UNFOLD_CONSTANCE_ADDITIONAL_FIELDS,

    # 示例：选择字段配置
    "choice_field": [
        "django.forms.fields.ChoiceField",
        {
            "widget": "unfold.widgets.UnfoldAdminSelectWidget",
            "choices": (
                ("light-blue", "Light blue"),
                ("dark-blue", "Dark blue"),
            ),
        },
    ],
}

CONSTANCE_CONFIG = {
    # 在这里添加你的配置项
    # 'EXAMPLE_CONFIG': ('default_value', _('配置说明'), str),
}

CONSTANCE_CONFIG_FIELDSETS = {
    # 在这里组织配置项到不同的字段集
    # '示例配置组': (
    #     'EXAMPLE_CONFIG',
    # ),
}

