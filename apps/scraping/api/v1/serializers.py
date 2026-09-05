import logging

from apps.scraping.models import Bicycle, Subscription
from apps.scraping.permissions import ROLE_USER, get_user_roles
from django.contrib.auth import authenticate
from django.contrib.auth.models import User, Group
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


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

class BicycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bicycle
        fields = ["id", "name", "current_price", "web", "reference", "url", "img"]

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
        
class ScrapingSerializer(serializers.Serializer):
    start_page = serializers.IntegerField()
    last_page = serializers.IntegerField()
    web = serializers.CharField()
    delete = serializers.BooleanField()

class ShowPriceHistorySerializer(serializers.Serializer):
    name = serializers.CharField()
    dates = serializers.ListField()
    prices = serializers.ListField()

class SubscriptionSerializer(serializers.ModelSerializer):
    reference = serializers.CharField(write_only=True)
    bicycle = serializers.PrimaryKeyRelatedField(read_only=True)
    user = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Subscription
        fields = ["email", "reference", "bicycle", "user"]

    def validate(self, data):
        email = data["email"]
        reference = data["reference"]
        user = self.context["request"].user

        try:
            bicycle = Bicycle.objects.get(reference=reference)
        except Bicycle.DoesNotExist:
            raise serializers.ValidationError({
                "reference": "Bicycle not found"
            })

        # Ownership is by user+bicycle (unique constraint); email is for notifications
        if Subscription.objects.filter(user=user, bicycle=bicycle).exists():
            raise serializers.ValidationError({"detail": "Subscription already exists"})

        data["bicycle"] = bicycle
        data["user"] = user
        data["email"] = email
        return data

    def create(self, validated_data):
        validated_data.pop("reference", None)
        return Subscription.objects.create(**validated_data)


class MySubscriptionSerializer(serializers.ModelSerializer):
    bicycle_reference = serializers.CharField(source="bicycle.reference", read_only=True)
    bicycle_name = serializers.CharField(source="bicycle.name", read_only=True)
    bicycle_web = serializers.CharField(source="bicycle.web", read_only=True)

    class Meta:
        model = Subscription
        fields = (
            "id",
            "email",
            "bicycle_reference",
            "bicycle_name",
            "bicycle_web",
            "created_at",
        )
        read_only_fields = fields


class UnsubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reference = serializers.CharField()

    def validate(self, data):
        email = data["email"]
        reference = data["reference"]
        user = self.context["request"].user

        try:
            bicycle = Bicycle.objects.get(reference=reference)
        except Bicycle.DoesNotExist:
            raise serializers.ValidationError({"detail": "Bicycle not found"})

        subscription = Subscription.objects.filter(
            email=email,
            bicycle=bicycle,
            user=user,
        ).first()

        if not subscription:
            raise serializers.ValidationError({"detail": "Subscription not found"})

        data["bicycle"] = bicycle
        data["subscription"] = subscription
        return data
        
        """Consultar en el caso que la bicicleta no exista, como hacer para borrar las suscripciones que los usuarios tenian a esa bicicleta (Se podria ejecutar eso cuando hago delete de una bicicleta)"""

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