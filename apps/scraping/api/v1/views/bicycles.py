from apps.scraping.api.v1.pagination import BicyclePagination
from apps.scraping.api.v1.serializers import BicycleSerializer, ShowPriceHistorySerializer
from apps.scraping.api.v1.views.filters import BicyclesFilter
from apps.scraping.models import Bicycle, PriceHistory
from apps.scraping.bicycles_selectors import get_bicycles
from apps.scraping.utils.pricing import clean_price
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView

class SearchBicycleView(ListAPIView):
    serializer_class = BicycleSerializer
    pagination_class = BicyclePagination
    filterset_class = BicyclesFilter

    def get_queryset(self):
        query = (self.request.query_params.get("q") or "").strip()
        min_price = clean_price(self.request.query_params.get("min_price"))
        max_price = clean_price(self.request.query_params.get("max_price"))

        qs = get_bicycles(q=query, min_price=min_price, max_price=max_price)

        return qs.order_by("-current_price")

class ShowPriceHistoryView(APIView):
    def get(self, request, reference):
        bicycle = get_object_or_404(Bicycle, reference=reference)
        price_history_objects = PriceHistory.objects.filter(bicycle=bicycle).order_by("date")

        dates = [price.date for price in price_history_objects]
        prices = [price.price for price in price_history_objects]

        data = {"name": bicycle.name, "dates": dates, "prices": prices}

        serializer = ShowPriceHistorySerializer(data=data)
        serializer.is_valid(raise_exception=True)

        return Response(serializer.data)
    
