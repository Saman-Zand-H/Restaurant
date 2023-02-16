import django_filters
from django_filters import widgets, rest_framework

from restaurants.models import (Restaurant,
                                RestaurantLocation,
                                Item,
                                ItemVariation,
                                Review,
                                Cuisine)


class RestaurantFilterSet(rest_framework.FilterSet):
    class Meta:
        model = Restaurant
        fields = {
            "name": ["icontains"],
            "public_uuid": ["exact"],
            "opens_at": ["range"],
            "closes_at": ["range"],
            "score": ["range"]
        }


class RestaurantLocationFilterSet(rest_framework.FilterSet):
    city_name = django_filters.CharFilter(field_name="city__name",
                                     lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name",
                                     lookup_expr="icontains")
    province_name = django_filters.CharFilter(field_name="province__name",
                                         lookup_expr="icontains")
    class Meta:
        model = RestaurantLocation
        fields = [
            "city",
            "name",
            "province"
        ]
        

class ItemFilterSet(rest_framework.FilterSet):
    name = django_filters.CharFilter(field_name="name", 
                                     lookup_expr="icontains")
    cuisine_name = django_filters.CharFilter(field_name="cuisine__name",
                                        lookup_expr="icontains")
    restaurant_name = django_filters.CharFilter(field_name="cuisine__restaurant__name",
                                           lookup_expr="icontains")
    
    class Meta:
        model = Item
        fields = [
            "public_uuid",
            "name",
            "cuisine",
        ]
        
class ItemVarFilterSet(rest_framework.FilterSet):
    item_name = django_filters.CharFilter(field_name="item__name", 
                                          lookup_expr="icontains")
    cuisine_name = django_filters.CharFilter(field_name="item__cuisine__name",
                                             lookup_expr="icontains")
    restaurant_name = django_filters.CharFilter(field_name="item__cuisine__restaurant__name",
                                                lookup_expr="icontains")
    price = django_filters.RangeFilter(field_name="price",
                                       lookup_expr="range")
    name = django_filters.CharFilter(field_name="name",
                                     lookup_expr="icontains")
    
    class Meta:
        model = ItemVariation
        fields = {
            "name": ["icontains"],
            "price": ["range"],
            "public_uuid": ["exact"]
        }
        fields = [
            "name",
            "public_uuid",
            "price",
            "item",
        ]


class ReviewFilterSet(rest_framework.FilterSet):
    item_name = django_filters.CharFilter(field_name="item__name",
                                     lookup_expr="icontains")
    username = django_filters.CharFilter(field_name="user__username",
                                         lookup_expr="icontains")
    score = django_filters.RangeFilter("score", lookup_expr="range")
    restaurant = django_filters.CharFilter(field_name="item__cuisine__restaurant__name",
                                           lookup_expr="icontains")
    
    class Meta:
        model = Review
        fields = [
            "item",
            "user",
            "username",
            "public_uuid",
            "score"
        ]
        
        
class CuisineFilterSet(rest_framework.FilterSet):
    restuarant_name = django_filters.CharFilter(field_name="restaurant__name",
                                           lookup_expr="icontains")
    name = django_filters.CharFilter(field_name="name",
                                     lookup_expr="icontains")
    
    class Meta:
        model = Cuisine
        fields = ["restaurant",
                  "name",
                  "public_uuid"]
        