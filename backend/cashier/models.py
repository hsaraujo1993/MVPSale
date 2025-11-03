from decimal import Decimal
from django.db import models
import uuid
from django.contrib.auth import get_user_model


class TimeStampedModel(models.Model):
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


SESSION_STATUS = (
    ("OPEN", "OPEN"),
    ("CLOSED", "CLOSED"),
)


class CashierSession(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    opened_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, related_name="cashier_opened")
    closed_by = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null=True, blank=True, related_name="cashier_closed")
    opened_at = models.DateTimeField(auto_now_add=True)
    closed_at = models.DateTimeField(null=True, blank=True)
    opening_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    closing_amount = models.DecimalField(max_digits=12, decimal_places=2, null=True, blank=True)
    expected_amount = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    difference = models.DecimalField(max_digits=12, decimal_places=2, default=Decimal("0.00"))
    status = models.CharField(max_length=10, choices=SESSION_STATUS, default="OPEN", db_index=True)
    notes = models.CharField(max_length=255, blank=True)

    def __str__(self):
        return f"CashierSession {self.id} ({self.status})"


MOVEMENT_TYPE = (
    ("INFLOW", "INFLOW"),
    ("OUTFLOW", "OUTFLOW"),
)


class CashMovement(TimeStampedModel):
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True)
    session = models.ForeignKey(CashierSession, on_delete=models.CASCADE, related_name="movements")
    type = models.CharField(max_length=10, choices=MOVEMENT_TYPE)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    reason = models.CharField(max_length=120, blank=True)
    reference = models.CharField(max_length=60, blank=True)

    def __str__(self):
        return f"{self.type} {self.amount} (sess {self.session_id})"
