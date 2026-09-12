from apps.scraping.models import Bicycle
from django_filters import FilterSet, NumberFilter

class BicyclesFilter(FilterSet):
    min_price = NumberFilter(
        field_name="current_price",
        lookup_expr="gte"
    )

    max_price = NumberFilter(
        field_name="current_price",
        lookup_expr="lte"
    )

    class Meta:
        model = Bicycle
        fields = []