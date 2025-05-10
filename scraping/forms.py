from django import forms
from .models import Bicycle, PriceHistory, Subscription

class BicycleForm(forms.ModelForm):
    class Meta:
        model = Bicycle
        fields = ["name", "img", "current_price", "url", "reference"]


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["email", "reference"]