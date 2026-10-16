from rest_framework import serializers

from apps.alerts.models import Subscription
from apps.catalog.models import Bicycle

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