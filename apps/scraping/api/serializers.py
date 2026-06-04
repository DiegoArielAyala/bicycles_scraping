import logging

from apps.scraping.models import Bicycle, Subscription
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


logger = logging.getLogger(__name__)

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
    reference = serializers.CharField()

    class Meta:
        model = Subscription
        fields = ["email","reference"]
    
    def validate(self, data):
        email = data["email"]
        reference = data["reference"]

        try:
            bicycle = Bicycle.objects.get(reference=reference)
        except Bicycle.DoesNotExist:
            raise serializers.ValidationError({
                "reference": "Bicycle not found"
            })

        exists = Subscription.objects.filter(email=email, bicycle=bicycle).exists()

        if exists:
            raise serializers.ValidationError({"detail": "Subscription already exists"})
        
        data["bicycle"] = bicycle
        return data
        
    def create(self, validated_data):
        validated_data.pop("reference", None)
        return Subscription.objects.create(**validated_data)


class UnsubscribeSerializer(serializers.Serializer):
    email = serializers.EmailField()
    reference = serializers.CharField()
    
    def validate(self, data):
        email = data["email"]
        reference = data["reference"]
        try:
            bicycle = Bicycle.objects.get(reference=reference)
        except Bicycle.DoesNotExist:
            raise serializers.ValidationError({"detail": "Bicycle not found"})
        
        subscription = Subscription.objects.filter(email=email, bicycle=bicycle).first()

        if not subscription:
            raise serializers.ValidationError({"detail": "Subscription not found"})

        data["bicycle"] = bicycle
        data["subscription"] = subscription
        return data
        
        """Consultar en el caso que la bicicleta no exista, como hacer para borrar las suscripciones que los usuarios tenian a esa bicicleta (Se podria ejecutar eso cuando hago delete de una bicicleta)"""