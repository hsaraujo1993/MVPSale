from rest_framework import serializers
from .models import PaymentMethod, Receivable, PaymentEvent, CardBrand, CardFeeTier


class PaymentMethodSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethod
        fields = [
            "uuid",
            "code",
            "name",
            "type",
            "fee_percent",
            "fee_fixed",
            "auto_settle",
            "settlement_days",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "created_at", "updated_at"]


class ReceivableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receivable
        fields = [
            "uuid",
            "method",
            "reference",
            "external_id",
            "due_date",
            "amount",
            "status",
            "paid_date",
            "paid_amount",
            "fee_amount",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "status", "paid_date", "paid_amount", "fee_amount", "created_at", "updated_at"]


class SettleSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    fee_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    paid_date = serializers.DateField()
    external_id = serializers.CharField(required=False, allow_blank=True)
    metadata = serializers.JSONField(required=False)


class CardBrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardBrand
        fields = ["id", "name", "active", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class CardFeeTierSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardFeeTier
        fields = [
            "id",
            "brand",
            "type",
            "installments_min",
            "installments_max",
            "fee_percent",
            "fee_fixed",
            "settlement_days",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]
