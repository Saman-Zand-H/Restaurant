from django.contrib import admin

from .models import Staff, Order, OrderItem


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    list_display = ["user"]

    
@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ["order", "paid_price"]
    list_display_links = ["order"]
    search_fields = ["item__item__name", "item__count", "item__user", "uuid"]
    list_filter = ["order__order_type", "order__restaurant"]
    ordering = ["order__timestamp"]
    sortable_by = ["paid_price", "order__timestamp"]
    empty_value_display = "-empty-"
    
    
@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["order_type", "restaurant", "order_number", "timestamp"]
    list_display_links = ["restaurant"]
    exclude = ["uuid"]
    search_fields = ["uuid", "order_number", "restaurant__name", "uuid"]
    list_filter = ["order_type"]
    ordering = ["timestamp"]
    sortable_by = ["timestamp", "total_price"]
