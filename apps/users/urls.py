from django.urls import path

from . import views


app_name = "accounts"

urlpatterns = [
   path(route="profile/",
        view=views.profile_view,
        name="profile"),
   path(route="change-user/",
        view=views.change_user_view,
        name="change-user"),
   path(route="addresses/add/",
        view=views.add_address_view,
        name="add_address"),
   path(route="addresses/edit/",
        view=views.edit_address_view,
        name="edit_address"),
   path(route="addresses/delete/",
        view=views.delete_address_view,
        name="delete_address"),
   path(route="password_change/",
        view=views.change_password_view,
        name="change_password")
]
