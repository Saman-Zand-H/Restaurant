from django.db import models
from django.urls import reverse
from django.conf import settings
from django.db.models.functions import TruncDate
from django.core.validators import MinValueValidator, MaxValueValidator
from django.contrib.gis.db import models as gis_models
from django.core.exceptions import ValidationError
from django.templatetags.static import static
from django.utils.functional import cached_property

from iranian_cities.fields import ProvinceField, CityField
from persiantools.jdatetime import JalaliDateTime
from datetime import timedelta, datetime, time, date
from django.utils import timezone
from dateutil.relativedelta import relativedelta
from typing import List, Tuple
from operator import attrgetter
from itertools import groupby
from copy import deepcopy
from uuid import uuid4

from .utils import validate_extension, validate_size


class RestaurantLocation(gis_models.Model):
    address = gis_models.CharField(max_length=255)
    province = ProvinceField()
    city = CityField()
    geo_address = gis_models.PointField()
    
    def __str__(self):
        try:
            representation = f"{self.location_restaurant.name}: {self.city}"
        except:
            representation = self.address
        return representation
    
    class Meta:
        verbose_name_plural = "Restaurants Locations"
        

class RestaurantDelivery(models.Model):
    delivery_fee = models.PositiveIntegerField()
    max_distance = models.PositiveSmallIntegerField()
    
    def __str__(self):
        return self.restaurant.name if hasattr(self, "restaurant") else self.id
    
    
class RestaurantType(models.Model):
    public_uuid = models.UUIDField(editable=False,
                                   default=uuid4,
                                   auto_created=True,
                                   unique=True)
    name = models.CharField(max_length=50, unique=True)
    icon = models.ImageField(blank=True,
                             null=True,
                             upload_to="restaurants/type_icons")
    
    def __str__(self):
        return self.name

    def get_icon_url(self):
        if self.icon and hasattr(self.icon, 'url'):
            return self.icon.url
        return static("assets/img/no_image_available.png")
    

class Restaurant(models.Model):
    public_uuid = models.UUIDField(default=uuid4,
                                  editable=False,
                                  auto_created=True,
                                  unique=True)
    name = models.CharField(max_length=100)
    phone_number = models.CharField(max_length=20, 
                                    blank=True, 
                                    null=True)
    table_count = models.PositiveIntegerField(default=0)
    delivery = models.ForeignKey(RestaurantDelivery,
                                 on_delete=models.SET_NULL,
                                 related_name="restaurant",
                                 null=True,
                                 blank=True,
                                 to_field="id")
    restaurant_type = models.ForeignKey(RestaurantType,
                                        related_name="restaurant_type_restaurants",
                                        on_delete=models.SET_NULL,
                                        null=True,
                                        to_field="id")
    opens_at = models.TimeField()
    closes_at = models.TimeField()
    date_created = models.DateTimeField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)
    logo = models.ImageField(upload_to='restaurants/logos', 
                             blank=True,
                             null=True)
    score = models.FloatField(blank=True, 
                              null=True, 
                              auto_created=True, 
                              default=0)
    location = models.OneToOneField(RestaurantLocation, 
                                    blank=True,
                                    null=True,
                                    on_delete=models.CASCADE,
                                    related_name="location_restaurant")
    
    def __str__(self):
        return self.name
    
    def _get_daily_orders_data(self,
                       timestamp:datetime|date=timezone.now()):
        if isinstance(timestamp, datetime):
            timestamp = timestamp.date()
        min_date = datetime.combine(timestamp,
                                    time.min,
                                    tzinfo=timezone.utc)
        max_date = datetime.combine(timestamp,
                                    time.max,
                                    tzinfo=timezone.utc)
        orders = self.restaurant_orders.filter(
                  models.Q(timestamp__lte=max_date)
                  & models.Q(timestamp__gte=min_date))
        return orders
    
    def get_monthly_revenue(self, 
                            jalali_datetime:
                                JalaliDateTime=JalaliDateTime.today()):
        gte = datetime.combine(jalali_datetime.replace(day=1).to_gregorian().date(),
                               time.min,
                               tzinfo=timezone.utc)
        lt = gte + relativedelta(months=1) 
        orders = self.restaurant_orders.filter(models.Q(timestamp__lt=lt)
                & models.Q(timestamp__gte=gte))
        return sum([i.total_price for i in orders if orders.exists()] or [0])
    
    @cached_property
    def monthly_revenue(self):
        return self.get_monthly_revenue() 
    
    def get_daily_revenue(self, 
                          timestamp:datetime|date=timezone.now()):
        orders = self._get_daily_orders_data(timestamp)
        return sum([i.total_price for i in orders])
    
    @cached_property
    def daily_revenue(self):
        return self.get_daily_revenue()
    
    @cached_property
    def weekly_revenue(self):
        return [*reversed([self.get_daily_revenue(timezone.now()-timedelta(days=i)) 
                        for i in range(7)])]
        
    @cached_property 
    def weekly_revenue_sum(self):
        return sum(self.weekly_revenue)
    
    def get_daily_sale(self, 
                       timestamp:datetime=timezone.now()):
        orders = self._get_daily_orders_data(timestamp)
        return orders.count()
    
    @cached_property
    def weekly_sale(self):
        return [*reversed([self.get_daily_sale(timezone.now()-timedelta(days=i)) 
                         for i in range(7)])]
    
    def get_average_score_daily(self,
                                timestamp:datetime=timezone.now()):
        reviews = Review.objects.filter(
                    item__cuisine__in=self.restaurant_cuisines.values("pk"))
        lt = timestamp + timedelta(days=1)
        gte = timestamp
        return reviews.filter(models.Q(date_created__lt=lt)
                & models.Q(date_created__gte=gte)
                    ).aggregate(avg_score=models.Avg("score"))["avg_score"] or 0
        
    @cached_property
    def weekly_score(self):
        return [*reversed([self.get_average_score_daily(timezone.now()
                                                        -timedelta(i)) 
                         for i in range(7)])]
        
    @cached_property
    def most_popular_food(self):
        return ItemVariation.objects.filter(item_orders__order__restaurant=self).annotate(
                   item_counts=models.Count("item_orders")
                        ).order_by("item_counts").first() or "Nothing yet"
    
    def calculate_average_score(self):
        return self.get_average_score_daily()
        
    def update_score(self):
        prev_score = self.score
        self.score = self.calculate_average_score()
        self.save()
        return f"Updated: {prev_score} -> {self.score}"
    
    def get_absolute_url(self):
        return reverse("restaurants:restaurant", kwargs={"public_uuid": self.public_uuid})
    
    def get_picture_url(self):
        if self.logo and hasattr(self.logo, 'url'):
            return self.logo.url
        return static("assets/img/no_image_available.png")
    
    @cached_property
    def orders_today(self):
        return self._get_daily_orders_data()
    
    @cached_property
    def all_revenues(self) -> List[Tuple[datetime, int]]:
        """
            A function that takes all the paid orders of a restaurant and 
            gourps them by their date of creation, by day, and returns the sum
            of the total revenue of each they.
        """
        orders = self.restaurant_orders.annotate(
            date_created=TruncDate(
                'timestamp')).order_by('timestamp')
        # in order to reuse this iterable, we need to take a deepcopy
        iterable = groupby(orders, attrgetter("date_created"))
        iterable_copy = deepcopy(iterable)
        grouped = [*map(lambda i: [*i[1]], iterable)]
        dates = [i[0].isoformat() for i in iterable_copy]
        revenues = [
            *map(lambda i: sum(
                map(lambda j: j.total_price, i)), 
            grouped)]
        return [*zip(dates, revenues)]
    
    def refresh_from_db(self, *args, **kwargs):
        super().refresh_from_db(*args, **kwargs)
        cached_properties = ["monthly_revenue",
                             "daily_revenue",
                             "weekly_revenue",
                             "weekly_revenue_sum",
                             "weekly_sale",
                             "weekly_score",
                             "most_popular_food",
                             "orders_today",
                             "all_revenues"]
        for i in cached_properties:
            try:
                del self.__dict__[i]
            except KeyError:
                pass
            
    def clean(self, *args, **kwargs):
        if self.score:
            if self.score != self.calculate_average_score():
                raise ValidationError("The given score is invalid. Leave it empty.")
        super().clean()


