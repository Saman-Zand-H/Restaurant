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
        name="discount"),
   path(route="cart/purchase/",
        view=views.purchase_view,
        name="purchase"),
   path(route="purchase/status/<uuid:public_uuid>/",
        view=views.purchase_status_view,
        name="payment_status"),
   path(route="orders/",
        view=views.orders_view,
        name="orders")
]