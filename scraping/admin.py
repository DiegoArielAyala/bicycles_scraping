from django.contrib import admin
from .models import Bicycle, PriceHistory

# Register your models here.


admin.site.register(Bicycle)
admin.site.register(PriceHistory)
