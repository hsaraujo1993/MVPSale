from rest_framework import serializers
from .models import Category, Brand, Product, Promotion


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["uuid", "name", "slug", "active", "created_at", "updated_at"]
        read_only_fields = ["uuid", "slug", "created_at", "updated_at"]


class BrandSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = ["uuid", "name", "active", "created_at", "updated_at"]
        read_only_fields = ["uuid", "created_at", "updated_at"]


class ProductSerializer(serializers.ModelSerializer):
    sale_price = serializers.DecimalField(max_digits=12, decimal_places=2, read_only=True)
    # accept category/brand by uuid on input while keeping uuid in representation
    category = serializers.SlugRelatedField(slug_field='uuid', queryset=Category.objects.all())
    brand = serializers.SlugRelatedField(slug_field='uuid', queryset=Brand.objects.all())

    class Meta:
        model = Product
        fields = [
            "uuid",
            "sku",
            "name",
            "description",
            "category",
            "brand",
            "cost_price",
            "margin",
            "sale_price",
            "barcode",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "sku", "sale_price", "created_at", "updated_at"]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Enriquecimento: lista de objetos { supplier_id, supplier_name, supplier_code }
        try:
            # Import dynamically to avoid static-analysis import errors in environments
            import importlib
            purchase_models = importlib.import_module('purchase.models')
            SupplierProduct = getattr(purchase_models, 'SupplierProduct')
            rows = SupplierProduct.objects.select_related("supplier").filter(product=instance)
            enriched = []
            for sp in rows:
                enriched.append({
                    "supplier_id": getattr(sp.supplier, "uuid", sp.supplier_id),
                    "supplier_name": getattr(sp.supplier, "corporate_name", ""),
                    "supplier_code": sp.supplier_code,
                })
            data["supplier_code"] = enriched
        except Exception:
            data["supplier_code"] = []
        return data

    def validate_margin(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Margem deve estar entre 0 e 100%.")
        return value

    def validate_cost_price(self, value):
        if value < 0:
            raise serializers.ValidationError("Preço de custo não pode ser negativo.")
        return value


class PromotionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Promotion
        fields = [
            "uuid",
            "product",
            "percent_off",
            "start_date",
            "end_date",
            "active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "created_at", "updated_at"]

    

    def validate_percent_off(self, value):
        if value < 0 or value > 100:
            raise serializers.ValidationError("Percentual deve estar entre 0 e 100%.")
        return value

    def validate(self, attrs):
        start = attrs.get("start_date") or getattr(self.instance, "start_date", None)
        end = attrs.get("end_date") or getattr(self.instance, "end_date", None)
        active = attrs.get("active") if "active" in attrs else getattr(self.instance, "active", True)
        product = attrs.get("product") or getattr(self.instance, "product", None)
        if start and end and start > end:
            raise serializers.ValidationError({"end_date": "Data final deve ser maior ou igual à inicial."})
        if active and product:
            qs = Promotion.objects.filter(product=product, active=True)
            if self.instance:
                qs = qs.exclude(pk=self.instance.pk)
            if qs.exists():
                raise serializers.ValidationError({"active": "Já existe promoção ativa para este produto."})
        return attrs
