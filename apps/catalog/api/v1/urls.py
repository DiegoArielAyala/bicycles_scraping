from django.urls import path

from apps.catalog.api.v1.views import bicycles

urlpatterns = [
    path("search_bicycle/", bicycles.SearchBicycleView.as_view(), name="search_bicycle_api"),
    path("price_history/<str:reference>/", bicycles.ShowPriceHistoryView.as_view(), name="price_history_api"),
]