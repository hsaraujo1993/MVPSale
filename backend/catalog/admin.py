from django.contrib import admin
from .models import Category, Brand, Product, Promotion


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "slug", "active", "created_at", "updated_at")
    list_filter = ("active",)
    search_fields = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    ordering = ("name",)


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "active", "created_at", "updated_at")
    list_filter = ("active",)
    search_fields = ("name",)
    ordering = ("name",)


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "sku",
        "name",
        "category",
        "brand",
        "cost_price",
        "margin",
        "sale_price",
        "active",
        "updated_at",
    )
    list_filter = ("active", "brand", "category")
    search_fields = ("name", "sku", "barcode")
    autocomplete_fields = ("category", "brand")
    ordering = ("name",)


@admin.register(Promotion)
class PromotionAdmin(admin.ModelAdmin):
    list_display = (
        "id",
        "product",
        "percent_off",
        "start_date",
        "end_date",
        "active",
        "created_at",
    )
    list_filter = ("active", "start_date", "end_date")
    search_fields = ("product__name", "product__sku")
    autocomplete_fields = ("product",)
    ordering = ("-created_at",)

