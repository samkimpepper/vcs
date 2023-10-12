from django.test import TestCase

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient

import factory
import json

from .serializers import FollowingListSerializer
from .models import *

# Create your tests here.

class UserFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = User 

    email = factory.Faker('email')
    username = factory.Faker('user_name')

class RegisterViewTestCase(APITestCase):
    url = reverse("user:register")

    def test_registration(self):
        data = {
            'email': 'testuser@gmail.com',
            'username': 'testuser',
            'password': 'password'
        }

        res = self.client.post(self.url, data)
        self.assertEqual(201, res.status_code)
        self.assertEqual('testuser', User.objects.get().username)

    def test_unique_email_validation(self):
        data1 = {
            'email': 'testuser@gmail.com',
            'username': 'testuser',
            'password': 'password'
        }
        res = self.client.post(self.url, data1)
        self.assertEqual(201, res.status_code)

        data2 = {
            'email': 'testuser@gmail.com',
            'username': 'testuser',
            'password': 'password'
        }
        res = self.client.post(self.url, data2)
        self.assertEqual(400, res.status_code)
        self.assertEqual(1, User.objects.count())

class LoginViewTestCase(APITestCase):
    url = reverse("user:login")

    def setUp(self):
        self.email = 'testuser@gmail.com'
        self.username = 'testuser'
        self.password = 'password'
        self.user = User.objects.create_user(
            email=self.email,
            username=self.username,
            password=self.password
        )

    def test_authentication_with_wrong_password(self):
        data = {
            'email': self.email,
            'password': 'wrongpassword'
        }
        
        res = self.client.post(self.url, data)
        self.assertEqual(400, res.status_code)

    def test_authentication_with_valid_password(self):
        data = {
            'email': self.email,
            'password': self.password
        }
        
        res = self.client.post(self.url, data)
        self.assertEqual(200, res.status_code)
        self.assertTrue('access_token' in json.loads(res.content))
        
class FollowViewTestCase(APITestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='testuser@gmail.com', username='testuser', password='password')
        self.client.force_authenticate(user=self.user)

    def test_follow_user(self):
        user_to_follow = User.objects.create_user(email='testuser2@gmail.com', username='testuser2', password='password')
        url = reverse("user:follow", args=[user_to_follow.pk])
        res = self.client.post(url)
        self.assertEqual(200, res.status_code)
        self.assertTrue(self.user.followings.filter(pk=user_to_follow.pk).exists())

    def test_follow_nonexistent_user(self):
        url = reverse("user:follow", args=[99999])
        res = self.client.post(url)
        self.assertEqual(404, res.status_code)
        self.assertFalse(self.user.followings.filter(pk=99999).exists())

    def test_unfollow_user(self):
        user_to_follow = User.objects.create_user(email='testuser2@gmail.com', username='testuser2', password='password')
        url = reverse("user:follow", args=[user_to_follow.pk])
        res = self.client.post(url)
        self.assertEqual(200, res.status_code)

        user_to_unfollow = user_to_follow
        url = reverse("user:follow", args=[user_to_unfollow.pk])
        res = self.client.delete(url)
        self.assertEqual(200, res.status_code)
        self.assertFalse(self.user.followings.filter(pk=user_to_unfollow.pk).exists())

class FollowingListViewTestCase(APITestCase):
    url = reverse("user:following-list")
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@gmail.com', username='testuser', password='password')
        self.client.force_authenticate(user=self.user)

        for i in range(4):
            user_to_follow = UserFactory.create()
            self.user.followings.add(user_to_follow)

    def test_get_following_list(self):
        res = self.client.get(self.url)

        self.assertEqual(200, res.status_code)
        self.assertEqual(4, len(res.json()))

class FollowerListViewTestCase(APITestCase):
    url = reverse("user:follower-list")
    def setUp(self):
        self.user = User.objects.create_user(email='testuser@gmail.com', username='testuser', password='password')
        self.client.force_authenticate(user=self.user)

        for i in range(4):
            user_to_follow = UserFactory.create()
            user_to_follow.followings.add(self.user)

    def test_get_follower_list(self):
        res = self.client.get(self.url)

        self.assertEqual(200, res.status_code)
        self.assertEqual(4, len(res.json()))

