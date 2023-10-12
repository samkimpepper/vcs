from channels.generic.websocket import WebsocketConsumer, AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from channels.layers import get_channel_layer
import json
from asgiref.sync import async_to_sync
from urllib.parse import parse_qs

from django.db.models.signals import post_save
from django.dispatch import receiver

from rest_framework_simplejwt.tokens import AccessToken
from rest_framework.authtoken.models import Token
import jwt 

from . models import Notification
from .serializers import NotificationSerializer
from user.models import User 

def get_notification():
    notifications = Notification.objects.all()
    serializer = NotificationSerializer(notifications, many=True)
    return serializer.data

class NotificationConsumer(WebsocketConsumer):
    def connect(self):
        print("NotificationConsumer connect")
        token = parse_qs(self.scope["query_string"].decode("utf8"))["token"][0]
        print('token: ' + token)

        user = self.get_user_from_token(token)

        if user is None:
            print("Notification Consumer 인증 실패")
            self.close()
        else:
            self.user = user
            self.group_name = str(user.pk)
            print(self.group_name)
            #await async_to_sync(self.channel_layer.group_add)(self.group_name, self.channel_name)
            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )
            self.accept()

    def disconnect(self, close_code):
        print("diconnect")

    def notify(self, event):
        print("notify")
        print("group_name: " + self.group_name)
        self.send(text_data=json.dumps(event))

    def get_user_from_token(self, token_str):
        token = jwt.decode(token_str, options={"verify_signature": False})
        user_id = token.get('user_id')

        user = User.objects.get(id=user_id)
        return user 
        