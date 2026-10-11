from rest_framework import serializers


class ScrapingSerializer(serializers.Serializer):
    start_page = serializers.IntegerField()
    last_page = serializers.IntegerField()
    web = serializers.CharField()
    delete = serializers.BooleanField()