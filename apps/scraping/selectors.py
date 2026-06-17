from apps.scraping.models import Bicycle

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