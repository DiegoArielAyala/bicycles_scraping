from django.urls import path

from apps.scraping.test.send_email import TestEmailView

from .views import auth, bicycles, scraping, subscription

urlpatterns = [
    path("signin/", auth.SigninView.as_view(), name="signin_api"),
    path("signup/", auth.SignupView.as_view(), name="signup_api"),
    path("signout/", auth.SignoutView.as_view(), name="signout_api"),
    path("scraping/", scraping.ScrapingView.as_view(), name="scraping_api"),
    path("search_bicycle/", bicycles.SearchBicycleView.as_view(), name="search_bicycle_api"),
    path("price_history/<str:reference>/", bicycles.ShowPriceHistoryView.as_view(), name="price_history_api"),
    path("subscription/", subscription.SubscriptionView.as_view(), name="subscription_api"),
    path("unsubscription/", subscription.UnsubscribeView.as_view(), name="unsubscription_api"),
    path("test-email/", TestEmailView.as_view(), name="test-email"),
]