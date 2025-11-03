from django.contrib import admin
from .models import Company, NFeInvoice, NFeEvent


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ("cnpj", "razao_social", "uf", "cidade")
    search_fields = ("cnpj", "razao_social")


class NFeEventInline(admin.TabularInline):
    model = NFeEvent
    extra = 0


@admin.register(NFeInvoice)
class NFeInvoiceAdmin(admin.ModelAdmin):
    list_display = ("id", "order", "status", "ref", "chave", "protocolo", "total", "created_at")
    list_filter = ("status",)
    search_fields = ("ref", "chave", "order__id")
    inlines = [NFeEventInline]

