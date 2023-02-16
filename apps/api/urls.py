from rest_framework import routers
from django.urls import path

from api.viewsets import (restaurants,
                          in_place,
                          delivery,
                          misc)
from .jwt_conf import (DecoratedTokenObtainPairView, 
                       DecoratedTokenRefreshView)
from . import views


app_name = "api_v1"

router = routers.DefaultRouter()

################ restaurants
router.register(prefix="restaurant",
                viewset=restaurants.RestaurantViewSet,
                basename="restaurants")
router.register(prefix="restaurant_location",
                viewset=restaurants.RestaurantLocationViewSet,
                basename="restaurant_location")
router.register(prefix="restaurant_types",
                viewset=restaurants.RestaurantTypeViewSet,
                basename="restaurant_types")
router.register(prefix="cuisine",
                viewset=restaurants.CuisineViewSet,
                basename="cuisine")
router.register(prefix="item",
                viewset=restaurants.ItemViewSet,
                basename="item")
router.register(prefix="item_variations",
                viewset=restaurants.ItemVariationViewSet,
                basename="item_var")
router.register(prefix="review",
                viewset=restaurants.ReviewViewSet,
                basename="review")


################ in_place
router.register(prefix="staff",
                viewset=in_place.StaffViewSet,
                basename="staff")
router.register(prefix="dinein_order",
                viewset=in_place.DineInOrderViewSet,
                basename="dinein_order")
router.register(prefix="order",
                viewset=in_place.OrderViewSet,
                basename="order")
router.register(prefix="order_item",
                viewset=in_place.OrderItemViewSet,
                basename="order_item")


################ delivery
router.register(prefix="cart",
                viewset=delivery.DeliveryCartViewSet,
                basename="cart")
router.register(prefix="cart_item",
                viewset=delivery.DeliveryCartItemViewSet,
                basename="cart_item")
router.register(prefix="user_address",
                viewset=delivery.UserAddressInfoViewset,
                basename="user_address")
router.register(prefix="discount",
                viewset=delivery.DiscountViewSet,
                basename="discount")


################ misc
router.register(prefix="city",
                viewset=misc.CitiesViewSet,
                basename="cities")
router.register(prefix="province",
                viewset=misc.ProvincesViewSet,
                basename="provinces")
router.register(prefix="payment",
                viewset=misc.PaymentsViewSet,
                basename="payments")


urlpatterns = [
   path(route="charts/revenue/<int:id>",
        view=views.revenue_chart_view,
        name="revenue_chart"),
   path(route="charts/sales/<int:id>",
        view=views.sales_chart_view,
        name="sales_chart"),
   path(route="charts/score/<int:id>",
        view=views.score_chart_view,
        name="score_chart"),
   path(route="charts/gamma/<int:id>",
        view=views.gamma_chart_view,
        name="gamma_chart"),
   path(route="charts/lin_reg/<int:id>",
        view=views.regression_view,
        name="regression_chart"),
   path(route="all_orders/<int:id>",
        view=views.sales_view,
        name="sales"),
   path(route="order_geos/<int:id>",
        view=views.orders_coords_view),
   path(route="token/",
        view=DecoratedTokenObtainPairView.as_view(),
        name="token_obtain_pair"),
   path(route="token/refresh/",
        view=DecoratedTokenRefreshView.as_view(),
        name="token_refresh")
    ] + router.urls
