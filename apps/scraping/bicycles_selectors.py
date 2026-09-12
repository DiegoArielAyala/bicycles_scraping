from django.core.cache import cache
from django.shortcuts import get_object_or_404
from apps.scraping.models import Bicycle, PriceHistory

def get_bicycles(q=None, min_price=None, max_price=None):
    qs = Bicycle.objects.all()

    if q:
        if q.isdigit():
            qs = qs.filter(reference=q)
        else:
            qs = qs.filter(name__icontains=q)

    if min_price:
        qs = qs.filter(current_price__gte=min_price)
    if max_price:
        qs = qs.filter(current_price__lte=max_price)

    return qs

def get_price_history(reference):
    cached = cache.get(f"price_history:{reference}")
    
    if cached is not None:
        return cached

    bicycle = get_object_or_404(Bicycle, reference=reference)
    price_histories = PriceHistory.objects.filter(bicycle=bicycle).order_by("date")

    dates = [price.date for price in price_histories]
    prices = [price.price for price in price_histories]
    data = {"name": bicycle.name, "dates": dates, "prices": prices}

    cache.set(f"price_history:{reference}", data , timeout=120)

    return data