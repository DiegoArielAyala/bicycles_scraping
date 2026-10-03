from django.contrib import admin
from apps.scraping.models import Bicycle, PriceHistory, Subscription

# Register your models here.


admin.site.register(Bicycle)
admin.site.register(PriceHistory)
admin.site.register(Subscription)
