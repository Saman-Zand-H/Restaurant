from django.urls import path

from . import views


app_name = "in_place"

urlpatterns = [
   path(route="",
        view=views.dashboard_view,
        name="dashboard"),
   path(route="orders/edit/",
        view=views.edit_order_view,
        name="edit_order"),
   path(route="orders/delete/",
        view=views.delete_order_view,
        name="delete_order"),
   path(route="orders",
        view=views.orders_view,
        name="orders"),
   path(route="staff/",
        view=views.staff_view,
        name="staff")
]
