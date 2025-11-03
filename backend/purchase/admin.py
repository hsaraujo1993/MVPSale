from django.contrib import admin
from .models import SupplierProduct, PurchaseInvoice, PurchaseInstallment


@admin.register(SupplierProduct)
class SupplierProductAdmin(admin.ModelAdmin):
    list_display = ("id", "supplier", "product", "supplier_code", "ncm", "cfop")
    search_fields = ("supplier__corporate_name", "product__name", "supplier_code", "barcode")
    list_filter = ("supplier",)
    autocomplete_fields = ("supplier", "product")


class PurchaseInstallmentInline(admin.TabularInline):
    model = PurchaseInstallment
    extra = 0


@admin.register(PurchaseInvoice)
class PurchaseInvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "number", "series", "supplier", "issue_date", "total_value")
    search_fields = ("number", "series", "supplier__corporate_name")
    list_filter = ("issue_date", "supplier")
    inlines = [PurchaseInstallmentInline]

