from rest_framework import serializers
from catalog.models import Product
from .models import Stock, StockMovement
from django.conf import settings
from decimal import Decimal


class StockSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    # provide product metadata via methods to be robust
    product_name = serializers.SerializerMethodField()
    product_sku = serializers.SerializerMethodField()

    class Meta:
        model = Stock
        fields = [
            "id",
            "uuid",
            "product",
            "product_name",
            "product_sku",
            "quantity_current",
            "minimum",
            "maximum",
            "status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "quantity_current", "status", "created_at", "updated_at"]

    def get_product_name(self, obj) -> str | None:
        try:
            return getattr(obj.product, 'name', None) or None
        except Exception:
            return None

    def get_product_sku(self, obj) -> str | None:
        try:
            return getattr(obj.product, 'sku', None) or None
        except Exception:
            return None


class StockMovementSerializer(serializers.ModelSerializer):
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = StockMovement
        fields = [
            "id",
            "uuid",
            "product",
            "type",
            "quantity",
            "reference",
            "note",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "created_at", "updated_at"]

    def validate(self, attrs):
        product = attrs.get("product")
        mtype = attrs.get("type")
        qty = attrs.get("quantity")
        if product is None or mtype is None or qty is None:
            return attrs
        try:
            current = Stock.objects.get(product=product).quantity_current
        except Stock.DoesNotExist:
            current = Decimal("0")
        if mtype == "ENTRADA":
            new_qty = current + qty
        elif mtype == "SAIDA":
            new_qty = current - qty
        else:  # AJUSTE (signed)
            new_qty = current + qty

        if getattr(settings, "PREVENT_NEGATIVE_STOCK", True) and new_qty < 0:
            raise serializers.ValidationError({"quantity": "Operação resultaria em estoque negativo."})
        return attrs
