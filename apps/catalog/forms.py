from django import forms

from apps.catalog.models import Bicycle
from core.exceptions import InvalidFormError


class BicycleForm(forms.ModelForm):
    class Meta:
        model = Bicycle
        fields = ["name", "img", "current_price", "url", "reference", "web", "last_seen_at", "is_active"]

def validated_bicycle_form(bicycle):
    bicycle_form = BicycleForm(bicycle)

    if not bicycle_form.is_valid():
        raise InvalidFormError(bicycle_form.errors)

    return bicycle_form