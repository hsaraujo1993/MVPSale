from django.contrib import admin
from .models import CashierSession, CashMovement


class CashMovementInline(admin.TabularInline):
    model = CashMovement
    extra = 0


@admin.register(CashierSession)
class CashierSessionAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "opened_by", "opened_at", "expected_amount", "closing_amount", "difference")
    list_filter = ("status",)
    inlines = [CashMovementInline]


@admin.register(CashMovement)
class CashMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "session", "type", "amount", "reason", "created_at")
    list_filter = ("type",)
    search_fields = ("reason", "reference")

