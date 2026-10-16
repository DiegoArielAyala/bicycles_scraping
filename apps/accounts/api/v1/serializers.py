import logging

from django.contrib.auth import get_user_model, authenticate
from django.contrib.auth.models import Group
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError

from apps.accounts.permissions import ROLE_USER, get_user_roles
from apps.alerts.models import Subscription

User = get_user_model()
logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    group = serializers.CharField(read_only=True)
    id = serializers.PrimaryKeyRelatedField(read_only=True)
    
    class Meta:
        model = User
        fields = ("username", "password1", "password2", "group", "id")

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

        user = User.objects.create_user(username=validated_data["username"], password=password)

        group = Group.objects.get(name=ROLE_USER)

        user.groups.add(group)

        return user

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
    token = serializers.CharField(write_only=True)

    def validate(self, data):
        try:
            refresh = RefreshToken(data["token"])
            data["refresh"] = refresh
            return data
        except TokenError:
            logger.exception({"event": "token_error"})
            raise serializers.ValidationError({"detail": "Invalid or expired token"})

class MeSerializer(serializers.Serializer):
    id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_blank=True)
    roles = serializers.SerializerMethodField()
    is_staff = serializers.BooleanField()
    is_superuser = serializers.BooleanField()

    def get_roles(self, obj):
        return get_user_roles(obj)


class AdminSubscriptionsSerializer(serializers.ModelSerializer):
    bicycle_reference = serializers.SerializerMethodField()
    username = serializers.CharField(source="user.username", allow_null=True)
    
    class Meta:
        model = Subscription
        fields = ("id", "email", "bicycle", "bicycle_reference", "user", "username")
        read_only_fields = fields

    def get_bicycle_reference(self, obj):
        return obj.bicycle.reference

class AdminUsersSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("username", "roles")
        read_only_fields = fields

    def get_roles(self, obj):
        return get_user_roles(obj)