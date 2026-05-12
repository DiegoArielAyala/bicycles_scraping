from django.shortcuts import render

def signin(request):
    return render(request, "signin.html")

def signup(request):
    return render(request, "signup.html")

def home(request):
    return render(request, "home.html")

def price_history(request):
    return render(request, "price_history.html")

def scraping(request):
    return render(request, "scraping.html")

def subscription(request):
    return render(request, "subscription.html")

def unsubscription(request):
    return render(request, "unsubscription.html")

def search_bicycle(request):
    return render(request, "search_bicycle.html")