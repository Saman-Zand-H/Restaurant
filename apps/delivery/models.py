from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models as gis_models
from django.contrib.contenttypes.fields import GenericRelation

from uuid import uuid4
from random import choices
from decimal import Decimal
from collections import Counter
from string import ascii_letters

from restaurants.models import ItemVariation, OrderItem


def generate_discount_code(length=10):
    return "".join(choices(ascii_letters, k=length))


class UserAddressInfo(gis_models.Model):
    public_uuid = gis_models.UUIDField(default=uuid4,
                                       auto_created=True,
                                       editable=False,
                                       unique=True)
    postal_code = gis_models.CharField(max_length=30)
    address = gis_models.TextField()
    location = gis_models.PointField()
    city = gis_models.CharField(max_length=50)
    province = gis_models.CharField(max_length=50)
    user = gis_models.ForeignKey(settings.AUTH_USER_MODEL,
                                 on_delete=models.CASCADE,
                                 related_name="user_addresses")
    
    # TODO: Implement str dunder
    
    class Meta:
        verbose_name_plural = "User Address Info"
        
    def save(self, *args, **kwargs):
        self.address = self.address.lower()
        self.city = self.city.lower()
        self.province = self.province.lower()
        return super().save(*args, **kwargs)


class Delivery(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.SET_NULL,
                                null=True,
                                related_name="user_delivery")
    vehicle_number = models.CharField(max_length=20)
    national_id = models.CharField(max_length=20)


class DeliveryCart(models.Model):
    paid = models.BooleanField(default=False)
    discounts = models.ManyToManyField("Discount",
                                       related_name="discount_carts")
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name="user_cart",
                                on_delete=models.CASCADE)
    user_address = models.OneToOneField(UserAddressInfo,
                                         on_delete=models.SET_NULL,
                                         null=True,
                                         related_name="address_cart")
    
    def get_discounts_price_diff(self):
        return sum([i.price_diff for i in self.discounts.all()])
    
    def get_estimated_price(self):
        return (sum([i.price for i in self.cart_items.all()]) 
                - self.get_discounts_price_diff())
    
    def clean(self, *args, **kwargs):
        items = [i.values("item") for i in self.discounts]
        counts = Counter(items)
        mul_items = [k for k, v in counts.items() if v > 1]
        if len(counts.most_common(1)) > 1:
            map(lambda i: self.discounts.remove(i), mul_items)
            return ValidationError({
                "discounts": "you can't have multiple discounts for a single item."
                })
        return super().clean(*args, **kwargs)
        
    

class DeliveryCartItem(models.Model):
    _price = 0
    public_uuid = models.UUIDField(default=uuid4,
                                   editable=False,
                                   auto_created=True,
                                   unique=True)
    item = models.ForeignKey(ItemVariation,
                             on_delete=models.CASCADE,
                             related_name="item_deliveries",
                             to_field="id")
    count = models.PositiveIntegerField()
    cart = models.ForeignKey(DeliveryCart,
                             on_delete=models.CASCADE,
                             related_name="cart_items",
                             to_field="id")
    discount = models.ForeignKey("Discount",
                                 on_delete=models.SET_NULL,
                                 related_name="discount_items",
                                 null=True,
                                 to_field="id")
    
    class Meta:
        unique_together = (
            ("item", "cart"),
        )
    
    @property
    def price(self):
        self. price = self.item.price * self.count
        return self._price
    
    @price.setter
    def price(self, value:Decimal):
        self._price = value
    

class Discount(models.Model):
    new_price = models.PositiveIntegerField()
    discount_code = models.CharField(max_length=20, 
                                     default=generate_discount_code,
                                     auto_created=True,
                                     unique=True)
    item = models.ForeignKey(ItemVariation,
                             on_delete=models.CASCADE,
                             related_name="item_discounts",
                             to_field="id")
    date_created = models.DateTimeField(auto_now_add=True)
    expiration_date = models.DateTimeField(blank=True, null=True)
    
    @classmethod
    def from_precent(cls, item:ItemVariation, percent:int):
        return cls.objects.create(item=item,
                                  new_price=item.price*(1-percent/100))
    
    @property
    def price_diff(self):
        return self.item.price - self.new_price
    
    def __str__(self):
        return f"{self.item.item.cuisine.restaurant.name}: {self.item.item}-{self.item}"
