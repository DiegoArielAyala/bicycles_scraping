from django_filters import FilterSet, NumberFilter

from apps.catalog.models import Bicycle


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