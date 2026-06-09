from apps.scraping.api.serializers import BicycleSerializer, ShowPriceHistorySerializer
from apps.scraping.models import Bicycle, PriceHistory
from django.shortcuts import get_object_or_404
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from apps.scraping.api.pagination import BicyclePagination

class SearchBicycleView(ListAPIView):
    serializer_class = BicycleSerializer
    pagination_class = BicyclePagination

    def get_queryset(self):
        qs = Bicycle.objects.all()
        query = (self.request.query_params.get("q") or "").strip()
        
        if not query:
            return qs.order_by("price")

        if query.isdigit():
            qs = qs.filter(reference=query)
        else:
            qs = qs.filter(name__icontains=query)

        return qs.order_by("price")

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
    
