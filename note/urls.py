from django.urls import path, include
from rest_framework.routers import DefaultRouter

from . import views 

app_name = 'note'

router = DefaultRouter()
router.register('', views.NoteViewSet)
router.register('tag/', views.TagViewSet)

urlpatterns = [
    path('share/', views.NoteShareRequestView.as_view(), name='share'),
    path('share/accept/', views.NoteShareAcceptView.as_view(), name='share-accept'),
    path('notes_view/', views.notes_view, name='notes-view'),
    path('list/', views.NotesView.as_view(), name='list'),
    path('list/shared/', views.SharedNotesView.as_view(), name='shared-list'),
    path('detail/<int:pk>/', views.note_detail_view, name='detail-view'),
    path('<int:pk>/', views.NoteViewSet.as_view({'get': 'retrieve'}), name='detail'),  
    path('commit/<int:note_id>/', views.NoteCommitView.as_view(), name='commit'),
    path('pull/<int:note_id>/', views.NotePullView.as_view(), name='pull'),
    path('commit-log/<int:note_id>/', views.CommitLogView.as_view(), name='commit-log'),
    path('commit-log-view/<int:note_id>/', views.commit_log_view, name='commit-log-view'),
    path('rollback/<int:version_id>/', views.RollbackView.as_view(), name='rollback'),
    path('stash/<int:note_id>/', views.NoteStashView.as_view(), name='stash'),
    path('stash-pop/<int:note_id>/', views.NoteStashPopView.as_view(), name='stash-pop'),
    path('', include(router.urls)),
    
     
]