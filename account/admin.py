from django.contrib import admin

from project_name.admin import BaseModelAdmin

from .models import WeixinUser


@admin.register(WeixinUser)
class WeixinUserAdmin(BaseModelAdmin):
    list_display = ('uuid', 'user', 'openid', 'unionid', 'created_at')
    search_fields = ('openid', 'unionid', 'user__username')
    autocomplete_fields = ('user',)
