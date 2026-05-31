from rest_framework import serializers

from order.models import Order, OrderItem, Refund


class OrderCreateSerializer(serializers.ModelSerializer):
    kind = serializers.CharField(write_only=True, required=False, default=OrderItem.KIND_GENERIC)
    params = serializers.JSONField(write_only=True, required=False, default=dict)
    amount_minor = serializers.IntegerField(write_only=True, min_value=1)
    payment_platform = serializers.ChoiceField(
        choices=[
            Order.PAYMENT_PLATFORM_WECHATPAY_JSAPI,
            Order.PAYMENT_PLATFORM_WECHATPAY_NATIVE,
        ],
        default=Order.PAYMENT_PLATFORM_WECHATPAY_NATIVE,
        required=False,
    )

    class Meta:
        model = Order
        fields = ("kind", "params", "amount_minor", "payment_platform")

    def create(self, validated_data):
        user = self.context["request"].user
        kind = validated_data.pop("kind")
        params = validated_data.pop("params") or {}
        amount_minor = validated_data.pop("amount_minor")
        payment_platform = validated_data.pop("payment_platform")
        nk = OrderItem.build_normalized_key(kind, params)
        item = OrderItem.objects.create(
            buyer=user,
            kind=kind,
            params=params,
            normalized_key=nk,
            amount_minor=amount_minor,
            original_amount_minor=amount_minor,
            currency="CNY",
        )
        return Order.objects.create(
            buyer=user,
            item=item,
            amount_minor=amount_minor,
            original_amount_minor=amount_minor,
            currency="CNY",
            status=Order.STATUS_PENDING,
            payment_platform=payment_platform,
        )


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = (
            "uuid",
            "kind",
            "params",
            "normalized_key",
            "amount_minor",
            "original_amount_minor",
            "currency",
            "execute_status",
            "created_at",
        )
        read_only_fields = fields


class OrderDetailSerializer(serializers.ModelSerializer):
    item = OrderItemSerializer(read_only=True)

    class Meta:
        model = Order
        fields = (
            "uuid",
            "buyer",
            "status",
            "payment_platform",
            "amount_minor",
            "original_amount_minor",
            "paid_amount_minor",
            "currency",
            "paid_at",
            "closed_at",
            "created_at",
            "updated_at",
            "item",
        )
        read_only_fields = fields


class RefundCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = ("reason",)
        extra_kwargs = {"reason": {"required": False, "allow_blank": True, "default": ""}}


class RefundSerializer(serializers.ModelSerializer):
    class Meta:
        model = Refund
        fields = (
            "uuid",
            "order",
            "refund_amount_minor",
            "status",
            "reason",
            "created_at",
        )
        read_only_fields = fields
