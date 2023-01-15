from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from .models import (Restaurant, 
                     Review, 
                     Order, 
                     OrderItem, 
                     Item, 
                     RestaurantLocation,
                     RestaurantDelivery,
                     RestaurantType,
                     ItemVariation,
                     Cuisine)


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    list_display = ["name", 
                    "location", 
                    "phone_number", 
                    "table_count", 
                    "delivery", 
                    "opens_at", 
                    "closes_at",
                    "restaurant_type"]
    date_hierarchy = "date_created"
    empty_value_display = "-empty-"
    readonly_fields = ["date_created"]
    exclude = ["uuid"]
    fieldsets = (
        (None, {
            "fields": ("name", 
                       "table_count", 
                       "delivery", 
                       "opens_at", 
                       "closes_at", 
                       "description", 
                       "logo",
                       "restaurant_type"),
        }),
        ("Contact Info", {
            "fields": ("phone_number", 
                       "location"),
            "classes": ("collapse",)
        })
    )
    ordering = ["name"]
    sortable_by = ["name", "date_created", "table_count"]
    list_filter = ["table_count", "location__city", "location__province"]
    search_fields = ["name", "phone_number", "uuid"]


@admin.register(RestaurantLocation)
class RestaurantLocationAdmin(OSMGeoAdmin):
    list_display = ["address", "city", "province"]
    empty_value_display = "-empty-"
    exclude = ["uuid"]


@admin.register(Item)
class ItemAdmin(admin.ModelAdmin):
    list_display = ["name", "cuisine"]
    list_display_links = ["cuisine", "name"]
    list_filter = ["cuisine"]
    empty_value_display = "-empty-"
    exclude = ["uuid"]
    ordering = ["name"]
    sortable_by = ["name", "cuisine"]
    search_fields = ["name", "restaurant"]
    

@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["score", "item", "user"]
    list_display_links = ["item", "user"]
    search_fields = ["item", "user"]
    list_filter = ["score"]
    ordering = ["date_created"]
    sortable_by = ["date_created", "score"]
    empty_value_display = "-empty-"
    exclude = ["uuid"]
    readonly_fields = ["date_created"]
    date_hierarchy = "date_created"
    
    
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


@admin.register(RestaurantType)
class RestaurantTypeAdmin(admin.ModelAdmin):
    pass


@admin.register(RestaurantDelivery)
class RestaurantDeliveryAdmin(admin.ModelAdmin):
    pass


@admin.register(ItemVariation)
class ItemVariationAdmin(admin.ModelAdmin):
    pass


@admin.register(Cuisine)
class CuisineAdmin(admin.ModelAdmin):
    pass
