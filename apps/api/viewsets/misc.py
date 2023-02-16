from rest_framework.viewsets import ReadOnlyModelViewSet
from azbankgateways.models import Bank
from iranian_cities.models import City, Province

from api.serializers.azbankgateways import BankSerializer
from api.serializers.iranian_cities import CitySerializer, ProvinceSerializer


class PaymentsViewSet(ReadOnlyModelViewSet):
    queryset = Bank
    serializer_class = BankSerializer
    

class CitiesViewSet(ReadOnlyModelViewSet):
    queryset = City
    serializer_class = CitySerializer
    
    
class ProvincesViewSet(ReadOnlyModelViewSet):
    queryset = Province
    serializer_class = ProvinceSerializer
