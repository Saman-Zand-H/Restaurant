import django_filters
from django_filters import rest_framework

from in_place.models import (Staff,
                             DineInOrder,
                             Order,
                             OrderItem)


class StaffFilterSet(rest_framework.FilterSet):
    username = django_filters.CharFilter(field_name="user__username",
                                         lookup_expr="icontains")
    income = django_filters.RangeFilter(field_name="income",
                                        lookup_expr="range")
    restuarant = django_filters.CharFilter(field_name="restuarant",
                                           lookup_expr="icontains")
    
    class Meta:
        model = Staff
        fields = [
            "role",
            "user",
            "public_uuid",
            "income",
            "restaurant"
        ]
        

class DineInOrderFilterSet(rest_framework.FilterSet):
    order_uuid = django_filters.UUIDFilter(field_name="order__public_uuid",
                                           lookup_expr="exact")
    timestamp = django_filters.DateTimeFilter(field_name="timestamp",
                                              lookup_expr="range")
    
    class Meta:
        model = DineInOrder
        fields = [
            "public_uuid",
            "timestamp",
            "table_number"
        ]


class OrderFilterSet(rest_framework.FilterSet):
    restaurant_name = django_filters.CharFilter(field_name="restaurant__name",
                                                lookup_expr="icontains")
    timestamp = django_filters.DateTimeFilter(field_name="timestamp",
                                              lookup_expr="range")
    
    class Meta:
        model = Order
        fields = [
            "done",
            "public_uuid",
            "order_type",
            "restaurant",
            "order_number"
        ]
        
        
class OrderItemFilterSet(rest_framework.FilterSet):
    name = django_filters.CharFilter(field_name="name",
                                     lookup_expr="icontains")
    paid_price = django_filters.RangeFilter(field_name="paid_price",
                                            lookup_expr="range")
    timestamp = django_filters.DateTimeFilter(field_name="timestamp",
                                              lookup_expr="range")
    
    class Meta:
        model = OrderItem
        fields = [
            "name",
            "public_uuid",
            "paid_price",
            "count",
            "timestamp",
            "order"
        ]
