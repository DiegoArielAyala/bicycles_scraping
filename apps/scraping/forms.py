from django import forms
from apps.scraping.models import Bicycle, Subscription

class BicycleForm(forms.ModelForm):
    class Meta:
        model = Bicycle
        fields = ["name", "img", "current_price", "url", "reference", "web"]


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["email"]