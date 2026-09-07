from django.contrib import admin

from .models import Order, OrderItem, Product


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    autocomplete_fields = ["product"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["name", "sku", "price", "stock", "is_available"]
    list_editable = ["price", "stock", "is_available"]
    list_filter = ["is_available"]
    search_fields = ["name", "sku"]


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["reference", "customer_name", "status", "total", "placed_at"]
    list_editable = ["status"]
    list_filter = ["status", "placed_at"]
    search_fields = ["reference", "customer_name", "customer_email"]
    date_hierarchy = "placed_at"
    inlines = [OrderItemInline]
    readonly_fields = ["total"]
