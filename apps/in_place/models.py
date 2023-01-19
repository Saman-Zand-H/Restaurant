from django.db import models
from django.conf import settings
from django.urls import reverse
from django.contrib.auth.models import Permission, Group
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone

from datetime import datetime, time
from uuid import uuid4

from restaurants.models import  Restaurant, ItemVariation
from delivery.models import DeliveryCart
from .managers import OrderDels, OrderEatIns
    

class Staff(models.Model):
    roles_choices = (
        ("ca", "cashier"),
        ("ch", "chef"),
        ("s", "supplier"),
        ("w", "waiter"),
        ("m", "manager"),
        ("d", "driver"),
    )
    public_uuid = models.UUIDField(default=uuid4,
                                   editable=False,
                                   auto_created=True,
                                   unique=True)
    role = models.CharField(max_length=2, choices=roles_choices)
    description = models.TextField(blank=True, null=True)
    date_created = models.DateTimeField(auto_now_add=True)
    income = models.PositiveIntegerField()
    address = models.CharField(max_length=255,
                               blank=True,
                               null=True)
    restaurant = models.ForeignKey(Restaurant,
                                   on_delete=models.CASCADE,
                                   related_name="restaurant_staff",
                                   to_field="id")
    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                on_delete=models.CASCADE,
                                related_name="user_staff")
     
    class Meta:
        permissions = [
            ("delete_orders", "is authorized to delete order records."),
            ("read_salaries", "is authorized to read other staff's salaries"),
            ("read_staff", "has access to details of the staff"),
            ("mod_staff", "can add, modify, or delete members for the staff")
        ]
        
    ######### Permission Properties #########
        
    @property
    def can_delete_orders(self):
        return self.user.has_perm("in_place.delete_orders")
    
    @property
    def can_read_salaries(self):
        return self.user.has_perm("in_place.read_salaries")
    
    @property
    def can_delete_items(self):
        return self.user.has_perm("in_place.delete_items")
    
    @property
    def can_add_items(self):
        return self.user.has_perm("in_place.add_items")
    
    @property
    def can_edit_items(self):
        return self.user.has_perm("in_place.edit_items")
    
    @property
    def can_change_staff(self):
        return self.user.has_perm("in_place.change_staff")
    
    @property
    def can_delete_staff(self):
        return self.user.has_perm("in_place.delete_staff")
    
    @property
    def can_edit_restaurant(self):
        return self.user.has_perm("in_place.edit_restaurant")
    
    ####################
    
    def get_restaurant_url(self):
        return reverse("restaurants:restaurant", 
                       kwargs={"public_uuid": self.restaurant.public_uuid})
    
    def save(self, *args, **kwargs):
        sup_save = super().save(*args, **kwargs)
        managers_g, created = Group.objects.get_or_create(
            name=f"{self.restaurant.name.lower()}_managers")
        if created:
            perms = Permission.objects.filter(
                codename__in=["delete_orders", 
                              "read_salaries", 
                              "read_staff", 
                              "mod_staff"])
            managers_g.permissions.set(perms)
        if self.role == "m":
            self.user.groups.add(managers_g)
        return sup_save
    
    
class DineInOrder(models.Model):
    table_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        null=True,
        blank=True
    )
    order = models.OneToOneField('Order',
                                 on_delete=models.CASCADE,
                                 related_name="order_dinein")
    public_uuid = models.UUIDField(default=uuid4,
                                   auto_created=True,
                                   editable=False,
                                   unique=True)
    timestamp = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"({self.order.timestamp}){self.order.order_number} - {self.table_number}"
    
    def clean(self, *args, **kwargs):
        table_count = self.order.restaurant.table_count
        if self.table_number > table_count:
            raise ValidationError(
                {"table_number": "you sure this table number is correct? "
                                 "it appears to exceed the total number of the tables..."})
        return super().clean(*args, **kwargs)
    
    
class Order(models.Model):
    order_type_choices = (
        ("d", "delivery"),
        ("i", "dine-in"),
    ) 
    public_uuid = models.UUIDField(default=uuid4,
                                   auto_created=True,
                                   unique=True,
                                   editable=False)
    done = models.BooleanField(default=False)
    description = models.TextField(blank=True, null=True)
    order_type = models.CharField(max_length=1, choices=order_type_choices)
    restaurant = models.ForeignKey(Restaurant,
                                   on_delete=models.CASCADE,
                                   related_name="restaurant_orders",
                                   to_field="id")
    timestamp = models.DateTimeField(default=timezone.now)
    order_number = models.PositiveIntegerField(blank=True)
    cart = models.ForeignKey(DeliveryCart,
                             on_delete=models.SET_NULL,
                             null=True,
                             blank=True,
                             related_name="order_cart")
    
    objects = models.Manager()
    deliveries = OrderDels()
    eatins = OrderEatIns()

    class Meta:
        ordering = ["-timestamp"]
    
    def __str__(self):
        return f"{self.restaurant}-{self.order_type}:{self.order_number}({self.id})"
    
    def _set_order_number(self):
        q = self.__class__.objects.filter(timestamp__date=self.timestamp.date())
        if q.exists():
            return q.latest("timestamp").order_number + 1
        else:
            return 1
    
    @property
    def total_price(self) -> int:
        return sum([item.paid_price for item in self.order_items.all()])
    
    @property
    def orders_repr(self):
        related = self.order_items.select_related("item")
        items = [i.item.full_name for i in related]
        counts = [i.count for i in related]
        paids = [i.paid_price for i in related]
        assert len(items) == len(counts) == len(paids)
        return [f"{c} x {i.title()} ({p})" for i, c, p in zip(items, counts, paids)]
        
    def save(self, *args, **kwargs):
        self.order_number = self._set_order_number()
        super().save(*args, **kwargs)
        self.restaurant.refresh_from_db()


class OrderItem(models.Model):
    order = models.ForeignKey(Order,
                              on_delete=models.CASCADE,
                              related_name="order_items")
    public_uuid = models.UUIDField(default=uuid4,
                                   auto_created=True,
                                   unique=True,
                                   editable=False)
    paid_price = models.PositiveIntegerField(default=0)
    item = models.ForeignKey(ItemVariation,
                             on_delete=models.CASCADE,
                             related_name="item_orders")
    count = models.PositiveIntegerField(default=1)
    timestamp = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.order}: {self.count} {self.item}"
    
    def save(self, *args, **kwargs):
        if self.count > 0:
            s = super().save(*args, **kwargs)
            self.order.restaurant.refresh_from_db()
            # In order for ElasticSearch to detect changes in the value of orders_repr,
            # we need to send a signal from Order to update the index.
            models.signals.post_save.send(
                sender=Order,
                instance=self.order,
                *args,
                **kwargs
            )
            return s
        # If this is the last order item remained, delete the order entirely
        keep_parents = 1 if self.order.order_items.count() > 1 else 0
        if not keep_parents:
            self.order.delete()
        super().delete(*args, **kwargs)
    
    class Meta:
        unique_together = (
            ("order", "item"),
        )

