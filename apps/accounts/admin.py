from django.contrib import admin
from apps.catalog.models import Bicycle, PriceHistory
from apps.alerts.models import Subscription

# Register your models here.


admin.site.register(Bicycle)
admin.site.register(PriceHistory)
admin.site.register(Subscription)
