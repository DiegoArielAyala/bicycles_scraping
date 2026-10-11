from apps.accounts.views import pages
from django.urls import path


urlpatterns = [
    path("signin/", pages.signin_page, name="signin"),
    path("signup/", pages.signup_page, name="signup"),
    path("auth/google/callback/", pages.google_callback_page, name="google_signin"),
]
