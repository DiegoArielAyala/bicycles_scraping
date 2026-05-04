import logging

from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

logger = logging.getLogger(__name__)

class UserSerializer(serializers.ModelSerializer):
    class Meta():
        model = User
        fields = ("username", "password1", "password2")
        extra_kwargs = {
            "password1": {"write_only": True},
            "password2": {"write_only": True}
        }
    
    password1 = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)

    def validate_username(self, value):
        try:
            User.objects.filter(username=value).exists()
        except:
            raise serializers.ValidationError("User already exists")

    def validate(self, data):
        if data.get("password1") == data.get("password2"):
            return data
        else:
            raise serializers.ValidationError("Passwords do not match") 
    
    def create(self, validated_data):
        try:
            validate_password(validated_data["password1"])
            validated_data.pop("password2")
            user = User.objects.create_user(username=validated_data["username"], password=validated_data["password1"],)
            return user
        except serializers.ValidationError("Invalid password"):
            logger.exception({"event": "invalid_password"}) 
        except:
            raise Exception("Error creating user")

