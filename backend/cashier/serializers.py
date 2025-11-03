from rest_framework import serializers
from .models import CashierSession, CashMovement


class CashierSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashierSession
        fields = [
            "uuid",
            "opened_by",
            "closed_by",
            "opened_at",
            "closed_at",
            "opening_amount",
            "closing_amount",
            "expected_amount",
            "difference",
            "status",
            "notes",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "uuid",
            "closed_by",
            "opened_at",
            "closed_at",
            "expected_amount",
            "difference",
            "status",
            "created_at",
            "updated_at",
        ]


class OpenSessionSerializer(serializers.Serializer):
    opening_amount = serializers.DecimalField(max_digits=12, decimal_places=2, required=False, default=0)
    notes = serializers.CharField(required=False, allow_blank=True)


class CloseSessionSerializer(serializers.Serializer):
    closing_amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    notes = serializers.CharField(required=False, allow_blank=True)


class CashMovementSerializer(serializers.ModelSerializer):
    class Meta:
        model = CashMovement
        fields = ["uuid", "session", "type", "amount", "reason", "reference", "created_at"]
        read_only_fields = ["uuid", "created_at"]
