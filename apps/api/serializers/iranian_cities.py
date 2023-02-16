from rest_framework import serializers
from iranian_cities.models import Province, City


class CitySerializer(serializers.ModelSerializer):
    class Meta:
        model = City
        fields = ["name", "id"]
        
        
class ProvinceSerializer(serializers.ModelSerializer):
    
    class Meta:
        model = Province
        fields = ["name", "id"]
        
        