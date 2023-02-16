from django.db import transaction
from django.core.validators import MinValueValidator
from rest_framework import serializers
from django.contrib.auth import get_user_model

from ..exceptions import ServerError
from ..validators import validate_relations
from .users import UserSerializer
from .restaurants import (RestaurantsSerializer,
                          ItemSerializer)
from restaurants.models import (Restaurant,
                                Item)
from in_place.models import (Staff,
                             DineInOrder,
                             Order,
                             OrderItem)


class StaffSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    user_id = serializers.IntegerField(validators=[MinValueValidator(1)],
                                       write_only=True,
                                       required=True)
    
    restaurant = RestaurantsSerializer(read_only=True)
    restaurant_public_uuid = serializers.UUIDField(write_only=True,
                                                   required=True)
    
    class Meta:
        model = Staff
        fields = [
            "public_uuid", 
            "user",
            "user_id",
            "role", 
            "description", 
            "date_created", 
            "income", 
            "address", 
            "restaurant",
            "restaurant_public_uuid",
        ]
        read_only_fields = ["date_created", "public_uuid"]
    
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[
                ("user", "id", get_user_model()),
                ("restaurant", "public_uuid", Restaurant)
            ]
        )
        
        return Staff.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        ins_id = instance.id
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[
                ("user", "id", get_user_model()),
                ("restuarant", "public_uuid", Restaurant)
            ]
        )
        
        try:
            with transaction.atomic():
                return (
                    Staff
                    .objects
                    .select_for_update()
                    .filter(id=ins_id)
                    .update(**validated_data)
                )
        except:
            raise ServerError()
        

class OrderSerializer(serializers.ModelSerializer):
    restaurant = RestaurantsSerializer(read_only=True)
    restaurant_public_uuid = serializers.UUIDField(write_only=True,
                                                   required=True)
    
    class Meta:
        model = Order
        fields = [
            "public_uuid",
            "order_type",
            "done",
            "description",
            "restaurant", # !!! cart !!!
            "restaurant_public_uuid",
            "timestamp",
            "order_number",
        ]
        read_only_fields = [
            "public_uuid"
        ]
        
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[
                ("restaurant", "public_uuid", Restaurant)
            ]
        )
        
        return Order.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        ins_id = instance.id
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[
                ("restaurant", "public_uuid", Restaurant)
            ]
        )
        
        try:
            with transaction.atomic():
                return (
                    Order
                    .objects
                    .select_for_update()
                    .filter(id=ins_id)
                    .update(**validated_data)
                )
        except:
            raise ServerError()


class OrderItemSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True)
    order_public_uuid = serializers.UUIDField(required=True,
                                              write_only=True)
    
    item = ItemSerializer(read_only=True, many=True)
    item_public_uuid = serializers.UUIDField(write_only=True,
                                             required=True)
    
    class Meta:
        model = OrderItem
        fields = [
            "public_uuid",
            "order",
            "order_public_uuid",
            "timestamp",
            "paid_price",
            "item",
            "item_public_uuid",
            "count"
        ]
        read_only_fields = [
            "public_uuid",
            "timestamp"
        ]
        
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[
                ("order", "public_uuid", Order),
                ("item", "public_uuid", Item)
            ]
        )
        
        return OrderItem.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        ins_id = instance.id
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[
                ("order", "public_uuid", Order),
                ("item", "public_uuid", Item)
            ]
        )
        
        try:
            with transaction.atomic():
                return (
                    OrderItem
                    .objects
                    .select_for_update()
                    .filter(id=ins_id)
                    .update(**validated_data)
                )
        except:
            raise ServerError()


class DineInOrderSerializer(serializers.ModelSerializer):
    order = OrderSerializer(read_only=True, many=True)
    order_public_uuid = serializers.UUIDField(write_only=True,
                                              required=True)
    
    class Meta:
        model = DineInOrder
        fields = [
            "public_uuid",
            "table_number",
            "order",
            "order_public_uuid",
            "timestamp"
        ]
        read_only_fields = [
            "public_uuid",
            "table_number",
            "timestamp",
        ]
        
    def create(self, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            mandatories=[
                ("order", "public_uuid", Order),
            ],
        )
        
        return DineInOrder.objects.create(**validated_data)
    
    def update(self, instance, validated_data):
        validated_data = validate_relations(
            validated_data=validated_data,
            optionals=[
                ("order", "public_uuid", Order),
            ],
        )
        ins_id = instance.id
        
        try:
            with transaction.atomic():
                return (
                    DineInOrder
                    .objects
                    .select_for_update()
                    .filter(id=ins_id)
                    .update(**validated_data)
                )
        except: 
            raise ServerError()
        