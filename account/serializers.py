from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    tier = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'uuid', 'email', 'phone', 'nickname', 'avatar',
            'effective_max_sessions', 'effective_max_workspaces',
            'effective_idle_minutes',
            'tier',
            'is_active', 'date_joined',
        ]

    def get_tier(self, obj):
        from django.utils import timezone
        now = timezone.now()
        sub = obj.subscriptions.filter(
            started_at__lte=now, expired_at__gte=now
        ).select_related('tier').first()
        if not sub:
            return None
        return {
            'name': sub.tier.name,
            'expired_at': sub.expired_at.isoformat(),
        }