from decimal import Decimal
from django.conf import settings
from django.contrib.auth import get_user_model
import uuid
from django.db.models import JSONField
from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator
from django.db import models


def only_digits(value: str) -> str:
    return "".join(ch for ch in value if ch.isdigit())


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Customer(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    name = models.CharField(max_length=200)
    cpf_cnpj = models.CharField(max_length=14, unique=True, help_text="Somente números (11=CPF, 14=CNPJ)")
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    cep = models.CharField(max_length=9, blank=True)
    city = models.CharField(max_length=60, blank=True)
    uf = models.CharField(max_length=2, blank=True)

    def clean(self):
        errors = {}
        digits = only_digits(self.cpf_cnpj or "")
        if len(digits) not in (11, 14):
            errors["cpf_cnpj"] = "CPF/CNPJ deve ter 11 ou 14 dígitos."
        self.cpf_cnpj = digits
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.name} ({self.cpf_cnpj})"


class Supplier(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    corporate_name = models.CharField(max_length=200)
    cnpj = models.CharField(max_length=14, unique=True, help_text="Somente números (14 dígitos)")
    email = models.EmailField(blank=True, validators=[EmailValidator()])
    phone = models.CharField(max_length=20, blank=True)
    address = models.CharField(max_length=255, blank=True)
    cep = models.CharField(max_length=9, blank=True)
    city = models.CharField(max_length=60, blank=True)
    uf = models.CharField(max_length=2, blank=True)

    def clean(self):
        errors = {}
        digits = only_digits(self.cnpj or "")
        if len(digits) != 14:
            errors["cnpj"] = "CNPJ deve ter 14 dígitos."
        self.cnpj = digits
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.corporate_name} ({self.cnpj})"


class Seller(TimeStampedModel):
    ACCESS_LEVEL_CHOICES = (
        ("total", "total"),
        ("leitura", "leitura"),
        ("desconto", "desconto"),
        ("fechamento", "fechamento"),
    )

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE, related_name="seller_profile", null=True, blank=True)
    name = models.CharField(max_length=200)
    access_level = models.CharField(max_length=20, choices=ACCESS_LEVEL_CHOICES, default="leitura")
    discount_max = models.DecimalField(max_digits=5, decimal_places=2, default=Decimal("0.00"))
    permissions = JSONField(default=list, blank=True)

    def clean(self):
        errors = {}
        if self.discount_max is not None and (self.discount_max < 0 or self.discount_max > 100):
            errors["discount_max"] = "desconto_maximo deve estar entre 0 e 100%."
        if errors:
            raise ValidationError(errors)

    def __str__(self):
        return f"{self.name} ({self.user})"
