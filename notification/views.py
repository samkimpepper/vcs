from django.shortcuts import render
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.generics import get_object_or_404

from . serializers import NotificationSerializer
from . models import *

def save_notification(notification_type, sender, recipient, note=None):
    data = {}
    data['notification_type'] = notification_type
    data['sender'] = sender 
    data['recipient'] = recipient
    data['note'] = note.pk
    if notification_type == NotificationType.NOTE_SHARE_REQUEST:
        data['content'] = f"{sender}님께서 노트 {note.title}를 공유하셨습니다. 수락하시겠습니까?"
    elif notification_type == NotificationType.NOTE_SHARE_ACCEPT:
        data['content'] = f"{sender}님께서 노트 {note.title}으로의 초대에 수락하셨습니다."
    
    serializer = NotificationSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    channel_layer = get_channel_layer()
    async_to_sync(channel_layer.group_send)(
        recipient, {
            "type": "notify",
            "data": data
        }
    )

    return Response(serializer.data, status=status.HTTP_200_OK)

class NotificationView(APIView):

    def get(self, request):
        notifications = Notification.objects.filter(recipient=request.user)
        serializer = NotificationSerializer(notifications, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class ReadNotificationView(APIView):
    def put(self, request, note_id):
        try:
            notification = Notification.objects.get(id=note_id)
            notification.is_read = True 
            notification.save()

            return Response({'msg': '알림 읽기 성공'}, status=status.HTTP_200_OK)
        except Note.DoesNotExist:
            return Response({'msg': '존재하지 않는 알림'}, status=status.HTTP_404_NOT_FOUND)
        
class ReadAllAndDeleteNotificationView(APIView):
    def delete(self, request):
        try:
            notifications = Notification.objects.filter(recipient=request.user)
            notifications.delete()

            return Response({'msg': '알림 모두 삭제 성공'}, status=status.HTTP_200_OK)
        except Notification.DoesNotExist:
            return Response({'msg': '알림이 존재하지 않음'}, status=status.HTTP_404_NOT_FOUND)



    
def notification_list_view(request):
    
    return render(request, 'notification/notification-list.html')

class DeleteReadNotifications(APIView):
    def delete(self, request):
        notifications = Notification.objects.filter(recipient=request.user, is_read=True)
        notifications.delete()

        notifications = Notification.objects.filter(recipient=request.user)
        serializer = NotificationSerializer(notifications, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

