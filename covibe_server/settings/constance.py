from django.utils.translation import gettext_lazy as _
from unfold.contrib.constance.settings import UNFOLD_CONSTANCE_ADDITIONAL_FIELDS

CONSTANCE_BACKEND = 'constance.backends.database.DatabaseBackend'
CONSTANCE_DATABASE_CACHE_BACKEND = None

CONSTANCE_ADDITIONAL_FIELDS = {
    **UNFOLD_CONSTANCE_ADDITIONAL_FIELDS,
    str: [
        "django.forms.CharField",
        {
            "widget": "unfold.widgets.UnfoldAdminTextInputWidget",
            "required": False,
        },
    ],
    "password_input": [
        "django.forms.fields.CharField",
        {
            "widget": "unfold.widgets.UnfoldAdminPasswordWidget",
            "widget_kwargs": {"render_value": True},
            "required": False,
        },
    ],
    "area_input": [
        "django.forms.fields.CharField",
        {
            "widget": "unfold.widgets.UnfoldAdminTextareaWidget",
            "required": False,
        },
    ],
}

CONSTANCE_CONFIG = {
    'WECHAT_APP_ID': ('', _('微信登录 AppID（JSAPI 支付 AppID 可回退到此值）'), str),
    'WECHAT_APP_SECRET': ('', _('微信登录 AppSecret'), str),
    'WECHAT_PAY_APP_ID': ('', _('支付用 AppID（留空则用 WECHAT_APP_ID）'), str),
    'WECHAT_PAY_MCH_ID': ('', _('微信支付商户号'), str),
    'WECHAT_PAY_SERIAL_NO': ('', _('商户 API 证书序列号'), str),
    'WECHAT_PAY_PRIVATE_KEY': ('', _('商户 API 证书私钥 PEM'), 'area_input'),
    'WECHAT_PAY_API_V3_KEY': ('', _('API v3 密钥（32 字节）'), 'password_input'),
    'WECHAT_PAY_VERIFY_PUBLIC_KEY_PEM': ('', _('微信支付验签公钥 PEM'), 'area_input'),
    'WECHAT_PAY_VERIFY_KEY_ID': ('', _('微信支付验签公钥 ID'), str),
    'WECHAT_PAY_NOTIFY_URL': ('', _('支付回调 URL（留空则用 BASE_URL 自动拼接）'), str),
    'WECHAT_PAY_REFUND_NOTIFY_URL': ('', _('退款回调 URL（留空则用 BASE_URL 自动拼接）'), str),
    'WECHAT_PAY_ORDER_BODY_PREFIX': ('DjangoStartupKit', _('微信支付商品描述前缀'), str),
    'WECHAT_PAY_NATIVE_EXPIRE_MINUTES': (15, _('Native 订单超时分钟数（自动关单）'), int),

    # ---- 会员默认配额 ----
    'DEFAULT_TIER_FREE_MAX_SESSIONS': (10, _('免费版默认最大会话数'), int),
    'DEFAULT_TIER_FREE_MAX_WORKSPACES': (3, _('免费版默认最大工作区数'), int),
    'DEFAULT_TIER_FREE_MAX_IDLE_MINUTES': (30, _('免费版默认最大空闲分钟数'), int),
    'DEFAULT_TIER_PRO_MAX_SESSIONS': (50, _('Pro 版默认最大会话数'), int),
    'DEFAULT_TIER_PRO_MAX_WORKSPACES': (10, _('Pro 版默认最大工作区数'), int),
    'DEFAULT_TIER_PRO_MAX_IDLE_MINUTES': (120, _('Pro 版默认最大空闲分钟数'), int),
    'DEFAULT_TIER_ENTERPRISE_MAX_SESSIONS': (200, _('企业版默认最大会话数'), int),
    'DEFAULT_TIER_ENTERPRISE_MAX_WORKSPACES': (50, _('企业版默认最大工作区数'), int),
    'DEFAULT_TIER_ENTERPRISE_MAX_IDLE_MINUTES': (1440, _('企业版默认最大空闲分钟数（1440 = 24 小时）'), int),
}

CONSTANCE_CONFIG_FIELDSETS = {
    '微信登录': (
        'WECHAT_APP_ID',
        'WECHAT_APP_SECRET',
    ),
    '微信支付': (
        'WECHAT_PAY_APP_ID',
        'WECHAT_PAY_MCH_ID',
        'WECHAT_PAY_SERIAL_NO',
        'WECHAT_PAY_PRIVATE_KEY',
        'WECHAT_PAY_API_V3_KEY',
        'WECHAT_PAY_VERIFY_PUBLIC_KEY_PEM',
        'WECHAT_PAY_VERIFY_KEY_ID',
        'WECHAT_PAY_NOTIFY_URL',
        'WECHAT_PAY_REFUND_NOTIFY_URL',
        'WECHAT_PAY_ORDER_BODY_PREFIX',
        'WECHAT_PAY_NATIVE_EXPIRE_MINUTES',
    ),
    '会员默认配额': (
        'DEFAULT_TIER_FREE_MAX_SESSIONS',
        'DEFAULT_TIER_FREE_MAX_WORKSPACES',
        'DEFAULT_TIER_FREE_MAX_IDLE_MINUTES',
        'DEFAULT_TIER_PRO_MAX_SESSIONS',
        'DEFAULT_TIER_PRO_MAX_WORKSPACES',
        'DEFAULT_TIER_PRO_MAX_IDLE_MINUTES',
        'DEFAULT_TIER_ENTERPRISE_MAX_SESSIONS',
        'DEFAULT_TIER_ENTERPRISE_MAX_WORKSPACES',
        'DEFAULT_TIER_ENTERPRISE_MAX_IDLE_MINUTES',
    ),
}
