from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns


urlpatterns = [
    path(route='admin/', 
         view=admin.site.urls),
    
    path(route="accounts/", 
         view=include("allauth.urls")),
    path(route='dj-rest-auth/', 
         view=include('dj_rest_auth.urls')),
    path(route='dj-rest-auth/registration/', 
         view=include('dj_rest_auth.registration.urls')),

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
