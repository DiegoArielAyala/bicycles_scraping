from django.urls import path

from apps.alerts.api.v1.views import subscription

urlpatterns = [
    path("subscription/", subscription.SubscriptionView.as_view(), name="subscription_api"),
    path("unsubscription/", subscription.UnsubscribeView.as_view(), name="unsubscription_api"),
]