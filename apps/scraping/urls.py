from django.urls import path

from apps.scraping.views import pages

urlpatterns = [
    path("scraping/", pages.scraping_page, name="scraping"),
]