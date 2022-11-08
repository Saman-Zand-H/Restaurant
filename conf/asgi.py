import os
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from channels.sessions import SessionMiddlewareStack
from django.core.asgi import get_asgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'conf.settings')

django_asgi_application = get_asgi_application()

application = ProtocolTypeRouter({
    # "ws": AuthMiddlewareStack(
    #     SessionMiddlewareStack(
    #         AllowedHostsOriginValidator(
    #             URLRouter()
    #         )
    #     )
    # ),
    "http": django_asgi_application,
})
