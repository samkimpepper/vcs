from django.db import models

from user.models import User

# Create your models here.

class Tag(models.Model):
    name = models.CharField(max_length=50)
    def __str__(self):
        return self.name 

class Note(models.Model):
    title = models.CharField(max_length=50)
    content = models.TextField(blank=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_notes')
    shared_users = models.ManyToManyField(User, blank=True, related_name='shared_notes')
    tags = models.ManyToManyField(Tag, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)

class Version(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    next_version = models.OneToOneField('self', related_name='prev', null=True, blank=True, on_delete=models.SET_NULL)
    prev_version = models.OneToOneField('self', related_name='next', null=True, blank=True, on_delete=models.SET_NULL)    

class StashedVersion(models.Model):
    note = models.ForeignKey(Note, on_delete=models.CASCADE)
    content = models.TextField(blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)