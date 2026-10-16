from django.urls import path

from apps.catalog.views import pages

urlpatterns = [
    path("search_bicycle/", pages.search_bicycle_page, name="search_bicycle"),
    path("price_history/<str:reference>", pages.price_history_page, name="price_history"),
    
]