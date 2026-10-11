from django import forms

from apps.alerts.models import Subscription


class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ["email"]