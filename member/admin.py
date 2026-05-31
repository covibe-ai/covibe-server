from django.contrib import admin
from django.utils.translation import gettext_lazy as _

from covibe_server.admin import BaseModelAdmin

from .models import MemberTier, Subscription


@admin.register(MemberTier)
class MemberTierAdmin(BaseModelAdmin):
    list_display = (
        'name', 'price_per_month_minor', 'max_sessions',
        'max_workspaces', 'max_idle_minutes', 'sort_order',
        'is_default',
    )
    list_editable = (
        'price_per_month_minor', 'max_sessions', 'max_workspaces',
        'max_idle_minutes', 'sort_order', 'is_default',
    )
    search_fields = ('name',)
    ordering = ('sort_order', 'created_at')
    list_filter_submit = True


@admin.register(Subscription)
class SubscriptionAdmin(BaseModelAdmin):
    list_display = (
        'user', 'tier', 'started_at', 'expired_at',
        'paid_amount_minor', 'is_active',
    )
    list_filter = ('tier', 'started_at', 'expired_at')
    search_fields = ('user__email', 'user__nickname', 'tier__name')
    readonly_fields = (
        'user', 'tier', 'started_at', 'expired_at',
        'paid_amount_minor', 'uuid', 'created_at', 'updated_at',
    )
    autocomplete_fields = ('user',)

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'tier')