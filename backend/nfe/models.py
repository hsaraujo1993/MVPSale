from decimal import Decimal
from django.db import models
import uuid


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Company(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    cnpj = models.CharField(max_length=14, unique=True)
    ie = models.CharField(max_length=20, blank=True)
    regime_tributario = models.CharField(max_length=20, blank=True)
    razao_social = models.CharField(max_length=200)
    nome_fantasia = models.CharField(max_length=200, blank=True)
    logradouro = models.CharField(max_length=200, blank=True)
    numero = models.CharField(max_length=20, blank=True)
    bairro = models.CharField(max_length=120, blank=True)
    cidade = models.CharField(max_length=120, blank=True)
    uf = models.CharField(max_length=2, blank=True)
    cep = models.CharField(max_length=9, blank=True)

    def __str__(self):
        return f"{self.razao_social} ({self.cnpj})"


NFE_STATUS = (
    ("DRAFT", "DRAFT"),
    ("SUBMITTED", "SUBMITTED"),
    ("AUTHORIZED", "AUTHORIZED"),
    ("REJECTED", "REJECTED"),
    ("CANCELED", "CANCELED"),
)


class NFeInvoice(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    order = models.ForeignKey("sale.Order", on_delete=models.PROTECT, related_name="nfe_invoices")
    company = models.ForeignKey(Company, on_delete=models.PROTECT, related_name="nfe_invoices", null=True, blank=True)
    env = models.CharField(max_length=10, default="homolog")
    provider = models.CharField(max_length=20, default="focus")
    ref = models.CharField(max_length=60, unique=True)
    status = models.CharField(max_length=12, choices=NFE_STATUS, default="DRAFT", db_index=True)
    chave = models.CharField(max_length=50, blank=True, db_index=True)
    protocolo = models.CharField(max_length=50, blank=True)
    cStat = models.CharField(max_length=10, blank=True)
    xMotivo = models.CharField(max_length=255, blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    danfe_url = models.URLField(blank=True)
    xml = models.TextField(blank=True)

    def __str__(self):
        return f"NFe {self.ref} ({self.status})"


class NFeEvent(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    invoice = models.ForeignKey(NFeInvoice, on_delete=models.CASCADE, related_name="events")
    tipo = models.CharField(max_length=30)
    motivo = models.CharField(max_length=255, blank=True)
    protocolo = models.CharField(max_length=50, blank=True)
    payload = models.JSONField(default=dict, blank=True)
    status = models.CharField(max_length=20, default="SUBMITTED")

    def __str__(self):
        return f"{self.tipo} {self.invoice_id} ({self.status})"
