from django.urls import path, include

from . import views 

app_name = 'user'

urlpatterns = [
    path('register/', views.RegisterView.as_view(), name='register'),
    path('login/', views.LoginView.as_view(), name='login'),
    path('follow/<int:user_pk>/', views.FollowView.as_view(), name='follow'),
    path('followings/', views.FollowingListView.as_view(), name='following-list'),
    path('followers/', views.FollowerListView.as_view(), name='follower-list'),
    
    path('follow-view/', views.follow_view, name='follow-view'),
]