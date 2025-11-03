from decimal import Decimal
from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models, transaction
import uuid

from catalog.models import Product


STATUS_CHOICES = (
    ("ZERADO", "ZERADO"),
    ("ABAIXO", "ABAIXO"),
    ("OK", "OK"),
    ("ACIMA", "ACIMA"),
)


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Stock(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    product = models.OneToOneField(Product, on_delete=models.CASCADE, related_name="stock")
    quantity_current = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    minimum = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    maximum = models.DecimalField(max_digits=12, decimal_places=3, default=Decimal("0"))
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default="ZERADO", db_index=True)

    def recalc_status(self):
        qty = self.quantity_current or Decimal("0")
        minv = self.minimum or Decimal("0")
        maxv = self.maximum or Decimal("0")
        if qty <= 0:
            self.status = "ZERADO"
        elif qty < minv:
            self.status = "ABAIXO"
        elif maxv and qty > maxv:
            self.status = "ACIMA"
        else:
            self.status = "OK"

    def save(self, *args, **kwargs):
        self.recalc_status()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Stock({self.product_id}): {self.quantity_current}"


MOVEMENT_TYPES = (
    ("ENTRADA", "ENTRADA"),
    ("SAIDA", "SAIDA"),
    ("AJUSTE", "AJUSTE"),
)


class StockMovement(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="stock_movements")
    type = models.CharField(max_length=10, choices=MOVEMENT_TYPES)
    quantity = models.DecimalField(max_digits=12, decimal_places=3)
    reference = models.CharField(max_length=60, blank=True)
    note = models.CharField(max_length=255, blank=True)

    def clean(self):
        errors = {}
        if self.type in ("ENTRADA", "SAIDA"):
            if self.quantity is None or self.quantity <= 0:
                errors["quantity"] = "Quantidade deve ser positiva."
        elif self.type == "AJUSTE":
            if self.quantity is None or self.quantity == 0:
                errors["quantity"] = "Ajuste não pode ser zero."
        if errors:
            raise ValidationError(errors)

    @transaction.atomic
    def apply(self):
        stock, _ = Stock.objects.select_for_update().get_or_create(product=self.product)
        qty = self.quantity
        if self.type == "ENTRADA":
            new_qty = stock.quantity_current + qty
        elif self.type == "SAIDA":
            new_qty = stock.quantity_current - qty
        else:  # AJUSTE (signed)
            new_qty = stock.quantity_current + qty

        if getattr(settings, "PREVENT_NEGATIVE_STOCK", True) and new_qty < 0:
            raise ValidationError({"quantity": "Operação resultaria em estoque negativo."})

        stock.quantity_current = new_qty
        stock.save()
        return stock

    def save(self, *args, **kwargs):
        creating = self.pk is None
        self.full_clean()
        result = super().save(*args, **kwargs)
        if creating:
            self.apply()
        return result

    def __str__(self):
        return f"{self.type} {self.quantity} ({self.product_id})"
