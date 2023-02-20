from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from azbankgateways.urls import az_bank_gateways_urls


schema_view = get_schema_view(
     info=openapi.Info(
          title="Rubik Food API",
          default_version="1.0.0",
          contact=openapi.Contact(email="tnsperuse@gmail.com",
                                  name="Saman Zand Haghighi")
     ),
     public=True
)


urlpatterns = [
    path(route='admin/', 
         view=admin.site.urls),
    
    path(route="accounts/", 
         view=include("allauth.urls")),
    path(route='dj-rest-auth/', 
         view=include('dj_rest_auth.urls')),
    path(route='dj-rest-auth/registration/', 
         view=include('dj_rest_auth.registration.urls')),
#     path(route="blog/",
#          view=include("cms.urls")),
#     path('taggit_autosuggest/', include('taggit_autosuggest.urls')),

    path(route="swagger/",
         view=schema_view.with_ui(
              renderer="swagger", cache_timeout=0),
         name="schema-swagger-ui"),
    path(route="openapi/",
         view=schema_view.with_ui(),
         name="openapi-schema"),
    path(route="redoc/",
         view=schema_view.with_ui(
              renderer="redoc", cache_timeout=0),
         name="schema-redoc"),
    path(route="bankgateways/",
         view=az_bank_gateways_urls()),
    path(route="webpush/",
         view=include("webpush.urls")),

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
