from rest_framework import serializers
from decimal import Decimal, InvalidOperation
from .models import PaymentMethod, Receivable, CardBrand, CardFeeTier


class PaymentMethodSerializer(serializers.ModelSerializer):
    # Permitir 3 casas decimais para alinhar com testes (ex.: "0.000")
    id = serializers.IntegerField(read_only=True)
    fee_percent = serializers.DecimalField(max_digits=6, decimal_places=3)

    class Meta:
        model = PaymentMethod
        fields = [
            "id",
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
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]

    def validate_fee_percent(self, value):
        try:
            if isinstance(value, str):
                return Decimal(value.replace(",", "."))
            return value
        except (InvalidOperation, ValueError):
            raise serializers.ValidationError("Valor de fee_percent inválido")


class ReceivableSerializer(serializers.ModelSerializer):
    class Meta:
        model = Receivable
        fields = [
            "id",
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
        read_only_fields = ["id", "uuid", "status", "paid_date", "paid_amount", "fee_amount", "created_at", "updated_at"]


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
    # Explicit DecimalField so we can normalize strings like '1,5' -> Decimal('1.5')
    fee_percent = serializers.DecimalField(max_digits=6, decimal_places=2)
    # include nested brand data in responses for consistent frontend display
    brand_detail = CardBrandSerializer(source='brand', read_only=True)

    class Meta:
        model = CardFeeTier
        fields = [
            "id",
            "brand",
            "brand_detail",
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

    def validate_fee_percent(self, value):
        # Accept strings with comma as decimal separator from frontend (e.g. '1,5')
        try:
            if isinstance(value, str):
                v = value.replace(",", ".")
                return Decimal(v)
            # if already Decimal or numeric, let DRF handle coercion
            return value
        except (InvalidOperation, ValueError):
            raise serializers.ValidationError("Valor de fee_percent inválido")
