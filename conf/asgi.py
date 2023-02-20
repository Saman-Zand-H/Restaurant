import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import SessionMiddlewareStack
from channels.http import AsgiHandler

from apps.in_place.routing import websocket_urlpatterns


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')


application = ProtocolTypeRouter({
    "websocket": AuthMiddlewareStack(
        SessionMiddlewareStack(
            AllowedHostsOriginValidator(
                URLRouter(websocket_urlpatterns)
            )
        )
    ),
    "http": AsgiHandler(),
})
