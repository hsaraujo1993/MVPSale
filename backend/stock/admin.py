from django.contrib import admin
from .models import Stock, StockMovement


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "quantity_current", "minimum", "maximum", "status", "updated_at")
    list_filter = ("status",)
    search_fields = ("product__name", "product__sku")
    autocomplete_fields = ("product",)
    ordering = ("-updated_at",)


@admin.register(StockMovement)
class StockMovementAdmin(admin.ModelAdmin):
    list_display = ("id", "product", "type", "quantity", "reference", "created_at")
    list_filter = ("type",)
    search_fields = ("product__name", "product__sku", "reference")
    autocomplete_fields = ("product",)
    ordering = ("-created_at",)

