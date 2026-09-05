from django.conf import settings
from django.shortcuts import render

def signin_page(request):
    return render(request, "signin.html", {
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "google_redirect_uri": settings.GOOGLE_OAUTH_CALLBACK_URL,
    })

def signup_page(request):
    return render(request, "signup.html")

def home_page(request):
    return render(request, "home.html")

def price_history_page(request, reference):
    return render(request, "price_history.html")

def scraping_page(request):
    return render(request, "scraping.html", {
        "cron_token": settings.CRON_SECRET_TOKEN,
    })

def subscription_page(request):
    reference = request.GET.get("reference")
    return render(request, "subscription.html", {"reference": reference})

def unsubscription_page(request):
    return render(request, "unsubscription.html")

def search_bicycle_page(request):
    return render(request, "search_bicycle.html")

def google_callback_page(request):
    return render(request, "google_callback.html")

def my_subscriptions_page(request):
    return render(request, "my_subscriptions.html")