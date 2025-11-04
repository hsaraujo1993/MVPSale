from decimal import Decimal
import uuid
from django.db import models, transaction
from django.core.validators import MinValueValidator


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


PAYMENT_METHOD_TYPES = (
    ("cash", "Dinheiro"),
    ("card_credit", "Cartão Crédito"),
    ("card_debit", "Cartão Débito"),
    ("pix", "PIX"),
    ("boleto", "Boleto"),
    ("voucher", "Voucher"),
    ("credit_note", "Crédito Loja"),
)


class PaymentMethod(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    code = models.SlugField(max_length=40, unique=True)
    name = models.CharField(max_length=80)
    type = models.CharField(max_length=20, choices=PAYMENT_METHOD_TYPES)
    fee_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    settlement_days = models.PositiveIntegerField(default=0)
    auto_settle = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} ({self.code})"


RECEIVABLE_STATUS = (
    ("PENDENTE", "PENDENTE"),
    ("PAGO", "PAGO"),
    ("ATRASADO", "ATRASADO"),
    ("ESTORNADO", "ESTORNADO"),
)


class Receivable(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    method = models.ForeignKey(PaymentMethod, on_delete=models.PROTECT, related_name="receivables")
    reference = models.CharField(max_length=60, blank=True)
    external_id = models.CharField(max_length=80, blank=True, db_index=True)
    due_date = models.DateField(null=True, blank=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    status = models.CharField(max_length=12, choices=RECEIVABLE_STATUS, default="PENDENTE", db_index=True)
    paid_date = models.DateField(null=True, blank=True)
    paid_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))

    def __str__(self):
        return f"{self.method.code} {self.amount} ({self.status})"


class PaymentEvent(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    receivable = models.ForeignKey(Receivable, on_delete=models.CASCADE, related_name="events")
    amount = models.DecimalField(max_digits=12, decimal_places=2, validators=[MinValueValidator(0)])
    fee_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    paid_date = models.DateField()
    external_id = models.CharField(max_length=80, unique=True, null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)

    def __str__(self):
        return f"evt {self.id} rec {self.receivable_id} {self.amount}"

    @transaction.atomic
    def apply(self):
        r = self.receivable
        if r.status in ("PAGO", "ESTORNADO"):
            return
        r.paid_amount = (r.paid_amount or Decimal("0.00")) + self.amount
        r.fee_amount = (r.fee_amount or Decimal("0.00")) + (self.fee_amount or Decimal("0.00"))
        r.paid_date = self.paid_date
        if r.paid_amount >= r.amount:
            r.status = "PAGO"
        r.save()


class CardBrand(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=80, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


CARD_TYPES = (
    ("card_credit", "Crédito"),
    ("card_debit", "Débito"),
)


class CardFeeTier(TimeStampedModel):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    brand = models.ForeignKey(CardBrand, on_delete=models.CASCADE, related_name="fee_tiers")
    type = models.CharField(max_length=20, choices=CARD_TYPES)
    installments_min = models.PositiveIntegerField(default=1)
    installments_max = models.PositiveIntegerField(default=1)
    fee_percent = models.DecimalField(max_digits=6, decimal_places=2, default=Decimal("0.00"))
    fee_fixed = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal("0.00"))
    settlement_days = models.PositiveIntegerField(default=30)

    class Meta:
        constraints = [
            models.CheckConstraint(check=models.Q(installments_min__gte=1), name="fee_min_ge_1"),
            models.CheckConstraint(check=models.Q(installments_max__gte=models.F('installments_min')), name="fee_max_ge_min"),
        ]

    def __str__(self):
        return f"{self.brand.name} {self.type} {self.installments_min}-{self.installments_max}"
