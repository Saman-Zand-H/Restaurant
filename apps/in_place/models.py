from django.db import models
from django.conf import settings
from django.contrib.auth.models import Permission, Group
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.utils import timezone
from uuid import uuid4

from restaurants.models import  Restaurant, Order
    

class Staff(models.Model):
    roles_choices = (
        ("ca", "cashier"),
        ("ch", "chef"),
        ("s", "supplier"),
        ("w", "waiter"),
        ("m", "manager"),
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
    description = models.TextField(blank=True,
                                   null=True)
    order = models.OneToOneField(Order,
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
    