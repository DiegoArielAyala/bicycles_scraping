import logging

from django.conf import settings
from django.shortcuts import get_object_or_404
from rest_framework import status
from rest_framework.generics import CreateAPIView, ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from ...models import Bicycle, PriceHistory
from ..serializers import UserSerializer, BicycleSerializer, SigninSerializer, SignoutSerializer, ScrapingSerializer, ShowPriceHistorySerializer
from ...services.github_actions import trigger_github_action

logger = logging.getLogger(__name__)

class SignupView(CreateAPIView):
    serializer_class = UserSerializer

class SearchBicycleView(ListAPIView):
    serializer_class = BicycleSerializer

    def get_queryset(self):
        max_results = 50
        qs = Bicycle.objects.all()
        query = (self.request.query_params.get("q") or "").strip()
        
        if not query:
            return qs[:max_results]

        if query.isdigit():
            qs = qs.filter(reference=query)
        else:
            qs = qs.filter(name__icontains=query)

        return qs.order_by("price")[:max_results]
    
class SigninView(APIView):
    def post(self, request):
        serializer = SigninSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = serializer.validated_data["user"]
        refresh = RefreshToken.for_user(user)
        
        return Response({"refresh": str(refresh), "access": str(refresh.access_token)})

class SignoutView(APIView):
    def post(self, request):
        serializer = SignoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        refresh = serializer.validated_data["refresh"]
        refresh.blacklist()
        
        return Response({"message": "Successfully logged out"})
    

class ScrapingView(APIView):
    def post(self, request):
        serializer = ScrapingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        token = request.headers.get("X-CRON-TOKEN")
        if token != settings.CRON_SECRET_TOKEN:
            logger.error({"event": "invalid_cron_secret"})
            return Response({"error": "Unauthorized"}, status=403)

        trigger_github_action(data)

        return Response({"message": "Scraping triggered", "job": "github-actions"}, status=status.HTTP_202_ACCEPTED)

class ShowPriceHistoryView(APIView):
    def get(self, request, reference):
        bicycle = get_object_or_404(Bicycle, reference=reference)
        price_history_objects = PriceHistory.objects.filter(bicycle=bicycle).order_by("date")

        dates = [price.date for price in price_history_objects]
        prices = [price.price for price in price_history_objects]

        data = {"name": bicycle.name, "dates": dates, "prices": prices}

        serializer = ShowPriceHistorySerializer(data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)
