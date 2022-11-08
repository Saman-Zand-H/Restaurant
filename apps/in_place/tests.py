from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages

import random
from datetime import time
from string import ascii_letters

from restaurants.models import Restaurant, RestaurantType, Item, ItemVariation, Cuisine
from in_place.models import Staff


def random_str():
    return "".join(random.choices(ascii_letters, k=8))


class TestOrderSubmission(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.user = get_user_model().objects.create(
            username="test",
            first_name=random_str(),
            last_name=random_str(),
            password="test123456")
        res_type = RestaurantType.objects.create(name="test_type")
        cls.restaurant = Restaurant.objects.create(name=random_str(),
                                                   opens_at=time(10),
                                                   closes_at=time(22),
                                                   restaurant_type=res_type,
                                                   table_count=random.randint(1, 50))
        cls.staff = Staff.objects.create(user=cls.user,
                                         role="m",
                                         restaurant=cls.restaurant)
        cuisine = Cuisine.objects.create(name="pizzas", restaurant=cls.restaurant)
        item = Item.objects.create(name="pepperoni", cuisine=cuisine)
        ItemVariation.objects.create(name="mini", price=25000, item=item)
                