class Cuisine(models.Model):
    public_uuid = models.UUIDField(default=uuid4,
                                   editable=True,
                                   auto_created=True,
                                   unique=True)
    name = models.CharField(max_length=50)
    restaurant = models.ForeignKey(Restaurant,
                                   on_delete=models.CASCADE,
                                   related_name="restaurant_cuisines",
                                   to_field="id")
    
    def __str__(self):
        return f"{self.restaurant.name}: {self.name}"
    
    
class Item(models.Model):
    public_uuid = models.UUIDField(default=uuid4,
                                   editable=False,
                                   auto_created=True,
                                   unique=True)
    name = models.CharField(max_length=100)
    cuisine = models.ForeignKey(Cuisine,
                                related_name="cuisine_items",
                                on_delete=models.CASCADE,
                                to_field="id")
    picture = models.ImageField(upload_to='items/pictures', 
                                blank=True, 
                                null=True,
                                validators=[validate_size, validate_extension])
    description = models.TextField(blank=True, null=True)
        
    def __str__(self):
        return self.name
    
    def get_picture_url(self):
        if self.picture and hasattr(self.picture, 'url'):
            return self.picture.url
        return static("assets/img/no_image_available.png")

    
class ItemVariation(models.Model):
    public_uuid = models.UUIDField(default=uuid4,
                                   editable=False,
                                   auto_created=True,
                                   unique=True)
    description = models.TextField(blank=True, null=True)
    item = models.ForeignKey(Item,
                             on_delete=models.CASCADE,
                             related_name="item_variations",
                             to_field="id")
    name = models.CharField(max_length=100)
    price = models.PositiveIntegerField()
    
    def __str__(self):
        return self.full_name
    
    @property
    def full_name(self):
        return f"{self.item.name} {self.name}"


class Review(models.Model):
    public_uuid = models.UUIDField(default=uuid4,
                                   editable=False,
                                   auto_created=True,
                                   unique=True)
    item = models.ForeignKey(Item,
                             on_delete=models.CASCADE,
                             related_name="item_reviews",
                             to_field="id")
    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.SET_NULL,
                             null=True,
                             related_name="user_reviews")
    date_created = models.DateTimeField(auto_now_add=True)
    review = models.TextField(blank=True, null=True)
    score = models.PositiveSmallIntegerField(validators=[MinValueValidator(1),
                                                         MaxValueValidator(5)])
    
    def __str__(self):
        return f"{self.item.name}: {self.score}"
    
    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.item.cuisine.restaurant.refresh_from_db()
