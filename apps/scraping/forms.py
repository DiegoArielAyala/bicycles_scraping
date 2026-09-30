from django import forms
from apps.scraping.models import Bicycle, Subscription
from core.exceptions import InvalidFormError

class BicycleForm(forms.ModelForm):
    class Meta:
        model = Bicycle
        fields = ["name", "img", "current_price", "url", "reference", "web"]


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["email"]

def validated_bicycle_form(bicycle):
    bicycle_form = BicycleForm(bicycle)

    if not bicycle_form.is_valid():
        raise InvalidFormError(bicycle_form.errors)

    return bicycle_form