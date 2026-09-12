from django.urls import path
from apps.scraping.views import pages

urlpatterns = [
    path("", pages.home_page, name="home"),
    path("signin/", pages.signin_page, name="signin"),
    path("signup/", pages.signup_page, name="signup"),
    path("scraping/", pages.scraping_page, name="scraping"),
    path("search_bicycle/", pages.search_bicycle_page, name="search_bicycle"),
    path("price_history/<str:reference>", pages.price_history_page, name="price_history"),
    path("subscription/", pages.subscription_page, name="subscription"),
    path("unsubscription/", pages.unsubscription_page, name="unsubscription"),
    path("auth/google/callback/", pages.google_callback_page, name="google_signin"),
    path("my_subscriptions/", pages.my_subscriptions_page, name="my_subscriptions"),
]