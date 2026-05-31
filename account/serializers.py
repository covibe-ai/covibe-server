from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    tier_name = serializers.SerializerMethodField()
    tier_display = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'nickname', 'avatar',
            'oidc_sub', 'oidc_issuer', 'oidc_provider',
            'effective_max_sessions', 'effective_max_workspaces',
            'effective_idle_minutes',
            'tier_name', 'tier_display',
            'is_active', 'date_joined',
        ]

    def get_tier_name(self, obj):
        sub = obj.subscriptions.filter(is_active=True).first()
        return sub.tier.name if sub else None

    def get_tier_display(self, obj):
        sub = obj.subscriptions.filter(is_active=True).first()
        return {
            'name': sub.tier.name,
            'expired_at': sub.expired_at.isoformat() if sub and sub.expired_at else None,
        } if sub else None
