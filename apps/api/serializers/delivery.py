from django.db import transaction
from django.core.validators import MinValueValidator, MaxLengthValidator
from rest_framework import serializers
from django.contrib.auth import get_user_model
from iranian_cities.models import City, Province

from ..exceptions import ServerError
from ..validators import validate_relations
from .restaurants import ItemSerializer
from .users import UserSerializer
from .iranian_cities import (CitySerializer,
                             ProvinceSerializer)
from .azbankgateways import BankSerializer
from restaurants.models import Item
from delivery.models import (UserAddressInfo,
                             DeliveryCart,
                             DeliveryCartItem,
                             Discount)


class UserAddressInfoSerializer(serializers.ModelSerializer):
    city = CitySerializer(read_only=True)
    city_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                       write_only=True,
                                       required=True)
    
    province = ProvinceSerializer(read_only=True)
    province_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                           write_only=True,
                                           required=True)
    
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                       write_only=True,
                                       required=True)
    
    class Meta:
        model = UserAddressInfo
        fields = [
            "public_uuid",
            "postal_code",
            "address",
            "location",
            "city",
            "city_id",
            "province",
            "province_id",
            "user",
            "user_id",
        ]
        read_only_fields = [
            "public_uuid",
        ]
        
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[
                ("city", "id", City),
                ("province", "id", Province),
                ("user", "id", get_user_model())
            ]
        )
        
        return UserAddressInfo.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[
                ("city", "id", City),
                ("province", "id", Province),
                ("user", "id", get_user_model())
            ]
        )
        ins_id = instance.id
        
        try:
            with transaction.atomic():
                return (
                    UserAddressInfo
                    .objects
                    .select_for_update()
                    .filter(id=ins_id)
                    .update(**validated_data)
                )
        except:
            raise ServerError()

        
class DiscountSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_public_uuid = serializers.UUIDField(required=True,
                                             write_only=True)
    
    class Meta:
        model = Discount
        fields = [
            "new_price",
            "discount_code",
            "item",
            "item_public_uuid",
            "date_created",
            "expiration_date"
        ]
        read_only_fields = [
            "date_created"
        ]
    
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[
                ("item", "public_uuid", Item)
            ]
        )
        
        return Discount.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[
                ("item", "public_uuid", Item)
            ]
        )
        ins_id = instance.id
        
        try:
            with transaction.atomic():
                return (
                    Discount
                    .objects
                    .select_for_update()
                    .filter(id=ins_id)
                    .update(**validated_data)
                )
        except:
            raise ServerError()
        

class DeliveryCartSerializer(serializers.ModelSerializer):
    discounts = DiscountSerializer(read_only=True)
    discounts_discount_code = serializers.CharField(required=False,
                                                    write_only=True,
                                                    validators=[MaxLengthValidator(20)])
    
    payment = BankSerializer(read_only=True)
    payment_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                          write_only=True,
                                          required=True)
    
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                       write_only=True,
                                       required=True)
    
    user_address = UserAddressInfoSerializer(read_only=True)
    user_address_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                               write_only=True,
                                               required=True)

    class Meta:
        model = DeliveryCart
        fields = [
            "public_uuid",
            "discounts",
            "discounts_discount_code",
            "user",
            "user_id",
            "payment",
            "payment_id",
            "user_address",
            "user_address_id",
            "date_created",
            "date_submitted"
        ]
        read_only_fields = [
            "public_uuid",
            "date_created",
            "date_submitted"
        ]
        
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[
                ("user", "id", get_user_model()),
                ("user_address", "public_uuid", UserAddressInfo)
            ],
            optionals=[
                ("discounts", "discount_code", Discount)
            ]
        )
        
        return DeliveryCart.objects.update(**validated_data)
    
    def update(self, instance, validated_data):
        ins_id = instance.id
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[
                ("discounts", "discount_code", Discount)
            ]
        )
        
        try:
            with transaction.atomic():
                return (
                    DeliveryCart
                    .objects
                    .select_for_update()
                    .filter(id=ins_id)
                    .update(**validated_data)
                )
        except:
            raise ServerError()
        

class DeliveryCartItemSerializer(serializers.ModelSerializer):
    item = ItemSerializer(read_only=True)
    item_public_uuid = serializers.UUIDField(write_only=True,
                                             required=True)
    
    cart = DeliveryCartSerializer(read_only=True)
    cart_public_uuid = serializers.UUIDField(write_only=True,
                                             required=True)
    
    class Meta:
        model = DeliveryCartItem
        fields = [
            "public_uuid",
            "item",
            "item_public_uuid",
            "count",
            "cart",
            "cart_public_uuid"
        ]
        read_only_fields= [
            "public_uuid",
        ]
        
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[
                ("item", "public_uuid", Item),
                ("cart", "public_uuid", DeliveryCart),
            ],
            optionals=[
                ("discount", "discount_code", Discount)
            ]
        )
        
        return DeliveryCartItem.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[
                ("discount", "discount_code", Discount)
            ]
        )
        ins_id = instance.id
        
        try:
            with transaction.atomic():
                return (
                    DeliveryCartItem
                    .objects
                    .select_for_update()
                    .filter(id=ins_id)
                    .update(**validated_data)
                )
        except:
            raise ServerError()
