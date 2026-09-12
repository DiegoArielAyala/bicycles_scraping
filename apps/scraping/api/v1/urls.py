from apps.scraping.api.v1.views import auth, bicycles, scraping, admin
from apps.scraping.api.v1.views import subscription
from apps.scraping.api.v1.views.auth import GoogleLogin
from django.urls import path, include

urlpatterns = [
    path("signin/", auth.SigninView.as_view(), name="signin_api"),
    path("signup/", auth.SignupView.as_view(), name="signup_api"),
    path("signout/", auth.SignoutView.as_view(), name="signout_api"),
    path("scraping/", scraping.ScrapingView.as_view(), name="scraping_api"),
    path("search_bicycle/", bicycles.SearchBicycleView.as_view(), name="search_bicycle_api"),
    path("price_history/<str:reference>/", bicycles.ShowPriceHistoryView.as_view(), name="price_history_api"),
    path("subscription/", subscription.SubscriptionView.as_view(), name="subscription_api"),
    path("unsubscription/", subscription.UnsubscribeView.as_view(), name="unsubscription_api"),
    path("auth/", include("dj_rest_auth.urls")),
    path("auth/registration/", include("dj_rest_auth.registration.urls")),
    path("auth/google/", GoogleLogin.as_view(), name="google_signin_api"),
    path("me/", auth.MeView.as_view(), name="me_api"),
    path("admin/subscriptions/", admin.AdminSubscriptionsView.as_view(), name="admin_subscriptions_api"),
    path("admin/users/", admin.AdminUsersView.as_view(), name="admin_users_api")
]