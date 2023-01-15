from django.db import models
from django.utils import timezone

from datetime import datetime, time


class OrderEatIns(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(order_type="i")

    def within(self, within_time=timezone.now()):
        w_time_min = datetime.combine(within_time.date(),
                                      time.min,
                                      tzinfo=timezone.utc)
        w_time_max = datetime.combine(within_time.date(),
                                      time.max,
                                      tzinfo=timezone.utc)
        return self.filter(
            models.Q(timestamp__lte=w_time_max)
            & models.Q(timestamp__gte=w_time_min)).order_by(
                "-timestamp")
        
        
class OrderDels(models.Manager):
    def get_queryset(self, *args, **kwargs):
        return super().get_queryset(*args, **kwargs).filter(order_type="d")

    def within(self, within_time=timezone.now()):
        w_time_min = datetime.combine(within_time.date(),
                                      time.min,
                                      tzinfo=timezone.utc)
        w_time_max = datetime.combine(within_time.date(),
                                      time.max,
                                      tzinfo=timezone.utc)
        return self.filter(
            models.Q(timestamp__lte=w_time_max)
            & models.Q(timestamp__gte=w_time_min)).order_by(
                "-timestamp")
    