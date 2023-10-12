from django.shortcuts import render
from django.http import HttpResponse, JsonResponse

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth.decorators import login_required
from rest_framework.response import Response

from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer

from . models import *
from . serializers import * 

from notification.models import *
from notification.views import save_notification

# Create your views here.

class NoteViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = NoteSerializer
    queryset = Note.objects.all().order_by('created_at')

    def create(self, request):
        serializer = self.serializer_class(data=request.data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return JsonResponse({'msg': '노트가 생성되었습니다.'}, status=status.HTTP_201_CREATED)


def notes_view(request):
    permission_classes = [AllowAny]
    return render(request, 'note/note-list.html')

def note_detail_view(request, pk):
    permission_classes = [AllowAny]

    note = Note.objects.get(pk=pk)
    current_version = Version.objects.filter(note=note).latest('created_at')
    return render(request, 'note/note-detail.html', {'note': note, 'current_version': current_version})

class NotesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notes = Note.objects.filter(created_by=request.user)
        serializer = NoteSerializer(notes, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class NoteCommitView(APIView):
    def post(self, request, note_id):
        note = Note.objects.get(id=note_id)
        user = request.user 

        serializer = NoteCommitSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        new_content = serializer.validated_data['new_content']

        current_version = Version.objects.get(id=serializer.validated_data['current_version'].id)
        if current_version.next_version:
            print("충돌!")
            return 

        print('prev version: ', current_version.id)
        new_version = Version.objects.create(note=note, content=new_content, user=user, prev_version=current_version, next_version=None)
        current_version.next_version = new_version         
        current_version.save()
        note.content = new_content 
        note.save() 

        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(
            f"note{note.id}", {
                "type": "commit_notify",
                "data": user.username
            }
        )
        
        return Response({'current_version': new_version.id}, status=status.HTTP_200_OK)

class NotePullView(APIView):
    def post(self, request, note_id):
        current_version = Version.objects.get(id=request.data.get('current_version'))
        latest_version = Version.objects.filter(note=note_id).latest('created_at')

        if current_version.id == latest_version.id:
            return Response({'msg': '이미 최신 버전으로 풀된 상태입니다'}, status=status.HTTP_200_OK)
        
        serializer = VersionSerializer(latest_version)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class NoteStashView(APIView):
    def post(self, request, note_id):
        note = Note.objects.get(id=note_id)
        content = request.data.get('content')
        user = request.user

        stash = StashedVersion.objects.create(note=note, content=content, user=user)
        return Response({'msg': '스테이시 성공'}, status=status.HTTP_200_OK)
    
class NoteStashPopView(APIView):
    def post(self, request, note_id):
        note = Note.objects.get(id=note_id)
        user = request.user

        stash = StashedVersion.objects.filter(note=note, user=user).latest('created_at')

        stash.delete()

        return Response({'stash': stash.content}, status=status.HTTP_200_OK)
    
class SharedNotesView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        notes = Note.objects.filter(shared_users=request.user)
        serializer = NoteSerializer(notes, many=True)
        
        return Response(serializer.data, status=status.HTTP_200_OK)


class TagViewSet(viewsets.ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()

class NoteShareRequestView(APIView):
    def post(self, request):
        data = request.data 
        serializer = NoteShareRequestSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        shared_with = data.get('shared_with')
        note = Note.objects.get(pk=data.get('note'))
        for recipient in shared_with:
            save_notification(NotificationType.NOTE_SHARE_REQUEST, request.user.pk, recipient, note)

        return JsonResponse({'msg': '노트 공유를 완료했습니다.'}, status=status.HTTP_200_OK)
    
class NoteShareAcceptView(APIView):
    def post(self, request):
        print(request.data)
        data = request.data 
        serializer = NoteShareAcceptSerializer(data=data, context={'user': request.user})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        shared_by = data.get('shared_by')
        note = Note.objects.get(pk=data.get('note'))
        save_notification(NotificationType.NOTE_SHARE_ACCEPT, request.user.pk, shared_by, note)

        return JsonResponse({'msg': '노트 공유를 수락했습니다.'}, status=status.HTTP_200_OK)
    
def commit_log_view(request, note_id):
    versions = Version.objects.filter(note=note_id).order_by('created_at')
    return render(request, 'note/commit-log.html', {'versions': versions, 'note_id': note_id})

class CommitLogView(APIView):
    def get(self, request, note_id):
        versions = Version.objects.filter(note=note_id).order_by('created_at')

        serializer = VersionSerializer(versions, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
class RollbackView(APIView):
    def post(self, request, version_id):
        rollback_version = Version.objects.get(id=version_id)

        delete_version = rollback_version.next_version
        while delete_version:
            next_version = delete_version.next_version
            delete_version.delete()
            delete_version = next_version 
        
        rollback_version.next_version = None
        rollback_version.save()

        note = rollback_version.note 
        note.content = rollback_version.content
        note.save()

        return Response({'msg': '삭제 성공'}, status=status.HTTP_200_OK)
        