"""
ASGI config for crdt project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.2/howto/deployment/asgi/
"""

import os
import django 

from .wsgi import *
from channels.auth import AuthMiddlewareStack
from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter, URLRouter, get_default_application
from django.core.asgi import get_asgi_application


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'crdt.settings')
django.setup()
application = get_default_application()

# application = ProtocolTypeRouter({
#     "http": AsgiHandler(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             notification.routing.websocket_urlpatterns
#         )
#     ),
# })