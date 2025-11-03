from django.db import models
import uuid
from django.utils.text import slugify
from django.core.exceptions import ValidationError
from django.utils import timezone
from django.conf import settings
from decimal import Decimal


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Category(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=120, unique=True)
    slug = models.SlugField(max_length=140, unique=True, blank=True)
    active = models.BooleanField(default=True)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Brand(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=120, unique=True)
    active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class Product(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    sku = models.CharField(max_length=20, unique=True, blank=True)
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="products")
    brand = models.ForeignKey(Brand, on_delete=models.PROTECT, related_name="products")
    cost_price = models.DecimalField(max_digits=12, decimal_places=2)
    margin = models.DecimalField(max_digits=5, decimal_places=2, help_text="percentual 0-100")
    sale_price = models.DecimalField(max_digits=12, decimal_places=2)
    barcode = models.CharField(max_length=64, blank=True, db_index=True)
    active = models.BooleanField(default=True, db_index=True)

    def clean(self):
        errors = {}
        cost = Decimal(str(self.cost_price)) if self.cost_price is not None else None
        margin = Decimal(str(self.margin)) if self.margin is not None else None
        if cost is not None and cost < 0:
            errors["cost_price"] = "Preço de custo não pode ser negativo."
        if margin is not None and (margin < 0 or margin > 100):
            errors["margin"] = "Margem deve estar entre 0 e 100%."
        # Enforce minimum margin (business rule)
        if margin is not None and margin < Decimal(str(getattr(settings, "MIN_MARGIN_PERCENT", 0))):
            errors["margin"] = f"Margem mínima é {getattr(settings, 'MIN_MARGIN_PERCENT', 0)}%."
        expected = self._calc_sale_price(cost, margin)
        if self.sale_price is not None and expected is not None and round(Decimal(str(self.sale_price)), 2) != round(expected, 2):
            errors["sale_price"] = "Preço de venda deve ser custo + (custo * margem/100)."
        if errors:
            raise ValidationError(errors)

    def _calc_sale_price(self, cost=None, margin=None):
        cost = Decimal(str(cost if cost is not None else self.cost_price)) if (cost is not None or self.cost_price is not None) else None
        margin = Decimal(str(margin if margin is not None else self.margin)) if (margin is not None or self.margin is not None) else None
        if cost is None or margin is None:
            return None
        # Regra solicitada: se a margem for 0, o sale_price deve ser 0
        if margin == 0:
            return Decimal("0.00")
        return cost + (cost * (margin / Decimal("100")))

    def save(self, *args, **kwargs):
        # Auto SKU simple strategy: P + zero-padded ID after first save
        creating = self.pk is None
        # Always compute sale_price from cost+margin
        calc = self._calc_sale_price()
        if calc is not None:
            self.sale_price = calc
        super().save(*args, **kwargs)
        if creating and not self.sku:
            self.sku = f"P{self.pk:06d}"
            super().save(update_fields=["sku"])

    def __str__(self):
        return f"{self.name} ({self.sku})"


class Promotion(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name="promotions")
    percent_off = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()
    active = models.BooleanField(default=True, db_index=True)

    def clean(self):
        errors = {}
        if self.percent_off is not None and (self.percent_off < 0 or self.percent_off > 100):
            errors["percent_off"] = "Percentual deve estar entre 0 e 100%."
        if self.start_date and self.end_date and self.start_date > self.end_date:
            errors["end_date"] = "Data final deve ser maior ou igual à inicial."
        if self.active:
            overlapping = Promotion.objects.filter(
                product=self.product,
                active=True,
            )
            if self.pk:
                overlapping = overlapping.exclude(pk=self.pk)
            # Allow overlapping date ranges but enforce single active promo per product
            if overlapping.exists():
                errors["active"] = "Já existe promoção ativa para este produto."
        if errors:
            raise ValidationError(errors)

    @property
    def is_current(self):
        today = timezone.localdate()
        return self.active and self.start_date <= today <= self.end_date

    def __str__(self):
        return f"Promo {self.percent_off}% - {self.product}"

    class Meta:
        indexes = [
            models.Index(fields=["product", "active"], name="promo_prod_active_idx"),
            models.Index(fields=["start_date"], name="promo_start_idx"),
            models.Index(fields=["end_date"], name="promo_end_idx"),
        ]
