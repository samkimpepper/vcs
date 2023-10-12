from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.response import Response


from . models import *
from . serializers import * 


class RegisterView(APIView):
    permission_classes = []

    def post(self, request):
        data = request.data 
        serializer = RegisterSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return JsonResponse({'msg': '회원가입 성공'}, status=status.HTTP_201_CREATED)
    
class LoginView(APIView):
    permission_classes = []

    def get(self, request):
        return render(request, 'user/login.html')

    def post(self, request):
        data = request.data 
        serializer = LoginSerializer(data=data)
        serializer.is_valid(raise_exception=True)

        email = data.get('email')
        password = data.get('password')
        user = authenticate(username=email, password=password)
        if user is None:
            raise serializers.ValidationError("비밀번호 불일치")

        token = TokenObtainPairSerializer.get_token(user)
        access_token = str(token.access_token)
        refresh_token = str(token)

        response = Response({'access_token': access_token, 'refresh_token': refresh_token, 'user_id': user.id, 'username': user.username}, status=status.HTTP_200_OK)
        response.set_cookie('access_token', access_token)
        response.set_cookie('refresh_token', refresh_token)

        return response
    
class FollowView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_pk):
        try:
            following = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            return Response({'msg': '존재하지 않는 사용자를 팔로우 시도했습니다.'}, status=status.HTTP_404_NOT_FOUND)
        user = request.user 

        user.followings.add(following)

        return Response({'msg': '팔로우되었습니다.'}, status=status.HTTP_200_OK)
    
    def delete(self, request, user_pk):
        try:
            following = User.objects.get(pk=user_pk)
        except User.DoesNotExist:
            return Response({'msg': '존재하지 않는 사용자를 언팔로우 시도했습니다.'}, status=status.HTTP_404_NOT_FOUND)
        user = request.user 

        user.followings.remove(following)

        return Response({'msg': '언팔로우했습니다.'}, status=status.HTTP_200_OK)


class FollowingListView(APIView):
    def get(self, request):
        followings = request.user.followings.all()

        serializer = FollowingListSerializer(followings, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)

class FollowerListView(APIView):
    def get(self, request):
        followers = User.objects.filter(followings=request.user)

        serializer = FollowingListSerializer(followers, many=True)

        return Response(serializer.data, status=status.HTTP_200_OK)
    
def follow_view(request):
    render(request, 'user/follow.html')
