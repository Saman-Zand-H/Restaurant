from django.urls import path

from . import views


app_name = "delivery"

urlpatterns = [
   path(route="cart/add/",
        view=views.add_to_cart_view,
        name="add_to_cart"),
   path(route='cart/',
        view=views.cart_view,
        name='cart'),
   path(route="discounts/",
        view=views.discount_view,
        name="discount")
]