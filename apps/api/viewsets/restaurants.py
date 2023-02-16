from drf_yasg import openapi
from rest_framework import viewsets, status
from drf_yasg.utils import swagger_auto_schema


from restaurants.models import (RestaurantLocation,
                                RestaurantType,
                                Restaurant,
                                Item,
                                Cuisine,
                                ItemVariation,
                                Review)
from api.serializers.restaurants import (RestaurantLocationSerializer,
                                         RestaurantTypeSerializer,
                                         RestaurantsSerializer,
                                         ItemSerializer,
                                         CuisineSerializer,
                                         ItemVariationSerializer,
                                         ReviewSerializer)
from api.filters.restaurants import (RestaurantFilterSet,
                                     ItemFilterSet,
                                     ItemVarFilterSet,
                                     RestaurantLocationFilterSet,
                                     CuisineFilterSet,
                                     ReviewFilterSet)


location_schema = openapi.Schema(
    type=openapi.TYPE_OBJECT,
    properties={
        "geo_address": openapi.Schema(type=openapi.TYPE_STRING,
                                    description="location coordinates in the format: POINT(x y)",
                                    example="POINT(2.03 6.09)"),
        "address": openapi.Schema(type=openapi.TYPE_STRING,
                                description="descriptive address of the location.",
                                example="221B Baker Street"),
        "city_id": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            example=1
        ),
        "province_id": openapi.Schema(
            type=openapi.TYPE_INTEGER,
            example=1
        ),
    }
)


class RestaurantLocationViewSet(viewsets.ModelViewSet):
    queryset = RestaurantLocation.objects.all()
    serializer_class = RestaurantLocationSerializer
    filterset_class = RestaurantLocationFilterSet
    
    @swagger_auto_schema(
        request_body=location_schema,
        responses={status.HTTP_201_CREATED:RestaurantLocationSerializer()}
    )
    def create(self, request, *args, **kwargs):
        return super().create(request, *args, **kwargs)
    
class RestaurantTypeViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = RestaurantType.objects.all()
    serializer_class = RestaurantTypeSerializer
    
    
class RestaurantViewSet(viewsets.ModelViewSet):
    queryset = Restaurant.objects.all()
    serializer_class = RestaurantsSerializer
    filterset_class = RestaurantFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    

class CuisineViewSet(viewsets.ModelViewSet):
    queryset = Cuisine.objects.all()
    serializer_class = CuisineSerializer
    filterset_class = CuisineFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    
    
class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    filterset_class = ItemFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    

class ItemVariationViewSet(viewsets.ModelViewSet):
    queryset = ItemVariation.objects.all()
    serializer_class = ItemVariationSerializer 
    filterset_class = ItemVarFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all()
    serializer_class = ReviewSerializer
    filterset_class = ReviewFilterSet
    lookup_field = "public_uuid"
    
    def get_queryset(self):
        if (uuid:=self.kwargs.get("public_uuid")) is not None:
            return self.queryset.filter(public_uuid=uuid)
        else:
            return self.queryset
    