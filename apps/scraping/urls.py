from django.urls import path
from .views import pages

urlpatterns = [
    path("home/", pages.home, name="home"),
    path("signin/", pages.signin, name="signin"),
    path("signup/", pages.signup, name="signup"),
    path("scraping/", pages.scraping, name="scraping"),
    path("search_bicycle/", pages.search_bicycle, name="search_bicycle"),
    path("price_history/", pages.price_history, name="price_history"),
    path("subscription", pages.subscription, name="subscription"),
    path("unsubscription/", pages.unsubscription, name="unsubscription")
]