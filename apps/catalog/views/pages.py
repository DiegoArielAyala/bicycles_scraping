from django.shortcuts import render


def price_history_page(request, reference):
    return render(request, "price_history.html")

def search_bicycle_page(request):
    return render(request, "search_bicycle.html")



