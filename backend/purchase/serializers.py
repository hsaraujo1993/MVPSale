from rest_framework import serializers
from .models import PurchaseInvoice


class NFeImportSerializer(serializers.Serializer):
    xml_text = serializers.CharField(required=False, allow_blank=True)


class PurchaseInvoiceSerializer(serializers.ModelSerializer):
    supplier_name = serializers.CharField(source='supplier.corporate_name', read_only=True)

    class Meta:
        model = PurchaseInvoice
        fields = [
            'uuid', 'number', 'series', 'supplier', 'supplier_name', 'issue_date', 'total_value', 'created_at', 'updated_at'
        ]
        read_only_fields = ['uuid', 'created_at', 'updated_at']


class PurchaseInvoiceDetailSerializer(PurchaseInvoiceSerializer):
    class Meta(PurchaseInvoiceSerializer.Meta):
        fields = PurchaseInvoiceSerializer.Meta.fields + ['xml']
        read_only_fields = PurchaseInvoiceSerializer.Meta.read_only_fields + ['xml']
