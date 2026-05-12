"""
URL configuration for bicyclesscraping project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.scraping.urls")),
    path("api/", include("apps.scraping.api.urls"))
]

from apps.scraping.api.views import views

from .views import user_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.home, name="home"),
    path("signup/", user_views.SignupView.as_view(), name="signup"),
    path("signin/", user_views.SigninView.as_view(), name="signin"),
    path("signout/", user_views.SignoutView.as_view(), name="signout"),
    path("scraping/", user_views.ScrapingView.as_view(), name="scraping"),
    path("search_bicycle/", user_views.SearchBicycleView.as_view(), name="search_bicycle"),
    path("price_history/<str:reference>", user_views.ShowPriceHistoryView.as_view(), name="price_history"),
    path("subscription/", user_views.SubscriptionView.as_view(), name="subscription"),
    path("unsubscription/", user_views.UnsubscribeView.as_view(), name="unsubscription"),
]
