from django.urls import path

from .views import user_views

urlpatterns = [
    path("api/signin", user_views.SigninView.as_view(), name="signin_api"),
    path("api/signup", user_views.SignupView.as_view(), name="signup_api"),
    path("api/signout", user_views.SignoutView.as_view(), name="signup_api"),
    path("api/sscraping", user_views.ScrapingView.as_view(), name="scraping_api"),
    path("api/search_bicycle", user_views.SearchBicycleView.as_view(), name="search_bicycle_api"),
    path("api/price_history", user_views.ShowPriceHistoryView.as_view(), name="price_history_api"),
    path("api/subscription", user_views.SubscriptionView.as_view(), name="subscription_api"),
    path("api/unsubscription", user_views.UnsubscribeView.as_view(), name="unsubscription_api"),
]