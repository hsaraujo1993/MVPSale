from django.contrib import admin
from .models import Customer, Supplier, Seller


@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "cpf_cnpj", "email", "city", "uf", "created_at")
    search_fields = ("name", "cpf_cnpj", "email")
    list_filter = ("uf",)
    ordering = ("name",)


@admin.register(Supplier)
class SupplierAdmin(admin.ModelAdmin):
    list_display = ("id", "corporate_name", "cnpj", "email", "city", "uf", "created_at")
    search_fields = ("corporate_name", "cnpj", "email")
    list_filter = ("uf",)
    ordering = ("corporate_name",)


@admin.register(Seller)
class SellerAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "user", "access_level", "discount_max", "created_at")
    search_fields = ("name", "user__username", "user__email")
    list_filter = ("access_level",)
    autocomplete_fields = ("user",)
    ordering = ("name",)

