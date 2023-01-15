from django.db import models
from django.conf import settings
from django.core.exceptions import ValidationError
from django.contrib.gis.db import models as gis_models
from azbankgateways.models import Bank

from uuid import uuid4
from random import choices
from decimal import Decimal
from collections import Counter
from string import ascii_letters

from restaurants.models import ItemVariation, Restaurant


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


class DeliveryMan(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name="user_deliveries")
    vehicle_model = models.CharField(max_length=50)
    vehicle_number = models.CharField(max_length=20)
    unique_code = models.CharField(max_length=30)
    restaurant = models.ForeignKey(Restaurant,
                                   on_delete=models.CASCADE,
                                   related_name="restaurnat_deliveries")
    
    def __str__(self):
        return f"{self.restaurant.name} DELIVERY: {self.user.username}"


class DeliveryCart(models.Model):
    discounts = models.ManyToManyField("Discount",
                                       related_name="discount_carts")
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             related_name="user_carts",
                             on_delete=models.SET_NULL,
                             blank=True,
                             null=True)
    payment = models.OneToOneField(Bank,
                                   related_name="payment_cart",
                                   on_delete=models.SET_NULL,
                                   null=True,
                                   blank=True)
    user_address = models.OneToOneField(UserAddressInfo,
                                         on_delete=models.SET_NULL,
                                         null=True,
                                         related_name="address_cart")
    date_created = models.DateTimeField(auto_now_add=True)
    date_submitted = models.DateTimeField(blank=True, null=True)
    
    def get_discounts_price_diff(self):
        return sum([i.price_diff for i in self.discounts.all()])
    
    def get_estimated_price(self):
        return (sum([i.price for i in self.cart_items.all()]) 
                - self.get_discounts_price_diff())
    
    def clean(self, *args, **kwargs):
        # Make sure there won't be more than one discounts.
        items = [i.values("item") for i in self.discounts]
        counts = Counter(items)
        mul_items = [k for k, v in counts.items() if v > 1]
        if len(counts.most_common(1)) > 1:
            map(lambda i: self.discounts.remove(i), mul_items)
            return ValidationError({
                "discounts": "you can't have multiple discounts for a single item."
                })
        
        # Make sure that the cart is up to date and is not 
        # an old one. If there is a 'date_submitted', it means
        # it's an old cart.
        if (self.id == self.user.user_carts.latest("date_created")
            and self.date_submitted is not None):
            self.__class__.objects.create(user=self.user)
            
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
