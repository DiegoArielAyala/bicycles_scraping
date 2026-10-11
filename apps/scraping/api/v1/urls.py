from django.urls import path

from apps.scraping.api.v1.views import scraping


urlpatterns = [
    path("scraping/", scraping.ScrapingView.as_view(), name="scraping_api"),
]