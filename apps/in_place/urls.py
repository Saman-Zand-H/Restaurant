from django.urls import path

from . import views


app_name = "in_place"

urlpatterns = [
   path(route="",
        view=views.dashboard_view,
        name="dashboard"),
   path(route="item/new/render_template/",
        view=views.render_new_item_view,
        name="new_item_temp"),
   
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
        name="staff"),
   path(route="staff/change/",
        view=views.edit_staff_view,
        name="edit_staff"),
   path(route="staff/delete/",
        view=views.delete_staff_view,
        name="delete_staff"),
   
   path(route="finance/",
        view=views.finance_view,
        name="finance"),
   path(route="export/excel/sells",
        view=views.sells_to_excel_view,
        name="sells_excel"),
   
   path(route="menu/",
        view=views.menu_view,
        name="menu"),
   
   path(route="menu/cuisine/create",
        view=views.create_cuisine_view,
        name="create_cuisine"),
   path(route="menu/cuisine/edit",
        view=views.edit_cuisine_view,
        name="edit_cuisine"),
   path(route="menu/cuisine/delete",
        view=views.delete_cuisine_view,
        name="delete_cuisine"),
   
   path(route="menu/item/create",
        view=views.create_item_view,
        name="create_item"),
   path(route="menu/item/edit",
        view=views.edit_item_view,
        name="edit_item"),
   path(route="menu/item/delete",
        view=views.delete_item_view,
        name="delete_item"),
   
   path(route="menu/itemvar/create",
        view=views.create_itemvar_view,
        name="create_itemvar"),
   path(route="menu/itemvar/edit",
        view=views.edit_itemvar_view,
        name="edit_itemvar"),
   path(route="menu/itemvar/delete",
        view=views.delete_itemvar_view,
        name="delete_itemvar"),
   path(route="restaurant/edit/",
        view=views.edit_restaurant_view,
        name="edit_restaurant"),
   path(route="location/",
        view=views.location_view,
        name="location"),
   path(route="location/ajax/",
        view=views.province_ajax,
        name="province_ajax")
]
