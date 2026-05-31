from django.templatetags.static import static
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _


UNFOLD = {
    "SITE_TITLE": "项目管理系统",
    "SITE_HEADER": "项目管理系统",
    "SITE_SUBHEADER": "基于 Django 和 Unfold 的现代化后台管理系统",
    "SITE_URL": "/",
    "SITE_SYMBOL": "hub",
    "SITE_FAVICONS": [
        {
            "rel": "icon",
            "sizes": "32x32",
            "type": "image/svg+xml",
            "href": lambda request: static("favicon.svg"),
        },
    ],
    "SHOW_HISTORY": True,
    "SHOW_VIEW_ON_SITE": False,
    "SHOW_BACK_BUTTON": True,
    "THEME": "light",
    "LOGIN": {
        "image": lambda request: static("sample/login-bg.jpg"),
        "redirect_after": lambda request: reverse_lazy("admin:index"),
    },
    "STYLES": [
        lambda request: static("css/styles.min.css"),
        lambda request: static("jquery-ui/jquery-ui.min.css"),
        lambda request: static("jquery-ui/jquery-ui.structure.min.css"),
        lambda request: static("jquery-ui/jquery-ui.theme.min.css"),
    ],
    "SCRIPTS": [
        lambda request: static("jquery/jquery-3.7.1.min.js"),
        lambda request: static("js/script.js"),
        lambda request: static("jquery-ui/jquery-ui.min.js"),
    ],
    "BORDER_RADIUS": "4px",
    "COLORS": {
        "base": {
            "50": "249, 250, 251",
            "100": "243, 244, 246",
            "200": "229, 231, 235",
            "300": "209, 213, 219",
            "400": "156, 163, 175",
            "500": "107, 114, 128",
            "600": "75, 85, 99",
            "700": "55, 65, 81",
            "800": "31, 41, 55",
            "900": "17, 24, 39",
            "950": "3, 7, 18",
        },
        "primary": {
            "50": "239, 246, 255",
            "100": "219, 234, 254",
            "200": "191, 219, 254",
            "300": "147, 197, 253",
            "400": "96, 165, 250",
            "500": "59, 130, 246",
            "600": "37, 99, 235",
            "700": "29, 78, 216",
            "800": "30, 64, 175",
            "900": "30, 58, 138",
            "950": "23, 37, 84",
        },
        "font": {
            "subtle-light": "var(--color-base-500)",
            "subtle-dark": "var(--color-base-400)",
            "default-light": "var(--color-base-600)",
            "default-dark": "var(--color-base-300)",
            "important-light": "var(--color-base-900)",
            "important-dark": "var(--color-base-100)",
        },
    },
    "SIDEBAR": {
        "navigation": [
            {
                "title": _("用户系统"),
                "collapsible": False,
                "items": [
                    {
                        "title": _("用户"),
                        "icon": "person",
                        "link": reverse_lazy("admin:auth_user_changelist"),
                    },
                    {
                        "title": _("用户组"),
                        "icon": "group",
                        "link": reverse_lazy("admin:auth_group_changelist"),
                    },
                ],
            },
            {
                "title": _("系统"),
                "separator": True,
                "collapsible": True,
                "collapsed": True,
                "items": [
                    {
                        "title": _("调试令牌"),
                        "icon": "bug_report",
                        "link": reverse_lazy("admin:authtoken_tokenproxy_changelist"),
                    },
                    {
                        "title": _("生效令牌"),
                        "icon": "check_circle",
                        "link": reverse_lazy("admin:token_blacklist_outstandingtoken_changelist"),
                    },
                    {
                        "title": _("失效令牌"),
                        "icon": "block",
                        "link": reverse_lazy("admin:token_blacklist_blacklistedtoken_changelist"),
                    },
                    {
                        "title": _("系统设置"),
                        "icon": "settings",
                        "link": reverse_lazy("admin:constance_config_changelist"),
                    },
                ],
            },
        ],
    },
}


def dashboard_callback(request, context):
    """
    Callback to prepare custom variables for index template which is used as dashboard
    template. It can be overridden in application by creating custom admin/index.html.
    """
    return context

