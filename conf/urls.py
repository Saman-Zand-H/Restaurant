from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.defaults import page_not_found
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

from functools import partial

from azbankgateways.urls import az_bank_gateways_urls


urlpatterns = [
    path(route='admin/', 
         view=admin.site.urls),
    
    # Using regex, exclude password/change/, so we can override it in 
    # users.
    path(route=r"accounts/", 
         view=include("allauth.urls")),
    path(route='dj-rest-auth/', 
         view=include('dj_rest_auth.urls')),
    path(route='dj-rest-auth/registration/', 
         view=include('dj_rest_auth.registration.urls')),
    path(route="bankgateways/",
         view=az_bank_gateways_urls()),

    path(route="", 
         view=include("restaurants.urls", 
                      namespace="restaurants")),
    path(route="delivery/",
         view=include("delivery.urls",
                      namespace="delivery")),
    path(route="in_place/",
         view=include("in_place.urls", 
                      namespace="in_place")),
    path(route="accounts/",
         view=include("users.urls", 
                      namespace="accounts")),
    path(route="api/v1/",
         view=include("api.urls", 
                      namespace="api_v1"))
] + static(settings.MEDIA_URL, 
           document_root=settings.MEDIA_ROOT) 
urlpatterns += staticfiles_urlpatterns()


if settings.DEBUG:
    import debug_toolbar
    urlpatterns.append(path("__debug__/", include(debug_toolbar.urls))),
