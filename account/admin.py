from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from covibe_server.admin import BaseModelAdmin, BaseTabularInline

from .models import WeixinUser

User = get_user_model()


class WeixinUserInline(BaseTabularInline):
    model = WeixinUser
    fk_name = 'user'
    extra = 0
    max_num = 1
    can_delete = True
    fields = ('openid', 'unionid', 'uuid', 'created_at')
    readonly_fields = ('uuid', 'created_at')
    autocomplete_fields = ()
    verbose_name = _('微信用户')
    verbose_name_plural = _('微信用户')


@admin.register(User)
class UserAdmin(BaseUserAdmin, BaseModelAdmin):
    form = UserChangeForm
    add_form = UserCreationForm
    change_password_form = AdminPasswordChangeForm

    list_display = (
        'email', 'nickname', 'is_active', 'is_staff', 'created_at',
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'nickname', 'oidc_sub', 'uuid')
    ordering = ('-created_at',)
    list_filter_submit = True

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        (_('个人信息'), {'fields': ('nickname', 'avatar')}),
        (_('OIDC 认证'), {
            'fields': ('oidc_sub', 'oidc_issuer', 'oidc_provider'),
            'classes': ('collapse',),
        }),
        (_('额度覆盖'), {
            'fields': ('max_sessions_override', 'max_workspaces_override'),
            'classes': ('collapse',),
        }),
        (_('权限'), {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'classes': ('collapse',),
        }),
        (_('重要日期'), {
            'fields': ('last_login', 'date_joined', 'created_at', 'updated_at'),
            'classes': ('collapse',),
        }),
    )
    readonly_fields = ('created_at', 'updated_at', 'last_login', 'date_joined')

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'nickname', 'password1', 'password2'),
        }),
    )

    inlines = [WeixinUserInline]

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tier')


@admin.register(WeixinUser)
class WeixinUserAdmin(BaseModelAdmin):
    list_display = ('uuid', 'user', 'openid', 'unionid', 'created_at')
    search_fields = ('openid', 'unionid', 'user__email')
    autocomplete_fields = ('user',)
    raw_id_fields = ('user',)