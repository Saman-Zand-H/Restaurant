from rest_framework import routers

from . import viewsets


app_name = "api_v1"

router = routers.DefaultRouter()

router.register(prefix="user_addresses", 
                viewset=viewsets.UserAddressesViewset,
                basename="user_addresses")

urlpatterns = router.urls
