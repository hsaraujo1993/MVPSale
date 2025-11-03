from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import Customer, Supplier, Seller
from .services.cep import fetch_cep, normalize_cep, format_cep
from .services.phone import normalize_phone, format_phone


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "uuid",
            "name",
            "cpf_cnpj",
            "email",
            "phone",
            "address",
            "cep",
            "city",
            "uf",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "created_at", "updated_at"]

    def validate_cpf_cnpj(self, value: str):
        digits = "".join(ch for ch in (value or "") if ch.isdigit())
        if len(digits) not in (11, 14):
            raise serializers.ValidationError("CPF/CNPJ deve ter 11 ou 14 dígitos.")
        return digits

    def validate_cep(self, value: str):
        digits = normalize_cep(value)
        if digits and len(digits) != 8:
            raise serializers.ValidationError("CEP deve conter 8 dígitos.")
        return digits

    def validate_phone(self, value: str):
        digits = normalize_phone(value)
        # Accept various lengths; require at least 8 digits for BR numbers if provided
        if digits and len(digits) < 8:
            raise serializers.ValidationError("Telefone inválido.")
        return digits

    def _apply_cep_lookup(self, instance: Customer):
        if instance.cep:
            info = fetch_cep(instance.cep)
            if info:
                # Only set if not provided explicitly
                if not instance.address:
                    addr = info.get("address")
                    neighborhood = info.get("neighborhood")
                    instance.address = f"{addr} - {neighborhood}" if neighborhood else addr
                if not instance.city:
                    instance.city = info.get("city") or instance.city
                if not instance.uf:
                    instance.uf = info.get("uf") or instance.uf
                # Normalize CEP to digits from service if provided
                instance.cep = normalize_cep(info.get("cep") or instance.cep)

    def create(self, validated_data):
        customer = Customer(**validated_data)
        self._apply_cep_lookup(customer)
        customer.full_clean()
        customer.save()
        return customer

    def update(self, instance, validated_data):
        for k, v in validated_data.items():
            setattr(instance, k, v)
        self._apply_cep_lookup(instance)
        instance.full_clean()
        instance.save()
        return instance

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if rep.get("cep"):
            rep["cep"] = format_cep(rep["cep"])
        if rep.get("phone"):
            rep["phone"] = format_phone(rep["phone"])
        return rep


class SupplierSerializer(serializers.ModelSerializer):
    class Meta:
        model = Supplier
        fields = [
            "uuid",
            "corporate_name",
            "cnpj",
            "email",
            "phone",
            "address",
            "cep",
            "city",
            "uf",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "created_at", "updated_at"]

    def validate_cnpj(self, value: str):
        digits = "".join(ch for ch in (value or "") if ch.isdigit())
        if len(digits) != 14:
            raise serializers.ValidationError("CNPJ deve ter 14 dígitos.")
        return digits

    def validate_cep(self, value: str):
        digits = normalize_cep(value)
        if digits and len(digits) != 8:
            raise serializers.ValidationError("CEP deve conter 8 dígitos.")
        return digits

    def validate_phone(self, value: str):
        digits = normalize_phone(value)
        if digits and len(digits) < 8:
            raise serializers.ValidationError("Telefone inválido.")
        return digits

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        if rep.get("cep"):
            rep["cep"] = format_cep(rep["cep"])
        if rep.get("phone"):
            rep["phone"] = format_phone(rep["phone"])
        return rep


class SellerSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(queryset=get_user_model().objects.all(), required=False, allow_null=True)

    class Meta:
        model = Seller
        fields = [
            "uuid",
            "user",
            "name",
            "access_level",
            "permissions",
            "discount_max",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "created_at", "updated_at"]

    def validate_discount_max(self, value):
        if value is None:
            return value
        if value < 0 or value > 100:
            raise serializers.ValidationError("desconto_maximo deve estar entre 0 e 100%.")
        return value
