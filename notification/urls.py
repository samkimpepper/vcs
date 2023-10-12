from django.urls import path, include

from . import views 

app_name = 'notification'

urlpatterns = [
    path('', views.notification_list_view, name='list-view'),
    path('list/', views.NotificationView.as_view(), name='list'),
    path('read/<int:note_id>/', views.ReadNotificationView.as_view(), name='read'),
    path('delete/read/', views.DeleteReadNotifications.as_view(), name='delete-read'),
    path('delete/all/', views.ReadAllAndDeleteNotificationView.as_view(), name='delete-all'),
]