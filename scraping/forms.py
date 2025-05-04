from django import forms
from .models import Bicycle, PriceHistory

class BicycleForm(forms.ModelForm):
    class Meta:
        model = Bicycle
        fields = ["name", "img", "current_price", "url", "reference"]
        

class PriceHistoryForm(forms.ModelForm):
    class Meta:
        model = PriceHistory
        fields = ["bicycle", "date", "price"]