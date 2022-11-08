from django.contrib import admin

from .models import Delivery, DeliveryCart, DeliveryCartItem, Discount


@admin.register(Delivery)
class DeliveryAdmin(admin.ModelAdmin):
    list_display = ["user", "vehicle_number", "national_id"]
    list_display_links = ["user"]
    search_fields = ["user__username", "uuid"]
    ordering = ["user__date_joined"]
    empty_value_display = "-empty-"
    exclude = ["uuid"]
    date_hierarchy = "user__date_joined"
    
    
@admin.register(DeliveryCart)
class DeliveryCartAdmin(admin.ModelAdmin):
    list_display = ["user", "paid"]
    list_display_links = ["user"]
    search_fields = ["user__username", "uuid"]
    list_filter = ["paid"]
    ordering = ["user__date_joined"]
    empty_value_display = "-empty-"
    exclude = ["uuid"]


@admin.register(DeliveryCartItem)
class DeliveryCartItemAdmin(admin.ModelAdmin):
    list_display = ["cart", "item", "count"]
    list_display_links = ["item"]
    search_fields = ["item__name", "count", "cart__user", "uuid"]
    ordering = ["cart__user__date_joined"]
    empty_value_display = "-empty-"
    exclude = ["uuid"]
    date_hierarchy = "cart__user__date_joined"
    
    
@admin.register(Discount)
class DiscountAdmin(admin.ModelAdmin):
    list_display = ["item", "new_price", "date_created", "discount_code"]
    list_display_links = ["item"]
    search_fields = ["uuid", "item__name", "item__menu__restaurant"]
    ordering = ["date_created"]
    exclude = ["uuid"]
    empty_value_display = "-empty-"
