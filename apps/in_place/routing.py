from django.urls import path

from . import consumers


websocket_urlpatterns = [
   path(route="ws/dinein/delivered/",
        view=consumers.mark_delivered_consumer),
   path(route="ws/dinein/new_item/",
        view=consumers.orders_consumer)
]
