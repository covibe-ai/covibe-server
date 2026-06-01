from django.contrib import admin
from django.contrib.auth import get_user_model
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.translation import gettext_lazy as _
from unfold.forms import AdminPasswordChangeForm, UserChangeForm, UserCreationForm

from covibe_server.admin import BaseModelAdmin, BaseTabularInline

from .models import SocialLogin, WeixinUser

User = get_user_model()


class SocialLoginInline(BaseTabularInline):
    model = SocialLogin
    extra = 0
    max_num = 10
    fields = ('provider', 'sub', 'username', 'avatar_url', 'uuid', 'created_at')
    readonly_fields = ('uuid', 'created_at')
    verbose_name = _('第三方登录')
    verbose_name_plural = _('第三方登录')


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
        'email', 'phone', 'nickname', 'is_active', 'is_staff', 'created_at',
    )
    list_filter = ('is_active', 'is_staff', 'is_superuser')
    search_fields = ('email', 'phone', 'nickname', 'uuid')
    ordering = ('-created_at',)
    list_filter_submit = True

    fieldsets = (
        (None, {'fields': ('email', 'phone', 'password')}),
        (_('个人信息'), {'fields': ('nickname', 'avatar', 'phone_verified')}),
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

    inlines = [SocialLoginInline, WeixinUserInline]


@admin.register(SocialLogin)
class SocialLoginAdmin(BaseModelAdmin):
    list_display = ('uuid', 'user', 'provider', 'sub', 'username', 'created_at')
    search_fields = ('provider', 'sub', 'username', 'user__email', 'user__nickname')
    list_filter = ('provider',)
    autocomplete_fields = ('user',)
    raw_id_fields = ('user',)


@admin.register(WeixinUser)
class WeixinUserAdmin(BaseModelAdmin):
    list_display = ('uuid', 'user', 'openid', 'unionid', 'created_at')
    search_fields = ('openid', 'unionid', 'user__email')
    autocomplete_fields = ('user',)
    raw_id_fields = ('user',)
