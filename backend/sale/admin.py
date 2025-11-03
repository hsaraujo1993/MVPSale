from django.contrib import admin
from .models import Order, OrderItem


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "status", "seller", "customer", "payment_method", "total", "discount_total", "created_at")
    list_filter = ("status", "payment_method")
    search_fields = ("id", "seller__name", "customer__name")
    inlines = [OrderItemInline]
