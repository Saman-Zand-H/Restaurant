from rest_framework import viewsets

from delivery.models import (DeliveryCart,
                             UserAddressInfo,
                             DeliveryCartItem,
                             Discount)
from api.serializers.delivery import (DeliveryCartItemSerializer,
                                      DiscountSerializer,
                                      DeliveryCartSerializer,
                                      UserAddressInfoSerializer)
from api.filters.delivery import (CartFilterSet,
                                  CartItemFilterSet,
                                  DiscountFilterSet,
                                  UserAddressInfoFilterSet)


class DeliveryCartViewSet(viewsets.ModelViewSet):
    queryset = DeliveryCart.objects.all()
    serializer_class = DeliveryCartSerializer
    filterset_class = CartFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    
    
class DeliveryCartItemViewSet(viewsets.ModelViewSet):
    queryset = DeliveryCartItem.objects.all()
    serializer_class = DeliveryCartItemSerializer
    filterset_class = CartItemFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    
    
class UserAddressInfoViewset(viewsets.ModelViewSet):
    queryset = UserAddressInfo.objects.all()
    serializer_class = UserAddressInfoSerializer
    filterset_class = UserAddressInfoFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    

class DiscountViewSet(viewsets.ModelViewSet):
    queryset = Discount.objects.all()
    serializer_class = DiscountSerializer
    filterset_class = DiscountFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset