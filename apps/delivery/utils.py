from django.db.models import F
from django.db.models.query import QuerySet

from itertools import groupby
from operator import attrgetter

from restaurants.models import Restaurant


def group_delivery_items(qs: QuerySet):
    """takes a DeliveryCartItem queryset, and separates
         them by restaurant.

    Args:
        qs (QuerySet): DeliveryCartItem queryset
    """
    qs = qs.annotate(restaurant=F("item__item__cuisine__restaurant"))
    grouped = [(Restaurant.objects.get(id=k), [*g]) 
               for k, g in groupby(qs, attrgetter("restaurant"))]
    return grouped
