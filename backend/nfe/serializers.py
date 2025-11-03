from rest_framework import serializers
from .models import NFeInvoice


class NFeInvoiceSerializer(serializers.ModelSerializer):
    class Meta:
        model = NFeInvoice
        fields = [
            "uuid",
            "order",
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
        read_only_fields = ["uuid", "status", "chave", "protocolo", "cStat", "xMotivo", "danfe_url", "xml", "created_at", "updated_at"]
