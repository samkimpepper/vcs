from django.test import TestCase

from rest_framework.reverse import reverse
from rest_framework.test import APITestCase, APIClient

import factory
from faker import Faker

from .models import *
from user.models import User
from notification.models import Notification

# Create your tests here.

class TagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Tag 
    name = factory.Faker('word')

class NoteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Note 
    title = factory.Faker('sentence', nb_words=4)
    content = factory.Faker('paragraph')
    created_by = factory.SubFactory('user.tests.UserFactory')
    tags = factory.SubFactory(TagFactory)

# 이 버전의 content는 Note의 content와 같다.
# 새 버전을 추가하면 이전 버전의 next_version을 새 버전으로 바꿔줘야 한다.
class VersionFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Version 
    note = factory.SubFactory(NoteFactory)
    content = factory.Faker('paragraph')
    user = factory.SubFactory('user.tests.UserFactory')
    prev_version = None
    next_version = None

@factory.post_generation
def create_version_links(self, create, extracted, **kwargs):
    if not create:
        return
    if extracted:
        self.prev_version = extracted
        extracted.next_version = self
        extracted.save()
        self.save()

class ExtractNoteID(TestCase):
    def test_extract(self):
        note_id = 1
        group_name = f"note{note_id}"

        start_idx = group_name.find("note") + len("note")
        extracted_note_id = group_name[start_idx:]

        self.assertEqual(note_id, int(extracted_note_id))

class NoteViewSetTestCase(APITestCase):
    url = reverse('note:note-list')
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@gmail.com', password='password')
        self.client.force_authenticate(user=self.user)
    
    def test_create_note(self):
        data = {
            'title': '노트',
            'content': '나도 노션같은 것 만들고 싶다',
            'tags': [],
            'shared_users': []
        }
        res = self.client.post(self.url, data)
        self.assertEqual(201, res.status_code)
        self.assertEqual(1, Note.objects.count())
        self.assertEqual(Note.objects.get().content, Version.objects.get().content)

    def test_get_note_detail(self):
        data = {
            'title': '노트',
            'content': '나도 노션같은 것 만들고 싶다',
            'tags': [],
            'shared_users': []
        }
        res = self.client.post(self.url, data)
        self.assertEqual(201, res.status_code)
        
        note_id = Note.objects.get().id
        url = reverse('note:note-detail', kwargs={'pk': note_id})
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        self.assertEqual(data['content'], res.data['content'])

class NotesViewTestCase(APITestCase):
    url = reverse('note:list')
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@gmail.com', password='password')
        self.client.force_authenticate(user=self.user)
        self.note = Note.objects.create(title='노트', content='나도 노션같은 것 만들고 싶다', created_by=self.user)


    def test_get_notes(self):
        res = self.client.get(self.url)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, len(res.data))

class NoteCommitViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@gmail.com', password='password')
        self.client.force_authenticate(user=self.user)
        self.note = Note.objects.create(title='노트', content='나도 노션같은 것 만들고 싶다', created_by=self.user)
        self.version = Version.objects.create(note=self.note, content=self.note.content, user=self.user, prev_version=None, next_version=None)

    def test_commit(self):
        data = {
            'current_version': self.version.id,
            'new_content': '나도 노션같은 것 만들고 싶다. 그래서 만들었다.'
        }
        url = reverse('note:commit', kwargs={'note_id': self.note.id})
        res = self.client.post(url, data)
        self.assertEqual(200, res.status_code)
        self.assertEqual(2, Version.objects.count())
        self.assertEqual(1, Note.objects.count())
        self.assertEqual(data['new_content'], Note.objects.get().content)
        self.assertEqual(data['new_content'], Version.objects.get(id=2).content)
        self.assertEqual(1, Version.objects.get(id=2).prev_version.id)
        self.assertEqual(2, Version.objects.get(id=1).next_version.id)
        #self.assertEqual(1, Notification.objects.count())

class NotePullViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@gmail.com', password='password')
        self.user2 = User.objects.create_user(username='testuser2', email='testuser2@gmail.com', password='password')
        self.client.force_authenticate(user=self.user)
        self.note = Note.objects.create(title='노트', content='나도 노션같은 것 만들고 싶다', created_by=self.user)
        self.note.shared_users.add(self.user2)
        self.version = Version.objects.create(note=self.note, content=self.note.content, user=self.user, prev_version=None, next_version=None)

    def test_pull(self):
        data = {
            'current_version': self.version.id,
            'new_content': '나도 노션같은 것 만들고 싶다. 그래서 만들었다.'
        }
                
        self.client.force_authenticate(user=self.user2)
        url = reverse('note:note-detail', kwargs={'pk': self.note.id})
        res = self.client.get(url)
        self.assertEqual(200, res.status_code)
        self.assertNotEqual(data['new_content'], res.data['content'])
    
        self.client.force_authenticate(user=self.user)
        url = reverse('note:commit', kwargs={'note_id': self.note.id})
        res = self.client.post(url, data)
        self.assertEqual(200, res.status_code)

        self.client.force_authenticate(user=self.user2)
        url = reverse('note:pull', kwargs={'note_id': self.note.id})
        res = self.client.post(url, {'current_version': self.version.id})
        self.assertEqual(200, res.status_code)
        self.assertEqual(data['new_content'], res.data['content'])

class NoteShareRequestViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@gmail.com', password='password')
        self.user2 = User.objects.create_user(username='testuser2', email='testuser2@gmail.com', password='password')
        self.client.force_authenticate(user=self.user)
        self.note = Note.objects.create(title='노트', content='나도 노션같은 것 만들고 싶다', created_by=self.user)

    def test_share_request(self):
        data = {
            'note': self.note.id,
            'shared_with': [self.user2.id]
        }
        url = reverse('note:share')
        res = self.client.post(url, data)
        print(res.content)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, Notification.objects.count())
        #print(Notification.objects.get().content)

class NoteShareAcceptViewTestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='testuser', email='testuser@gmail.com', password='password')
        self.user2 = User.objects.create_user(username='testuser2', email='testuser2@gmail.com', password='password')
        self.client.force_authenticate(user=self.user)
        self.note = Note.objects.create(title='노트', content='나도 노션같은 것 만들고 싶다', created_by=self.user)

    def test_share_accept(self):
        data = {
            'note': self.note.id,
            'shared_with': [self.user2.id]
        }
        url = reverse('note:share')
        res = self.client.post(url, data)
        self.assertEqual(200, res.status_code)

        self.client.force_authenticate(user=self.user2)
        data = {
            'note': self.note.id,
            'shared_by': self.user.id
        }
        url = reverse('note:share-accept')
        res = self.client.post(url, data)
        self.assertEqual(200, res.status_code)
        self.assertEqual(1, self.note.shared_users.count())
        self.assertEqual(self.user2.id, self.note.shared_users.get().id)
        