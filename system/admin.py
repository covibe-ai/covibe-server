from django.contrib import admin
from django.db import models
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from unfold.contrib.filters.admin import ChoicesDropdownFilter, RangeDateTimeFilter
from unfold.paginator import InfinitePaginator
from unfold.widgets import UnfoldAdminTextareaWidget

from covibe_server.admin import BaseModelAdmin

from system.models import Log


@admin.register(Log)
class LogAdmin(BaseModelAdmin):
    """列表使用 InfinitePaginator，避免大表 COUNT；列表不加载 content 字段以减轻 IO。"""

    compressed_fields = True
    ordering = ("-created_at",)
    list_display = ("get_level_display_colored", "title", "module", "created_at")
    list_filter = (
        ("level", ChoicesDropdownFilter),
        ("module", ChoicesDropdownFilter),
        ("created_at", RangeDateTimeFilter),
    )
    # title 模糊；module / level 精确匹配（短枚举，利于走索引）；大字段 content 不参与搜索
    search_fields = ("title", "=module", "=level")
    readonly_fields = (
        "title",
        "content_display",
        "level",
        "module",
        "uuid",
        "created_at",
        "updated_at",
    )
    fields = ("title", "content_display", "level", "module", "uuid", "created_at", "updated_at")
    paginator = InfinitePaginator
    show_full_result_count = False
    list_per_page = 50
    list_display_links = ("title",)

    formfield_overrides = {
        models.TextField: {"widget": UnfoldAdminTextareaWidget},
    }

    def content_display(self, obj):
        if obj.content:
            return mark_safe(obj.content.replace("\n", "<br>"))
        return ""

    content_display.short_description = "日志内容"

    def get_level_display_colored(self, obj):
        level_text = obj.get_level_display()
        level_colors = {
            "信息": "bg-blue-100 text-blue-600",
            "警告": "bg-yellow-100 text-yellow-600",
            "错误": "bg-red-100 text-red-600",
        }
        color_class = level_colors.get(str(level_text), "")
        return format_html('<span class="px-2 py-1 rounded-full text-sm {}">{}</span>', color_class, level_text)

    get_level_display_colored.short_description = "日志级别"

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        # changelist 不展示 content，推迟加载以降低列表页 IO
        return qs.defer("content")
