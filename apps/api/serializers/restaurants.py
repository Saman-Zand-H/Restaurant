from django.db import transaction
from rest_framework import serializers
from django.core.validators import MinValueValidator
from django.contrib.auth import get_user_model
from iranian_cities.models import City, Province

from ..exceptions import ServerError
from ..validators import validate_relations
from .users import UserSerializer
from .iranian_cities import (ProvinceSerializer,
                             CitySerializer)
from restaurants.models import (Restaurant,
                                RestaurantType,
                                RestaurantLocation,
                                Cuisine,
                                Item,
                                ItemVariation,
                                Review)


class RestaurantLocationSerializer(serializers.ModelSerializer):    
    city = CitySerializer(read_only=True)
    city_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                       write_only=True,
                                       required=True)
    
    province = ProvinceSerializer(read_only=True)
    province_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                           write_only=True,
                                           required=True)
    
    restaurant_url = serializers.HyperlinkedRelatedField(
        view_name='api_v1:restaurants-detail',
        lookup_field='public_uuid',
        read_only=True,
        source="location_restaurant"
    )
    
    class Meta:
        model = RestaurantLocation
        fields = [
            "id",
            "geo_address",
            "address",
            "city",
            "city_id",
            "province",
            "province_id",
            "restaurant_url"
        ]
        read_only_fields = ["id", "city", "province"]
        
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[
                ("city", "id", City),
                ("province", "id", Province)
            ]
        )
        return RestaurantLocation.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[
                ("city", "id", City),
                ("province", "id", Province)
            ]
        )
        ins_id = instance.id
        
        try:
            with transaction.atomic():
                return (
                    RestaurantLocation
                    .objects
                    .select_for_update()
                    .filter(id=ins_id)
                    .update(**validated_data)
                )
        except:
            raise ServerError()


class RestaurantTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RestaurantType
        fields = [
            "public_uuid",
            "name",
            "icon",
        ]
        read_only_fields = fields
    
    class Meta:
        model = RestaurantType
        fields = ["id"]


class RestaurantsSerializer(serializers.ModelSerializer):
    restaurant_type = RestaurantTypeSerializer(read_only=True)
    restaurant_type_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                                  required=True,
                                                  write_only=True)
    
    location = RestaurantLocationSerializer(read_only=True)
    location_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                                      required=False,
                                                      write_only=True)
    
    class Meta:
        model = Restaurant
        fields = [
            "public_uuid", 
            "name", 
            "phone_number", 
            "table_count", 
            "opens_at", 
            "closes_at", 
            "date_created", 
            "description",
            "score",
            "logo",
            "restaurant_type",
            "restaurant_type_id",
            "location",
            "location_id",
        ]
        read_only_fields = ["public_uuid", "date_created", "score"]
        
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[("restaurant_type", "id", RestaurantType)],
            optionals=[("location", "id", RestaurantLocation)]
        )
        return Restaurant.objects.create(**validated_data)
        
    def update(self, instance, validate_data):
        validate_data = validate_relations(
            validated_data=validate_data,
            optionals=[
                ("location", "id", RestaurantLocation),
                ("restaurant_type", "id", RestaurantType),
            ]
        )
        ins_id = instance.id
            
        try:
            with transaction.atomic():
                return (
                    Restaurant
                    .objects
                    .select_for_update()
                    .filter(id=ins_id)
                    .update(**validate_data)
                )
        except:
            raise ServerError()
        
        
class CuisineSerializer(serializers.ModelSerializer):
    restaurant = RestaurantsSerializer(read_only=True)
    restaurant_public_uuid = serializers.UUIDField(write_only=True,
                                                   required=True)
    
    class Meta:
        model = Cuisine
        fields = [
            "public_uuid",
            "name",
            "restaurant",
            "restaurant_public_uuid",
        ]
        read_only_fields = ["public_uuid"]
    
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[("restaurant", "public_uuid", Restaurant)]
        )
        
        return Cuisine.objects.create(**validated_data)
        
    def update(self, instance, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[("restaurant", "public_uuid", Restaurant)]
        )
        ins_uuid = instance.public_uuid
            
        try:
            with transaction.atomic():
                return (
                    Cuisine
                    .objects
                    .select_for_update()
                    .filter(public_uuid=ins_uuid)
                    .update(**validated_data)
                )
        except:
            raise ServerError()
            
        
class ItemSerializer(serializers.ModelSerializer):
    cuisine = CuisineSerializer(read_only=True)
    cuisine_public_uuid = serializers.UUIDField(write_only=True,
                                                required=True)
    
    class Meta:
        model = Item
        fields = ["public_uuid",
                  "name",
                  "cuisine",
                  "cuisine_public_uuid",
                  "picture",
                  "description"]
        read_only_fields = ["public_uuid"]
    
    def create(self, validated_data):
        cuisine_data = validated_data.pop("cuisine", None)
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[("cuisine", "public_uuid", Cuisine)]
        )
        
        return Item.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[("cuisine", "public_uuid", Cuisine)]
        )
        ins_uuid = instance.public_uuid
            
        try:
            with transaction.atomic():
                return (
                    Item
                    .objects
                    .select_for_update()
                    .filter(public_uuid=ins_uuid)
                    .update(**validated_data)
                )
        except:
            raise ServerError()
    
    
class ItemVariationSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_public_uuid = serializers.UUIDField(write_only=True,
                                             required=True)
    
    class Meta:
        model = ItemVariation
        fields = ["public_uuid",
                  "item",
                  "item_public_uuid",
                  "name",
                  "price",
                  "description"]
        read_only_fields = ["public_uuid"]
        
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[("item", "public_uuid", Item),]
        )
        
        return ItemVariation.objects.create(**validated_data)

    def update(self, instance, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[("item", "public_uuid", Item)]
        )
        ins_uuid = instance.public_uuid
        
        try:
            with transaction.atomic():
                return (
                    ItemVariation
                    .objects
                    .select_for_update()
                    .filter(public_uuid=ins_uuid)
                    .update(**validated_data)
                )
        except:
            raise ServerError()


class ReviewSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_public_uuid = serializers.UUIDField(write_only=True,
                                             required=True)
    
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                       write_only=True,
                                       required=True)
    
    class Meta:
        model = Review
        fields = ["public_uuid",
                  "item",
                  "item_public_uuid",
                  "user",
                  "user_id",
                  "date_created",
                  "review",
                  "score"]
        read_only_fields = ["public_uuid", "date_created"]
    
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[
                ("user", "id", get_user_model()),
                ("item", "public_uuid", Item),
            ],
        )
        
        return Review.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[
                ("user", "id", get_user_model()),
                ("item", "public_uuid", Item)
            ]
        )
        ins_uuid = instance.public_uuid
        
        try:
            with transaction.atomic():
                (
                    Review
                    .objects
                    .select_for_update()
                    .filter(public_uuid=ins_uuid)
                    .update(**validated_data)
                )
        except:
            raise ServerError()
        