from decimal import Decimal
from django.db import models
import uuid
from django.core.validators import MinValueValidator

from people.models import Supplier
from catalog.models import Product


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class SupplierProduct(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.CASCADE, related_name="supplier_products")
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="supplier_products")
    supplier_code = models.CharField(max_length=60, db_index=True)
    universal_code = models.CharField(max_length=60, blank=True)
    barcode = models.CharField(max_length=64, blank=True)
    # Custos/compra (para análise por fornecedor)
    last_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    last_purchase_date = models.DateField(null=True, blank=True)

    # Fiscais
    ncm = models.CharField(max_length=10, blank=True)
    cfop = models.CharField(max_length=10, blank=True)
    cest = models.CharField(max_length=10, blank=True)
    icms_cst = models.CharField(max_length=5, blank=True)
    icms_origem = models.CharField(max_length=5, blank=True)
    ipi_cenq = models.CharField(max_length=5, blank=True)
    ipi_cst = models.CharField(max_length=5, blank=True)
    pis_cst = models.CharField(max_length=5, blank=True)
    pis_aliq = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    cofins_cst = models.CharField(max_length=5, blank=True)
    cofins_aliq = models.DecimalField(max_digits=7, decimal_places=4, null=True, blank=True)
    uCom = models.CharField(max_length=6, blank=True)
    uTrib = models.CharField(max_length=6, blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["supplier", "product"], name="uniq_supplier_product"),
        ]

    def __str__(self):
        return f"{self.supplier} - {self.product} ({self.supplier_code})"


class PurchaseInvoice(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    number = models.CharField(max_length=20)
    series = models.CharField(max_length=10, blank=True)
    supplier = models.ForeignKey(Supplier, on_delete=models.PROTECT, related_name="purchase_invoices")
    issue_date = models.DateField(null=True, blank=True)
    total_value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    xml = models.TextField()
    pdf_path = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"NF {self.number}/{self.series} - {self.supplier}"

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["supplier", "number", "series"], name="uniq_invoice_supplier_number_series"),
        ]


class PurchaseInstallment(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    invoice = models.ForeignKey(PurchaseInvoice, on_delete=models.CASCADE, related_name="installments")
    number = models.CharField(max_length=10)
    due_date = models.DateField()
    value = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=12, default="PENDENTE")

    def __str__(self):
        return f"Parcela {self.number} - {self.invoice}"
