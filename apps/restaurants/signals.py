from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from datetime import datetime
from uuid import UUID
import json

from .utils import json_custom_encoder, json_custom_decoder
from .models import Review, Order, Restaurant


@receiver(post_save, sender=Review)
def update_restaurant_score(sender, instance, **kwargs):
    a = instance.item.item.cuisine.restaurant
    a.update_score()
    
    
# In Order to avoid unexpected rendering issues, 
# we basically re-render items in the consumer in js,
# send it to the dashboard and there re-eval it. Hence,
# what happens when an item is saved is the same thing that happens
# when we delete an item.

@receiver(post_save, sender=Order)
def signal_new_item(sender, instance, **kwargs):
    restaurant = instance.restaurant
    data = json.dumps({
        "restaurant": {
            "public_uuid": restaurant.public_uuid,
            "weekly_revenue": restaurant.weekly_revenue,
            "weekly_sale": restaurant.weekly_sale
        }
    }, default=json_custom_encoder)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"new_item_{restaurant.public_uuid}", {
        "type": "render_new_item",
        "msg": data
    })


@receiver(post_delete, sender=Order)
def signal_delete_order(sender, instance, **kwargs):
    restaurant = instance.restaurant
    data = json.dumps({
        "restaurant": {
            "public_uuid": restaurant.public_uuid,
            "weekly_revenue": restaurant.weekly_revenue,
            "weekly_sale": restaurant.weekly_sale
        }
    }, default=json_custom_encoder)
    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        f"new_item_{restaurant.public_uuid}", {
        "type": "render_new_item",
        "msg": data
    })
