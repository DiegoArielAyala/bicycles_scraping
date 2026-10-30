from django.urls import path

from apps.alerts.views import pages

urlpatterns = [
    path("subscription/", pages.subscription_page, name="subscription"),
    path("unsubscription/", pages.unsubscription_page, name="unsubscription"),
    path("my_subscriptions/", pages.my_subscriptions_page, name="my_subscriptions"),
]