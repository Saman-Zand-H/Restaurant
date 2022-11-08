from rest_framework import serializers

from delivery.models import UserAddressInfo


class UserAddressSerializer(serializers.ModelSerializer):
    location_lat = serializers.CharField()
    location_lon = serializers.CharField()
    
    class Meta:
        model = UserAddressInfo
        fields = ["address", 
                  "city", 
                  "location_lat", 
                  "location_lon", 
                  "postal_code",
                  "province",
                  "public_uuid"]
        readonly_fields = ["public_uuid"]
