from django.test import TestCase

import pytest
from crdt.routing import application
from channels.layers import get_channel_layer
from channels.testing import ChannelsLiveServerTestCase
from channels.testing import WebsocketCommunicator
from channels.testing import HttpCommunicator
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from note.models import Note
from rest_framework_simplejwt.tokens import AccessToken
import jwt

from .consumers import NotificationConsumer

# Create your tests here.
class NotificationConsumerTestCase(ChannelsLiveServerTestCase):
    async def setUp(self):
        self.user = get_user_model().objects.create_user(username="testuser3", password="password")
        self.token = AccessToken.for_user(self.user)
        self.token_str = str(self.token)

        self.note = Note.objects.create(title="test", created_by=self.user)

    @pytest.mark.django_db(transaction=True)
    @pytest.mark.asyncio
    async def test_connect(self):
        #communicator = self.get_communicator(f"/ws/notification/?token={self.token_str}")
        communicator = WebsocketCommunicator(NotificationConsumer(), f"ws/notification/?token={self.token_str}")

        connected, _ = await communicator.connect()
        self.assertTrue(connected)

        await communicator.disconnect()
