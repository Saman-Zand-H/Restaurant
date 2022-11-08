from django.urls import path

from . import views

app_name = "restaurants"

urlpatterns = [
    path(route="",
         view=views.home_page_view,
         name="home"),
    path(route="restaurants/",
         view=views.list_restaurants_view,
         name="list_restaurants"),
    path(route="search_restaurants/",
         view=views.search_restaurants_view,
         name="search_restaurants"),
    path(route="restaurants/<uuid:public_uuid>/",
         view=views.restaurant_page_view,
         name="restaurant"),
]
