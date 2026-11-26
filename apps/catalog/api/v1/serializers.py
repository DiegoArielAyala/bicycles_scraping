from rest_framework import serializers

from apps.catalog.models import Bicycle


class BicycleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Bicycle
        fields = ["id", "name", "current_price", "web", "reference", "url", "img"]


class ShowPriceHistorySerializer(serializers.Serializer):
    name = serializers.CharField()
    dates = serializers.ListField()
    prices = serializers.ListField()


        

