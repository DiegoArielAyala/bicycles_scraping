from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from ..models import Bicycle

class UserSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ("username", "password1", "password2")

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Username already exists")
        return value

    def validate(self, data):
        if data["password1"] != data["password2"]:
            raise serializers.ValidationError("Passwords do not match") 
        
        validate_password(data["password1"])
        return data
    
    def create(self, validated_data):
        password = validated_data.pop("password1")
        validated_data.pop("password2", None)

        return User.objects.create_user(username=validated_data["username"], password=password)

class BicycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bicycle
        fields = ["id", "name", "price", "web", "reference", "url", "img"]

class SigninSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(username=data["username"], password=data["password"])

        if not user:
            raise serializers.ValidationError({"detail": "User or password incorrect"})
        
        data["user"] = user

        return data
    
class SignoutSerializer(serializers.Serializer):
    def validate(self, data):
        if not data["refresh"]:
            raise serializers.ValidationError({"detail": "Invalid token" })
        return data