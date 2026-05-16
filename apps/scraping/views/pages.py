from django.shortcuts import render

def signin_page(request):
    return render(request, "signin.html")

def signup_page(request):
    return render(request, "signup.html")

def home_page(request):
    return render(request, "home.html")

def price_history_page(request):
    return render(request, "price_history.html")

def scraping_page(request):
    return render(request, "scraping.html")

def subscription_page(request):
    return render(request, "subscription.html")

def unsubscription_page(request):
    return render(request, "unsubscription.html")

def search_bicycle_page(request):
    return render(request, "search_bicycle.html")