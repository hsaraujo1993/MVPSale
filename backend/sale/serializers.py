from rest_framework import serializers
from decimal import Decimal
from .models import Order, OrderItem, confirm_order, cancel_order
from payment.models import PaymentMethod
from catalog.models import Product
from people.models import Seller, Customer


class OrderItemSerializer(serializers.ModelSerializer):
    # Aceitar produto por PK numérica
    id = serializers.IntegerField(read_only=True)
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())

    class Meta:
        model = OrderItem
        fields = [
            "id",
            "uuid",
            "product",
            "quantity",
            "unit_price",
            "discount_percent",
            "discount_value",
            "line_total",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "discount_value", "line_total", "created_at", "updated_at"]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    # Aceitar relações por PK numérica conforme testes
    id = serializers.IntegerField(read_only=True)
    customer = serializers.PrimaryKeyRelatedField(queryset=Customer.objects.all(), required=False, allow_null=True)
    seller = serializers.PrimaryKeyRelatedField(queryset=Seller.objects.all())
    payment_method = serializers.PrimaryKeyRelatedField(queryset=PaymentMethod.objects.all(), required=False, allow_null=True)
    order_type = serializers.CharField(required=False)
    sales_order = serializers.CharField(read_only=True)
    subtotal = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    order_discount_abs = serializers.DecimalField(max_digits=12, decimal_places=2, required=False)
    payment_metadata = serializers.JSONField(required=False, allow_null=True)

    class Meta:
        model = Order
        fields = [
            "id",
            "uuid",
            "customer",
            "seller",
            "status",
            "order_type",
            "sales_order",
            "subtotal",
            "total",
            "discount_total",
            "payment_method",
            "payment_metadata",
            "order_discount_abs",
            "items",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "uuid", "status", "total", "discount_total", "created_at", "updated_at", "subtotal"]

    def update(self, instance, validated_data):
        # Prevent changing payment_method if not in DRAFT
        new_pm = validated_data.get("payment_method", instance.payment_method)
        if instance.status != "DRAFT" and instance.payment_method_id != (new_pm.id if new_pm else None):
            raise serializers.ValidationError({"payment_method": "Não é permitido alterar o método de pagamento após confirmação."})
        # Allow setting payment_metadata and order_discount_abs in DRAFT only
        if instance.status != "DRAFT" and ("payment_metadata" in validated_data or "order_discount_abs" in validated_data):
            raise serializers.ValidationError({"non_field_errors": "Não é permitido alterar metadados de pagamento ou desconto após confirmação."})
        return super().update(instance, validated_data)

    # No extra validation required; SlugRelatedField ensures correct mapping
    def validate_seller(self, value: Seller):
        return value

    def validate_order_type(self, value: str):
        if not value:
            return "carrinho"
        v = str(value).strip().lower()
        if v not in ("carrinho", "orcamento"):
            raise serializers.ValidationError("order_type deve ser 'carrinho' ou 'orcamento'.")
        return v

    def validate_payment_metadata(self, value):
        """Normalize payment_metadata coming from frontend.

        Ensures fee_percent is present (defaults to 0), converted to a string with 2 decimals
        to avoid JSON serialization issues with Decimal in DB drivers.
        Also ensures installments is an int when present.
        """
        if value is None:
            return None
        meta = dict(value)
        # fee_percent may come as string or number; normalize to 2 decimal string
        try:
            fp = meta.get('fee_percent', 0)
            from decimal import Decimal, InvalidOperation
            fp_dec = Decimal(str(fp or 0))
            fp_dec = fp_dec.quantize(Decimal('0.01'))
            # store as string to preserve precision in JSONField
            meta['fee_percent'] = format(fp_dec, 'f')
        except Exception:
            meta['fee_percent'] = '0.00'
        # fee_value (absolute) may be provided by frontend; normalize to 2 decimal string
        try:
            fv = meta.get('fee_value', None)
            if fv is not None:
                from decimal import Decimal
                fv_dec = Decimal(str(fv or 0))
                fv_dec = fv_dec.quantize(Decimal('0.01'))
                meta['fee_value'] = format(fv_dec, 'f')
        except Exception:
            meta.pop('fee_value', None)
        # installments -> int
        try:
            if 'installments' in meta and meta['installments'] is not None:
                meta['installments'] = int(meta['installments'])
        except Exception:
            meta.pop('installments', None)
        # card_brand keep as-is
        return meta


class AddItemSerializer(serializers.Serializer):
    # Aceitar produto por PK numérica
    product = serializers.PrimaryKeyRelatedField(queryset=Product.objects.all())
    quantity = serializers.DecimalField(max_digits=12, decimal_places=3)
    unit_price = serializers.DecimalField(max_digits=12, decimal_places=2)
    discount_percent = serializers.DecimalField(max_digits=5, decimal_places=2, required=False, default=Decimal("0"))


class OrderActionSerializer(serializers.Serializer):
    action = serializers.ChoiceField(choices=["confirm", "cancel"])
