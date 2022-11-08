from uuid import uuid4
from functools import reduce
import os
from django.core.files import File

from restaurants.models import RestaurantType


restaurant_types = (
    ("کافه", "staticfiles/assets/img/Initials/coffee-cup.png"),
    ("شیرینی", "staticfiles/assets/img/Initials/bakery-shop.png"),
    ("رستوران", "staticfiles/assets/img/Initials/restaurant.png"),
    ("آبمیو بستنی", "staticfiles/assets/img/Initials/ice-cream.png"),
)

for i in restaurant_types:
    a, _ = RestaurantType.objects.get_or_create(name=i[0])
    with open(i[1], "rb") as f:
        a.icon.save(i[1].split("/")[-1], File(f))


cuisines = {
    "رستوران": [
        "فست فود",
        "ایرانی",
        "کباب",
        "سالاد",
        "غذای دریایی",
        "بین المللی"],
    "کافه": [
        "غذا",
        "نوشیدنی داغ",
        "نوشیدنی سرد",
        "کیک و دسر",
        "بستنی"],
    "شیرینی": [
        "شیرینی"],
    "آبمیو بستنی": [
        "آبمیوه بستنی"]
}

cuisines_keys = [[i]*len(cuisines[i]) for i in cuisines.keys()]
cuisines_keys = reduce(lambda i, j: i+j, cuisines_keys)
cuisines_values = reduce(lambda i, j: i+j, cuisines.values())
cuisines = [*zip(cuisines_keys, cuisines_values)]
