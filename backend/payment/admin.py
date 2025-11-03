from django.contrib import admin
from .models import PaymentMethod, Receivable, PaymentEvent, CardBrand, CardFeeTier


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ("id", "code", "name", "type", "fee_percent", "fee_fixed", "settlement_days")
    search_fields = ("code", "name")
    list_filter = ("type",)


class PaymentEventInline(admin.TabularInline):
    model = PaymentEvent
    extra = 0


@admin.register(Receivable)
class ReceivableAdmin(admin.ModelAdmin):
    list_display = ("id", "method", "amount", "status", "due_date", "paid_amount", "fee_amount")
    list_filter = ("status", "method")
    search_fields = ("reference", "external_id")
    inlines = [PaymentEventInline]


@admin.register(CardBrand)
class CardPaymentAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "active")
    list_filter = ("active",)
    search_fields = ("name",)


@admin.register(CardFeeTier)
class CardFeeTierAdmin(admin.ModelAdmin):
    list_display = ("id", "brand", "type", "installments_min", "installments_max", "fee_percent", "fee_percent", "fee_fixed", "settlement_days")
    list_filter = ("brand",)
    search_fields = ("brand__name",)

