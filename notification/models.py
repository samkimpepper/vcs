from django.db import models

from user.models import User
from note.models import Note

class NotificationType(models.TextChoices):
    FRIEND_REQUEST = 'FR', '친구 요청'
    NOTE_SHARE_REQUEST = 'NR', '노트 공유 초대'
    NOTE_SHARE_ACCEPT = 'NA', '노트 공유 수락'

class Notification(models.Model):
    sender = models.ForeignKey(User, related_name='notification_sender', on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name='notification_recipient', on_delete=models.CASCADE)
    content = models.TextField()
    note = models.ForeignKey(Note, on_delete=models.CASCADE ,null=True)
    notification_type = models.CharField(max_length=2, choices=NotificationType.choices,)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)




    