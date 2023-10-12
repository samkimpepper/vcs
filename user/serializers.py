from django.contrib.auth import authenticate

from rest_framework import serializers

from . models import * 

# Create your views here.

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'password', 'username']

    def validate(self, data):
        email = data.get('email')
        is_exists = User.objects.filter(email=email).exists()
        if is_exists:
            raise serializers.ValidationError("존재하는 이메일입니다")
        
        return data 
    
    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user 
    

class LoginSerializer(serializers.Serializer):
    email = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        user = authenticate(username=email, password=password)
        if user is None:
            raise serializers.ValidationError("비밀번호 불일치")
        
        return data 
    
class FollowingListSerializer(serializers.ModelSerializer):
    class Meta:
        model = User 
        fields = ['id', 'username', 'email']

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email']