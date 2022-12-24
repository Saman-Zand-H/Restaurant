import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import SessionMiddlewareStack
from django.core.asgi import get_asgi_application

from apps.in_place.routing import websocket_urlpatterns


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')

django_asgi_application = get_asgi_application()


application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        SessionMiddlewareStack(
            AllowedHostsOriginValidator(
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
    "http": django_asgi_application,
})
