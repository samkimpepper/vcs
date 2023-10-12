from django.urls import path, re_path
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator, OriginValidator
from django.core.asgi import get_asgi_application

from notification.consumers import NotificationConsumer
from note.consumer import NoteConsumer

# application = ProtocolTypeRouter({
#     'websocket': URLRouter(
#         notification.routing.websocket_urlpatterns,
#     )
# })

application = ProtocolTypeRouter({ 
    # Websocket chat handler
    'http': get_asgi_application(),
    'websocket':  # Only allow socket connections from the Allowed hosts in the settings.py file
        AuthMiddlewareStack(  # Session Authentication, required to use if we want to access the user details in the consumer 
            URLRouter(
                [
                    re_path(r'ws/notification/', NotificationConsumer.as_asgi()),    # Url path for connecting to the websocket to send notifications.
                    re_path(r'ws/note/', NoteConsumer.as_asgi()),
                ]
            )
        ),
    
})

# application = ProtocolTypeRouter({
#     "http": AsgiHandler(),
#     "websocket": AuthMiddlewareStack(
#         URLRouter(
#             notification.routing.websocket_urlpatterns
#         )
#     ),
# })