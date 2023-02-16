from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Review


@receiver(post_save, sender=Review)
def update_restaurant_score(sender, instance, **kwargs):
    a = instance.item.cuisine.restaurant
    a.update_score()
