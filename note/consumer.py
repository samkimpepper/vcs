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

from . models import Note
from user.models import User
from user.serializers import UserSerializer

import redis

# Redis 클라이언트 연결
redis_client = redis.StrictRedis(host='localhost', port=6379, db=0)

# 사용자를 그룹에 추가
def add_user_to_group(group_name, username):
    redis_client.hset(group_name, username, 1)

# 사용자를 그룹에서 제거
def remove_user_from_group(group_name, username):
    redis_client.hdel(group_name, username)

# 그룹에서 모든 사용자 목록 가져오기
def get_users_in_group(group_name):
    user_dict = redis_client.hgetall(group_name)
    return [user.decode('utf-8') for user in user_dict.keys()]

class NoteConsumer(WebsocketConsumer):

    def connect(self):
        token = parse_qs(self.scope["query_string"].decode("utf8"))["token"][0]
        note_id = parse_qs(self.scope["query_string"].decode("utf8"))["note_id"][0]

        user = self.get_user_from_token(token)

        if user is None:
            print("NoteConsumer 인증 실패!")
            self.close() 
        else:
            self.user = user 
            self.group_name = f"note{note_id}"

            add_user_to_group(self.group_name, user.username)

            async_to_sync(self.channel_layer.group_add)(
                self.group_name,
                self.channel_name
            )
            self.accept()

            serializer = UserSerializer(user)

            async_to_sync(self.channel_layer.group_send)(
                self.group_name, {
                    "type": "notify",
                    "data": serializer.data,
                }
            )

            async_to_sync(self.channel_layer.send)(
                self.channel_name, {
                    "type": "notify",
                    "data": serializer.data,
                    "current_users": get_users_in_group(self.group_name)
                }
            )

    def disconnect(self, close_code):
        print("diconnect")
        remove_user_from_group(self.group_name, self.user.username)
        async_to_sync(self.channel_layer.group_send)(
            self.group_name, {
                "type": "disconnect_notify",
                "username": self.user.username
            }
        )

        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )

    def commit_notify(self, event):
        print("commit notify")
        self.send(text_data=json.dumps(event))

    def notify(self, event):
        print("notify")
        self.send(text_data=json.dumps(event))
    
    def disconnect_notify(self, event):
        username = event['username']

        self.send(text_data=json.dumps(event))

    def receive(self, text_data):
        data = json.loads(text_data)
        text = data.get('text', '')

        start_idx = self.group_name.find("note") + len("note")
        note_id = int(self.group_name[start_idx:])

        try:
            note = Note.objects.get(id=note_id)
            note.content = text
            note.save()
        except Note.DoesNotExist:
            pass 

        self.send(text_data=json.dumps({'text': text_data}))


    #@database_sync_to_async
    def get_user_from_token(self, token_str):
        token = jwt.decode(token_str, options={"verify_signature": False})
        user_id = token.get('user_id')

        user = User.objects.get(id=user_id)
        
        return user 
        
