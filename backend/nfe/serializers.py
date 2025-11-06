from rest_framework import serializers
from .models import NFeInvoice


class NFeInvoiceSerializer(serializers.ModelSerializer):
    order_uuid = serializers.SerializerMethodField(read_only=True)
    class Meta:
        model = NFeInvoice
        fields = [
            "uuid",
            "order",
            "order_uuid",
            "company",
            "env",
            "provider",
            "ref",
            "status",
            "chave",
            "protocolo",
            "cStat",
            "xMotivo",
            "total",
            "danfe_url",
            "xml",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["uuid", "status", "chave", "protocolo", "cStat", "xMotivo", "danfe_url", "xml", "created_at", "updated_at", "order_uuid"]

    def get_order_uuid(self, obj):
        try:
            return str(obj.order.uuid)
        except Exception:
            return None
