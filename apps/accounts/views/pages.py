from django.conf import settings
from django.shortcuts import render

def signin_page(request):
    return render(request, "signin.html", {
        "google_client_id": settings.GOOGLE_CLIENT_ID,
        "google_redirect_uri": settings.GOOGLE_OAUTH_CALLBACK_URL,
    })

def signup_page(request):
    return render(request, "signup.html")

def google_callback_page(request):
    return render(request, "google_callback.html")