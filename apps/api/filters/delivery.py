import django_filters
from django_filters import rest_framework

from delivery.models import (DeliveryCart,
                             DeliveryCartItem,
                             UserAddressInfo,
                             Discount)


class CartFilterSet(rest_framework.FilterSet):
    date_created = django_filters.DateTimeFilter(field_name="date_created",
                                                 lookup_expr="range")
    date_submitted = django_filters.DateTimeFilter(field_name="date_submitted",
                                                 lookup_expr="range") 
    username = django_filters.CharFilter(field_name="user__username",
                                         lookup_expr="icontains")
    payment_code = django_filters.CharFilter(field_name="payment__tracking_code",
                                             lookup_expr="exact")
    
    class Meta:
        model = DeliveryCart
        fields = [
            "public_uuid",
            "user",
            "date_created",
            "date_submitted"
        ]
        
        
class CartItemFilterSet(rest_framework.FilterSet):
    item_name = django_filters.CharFilter(field_name="item__name",
                                          lookup_expr="icontains")
    cart_owner = django_filters.CharFilter(field_name="cart__user__username",
                                           lookup_expr="icontains")
    
    class Meta:
        model = DeliveryCartItem
        fields = [
            "public_uuid",
            "item",
            "cart"
        ]
        
        
class UserAddressInfoFilterSet(rest_framework.FilterSet):
    username = django_filters.CharFilter(field_name="user__username",
                                         lookup_expr="icontains")
    
    class Meta:
        model = UserAddressInfo
        fields = ["user"]    


class DiscountFilterSet(rest_framework.FilterSet):
    item_name = django_filters.CharFilter(field_name="item__name",
                                          lookup_expr="icontains")
    date_created = django_filters.DateTimeFilter(field_name="date_created",
                                                lookup_expr="range")
    expiration_date = django_filters.DateTimeFilter(field_name="expiration_date",
                                                    lookup_expr="range")
    
    class Meta:
        model = Discount
        fields = [
            "discount_code",
            "item",
            "date_created",
            "expiration_date"
        ]
