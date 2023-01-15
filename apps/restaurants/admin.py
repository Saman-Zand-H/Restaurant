from django.contrib import admin
from django.contrib.gis.admin import OSMGeoAdmin

from .models import (Restaurant, 
                     Review,
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
