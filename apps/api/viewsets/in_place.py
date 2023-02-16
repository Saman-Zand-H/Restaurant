from rest_framework import viewsets

from in_place.models import (Staff,
                             DineInOrder,
                             Order,
                             OrderItem)
from api.serializers.in_place import (StaffSerializer,
                                      DineInOrderSerializer,
                                      OrderSerializer,
                                      OrderItemSerializer)
from api.filters.in_place import (StaffFilterSet,
                                  DineInOrderFilterSet,
                                  OrderFilterSet,
                                  OrderItemFilterSet)

class StaffViewSet(viewsets.ModelViewSet):
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    filterset_class = StaffFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    
    
class DineInOrderViewSet(viewsets.ModelViewSet):
    queryset = DineInOrder.objects.all()
    serializer_class = DineInOrderSerializer
    filterset_class = DineInOrderFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    

class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer
    filterset_class = OrderFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    
    
class OrderItemViewSet(viewsets.ModelViewSet):
    queryset = OrderItem.objects.all()
    serializer_class = OrderItemSerializer
    filterset_class = OrderItemFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    