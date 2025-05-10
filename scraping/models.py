from django.db import models
from django.utils import timezone

# Create your models here.
class Bicycle(models.Model):
    name=models.TextField(max_length=200)
    img=models.URLField(default="Image not available")
    current_price=models.FloatField()
    url=models.URLField()
    reference=models.IntegerField()

    def __str__(self):
        return self.name

class PriceHistory(models.Model):
    bicycle=models.ForeignKey(Bicycle, on_delete=models.CASCADE, related_name="price_history")
    date=models.DateField(default=timezone.now)
    price=models.FloatField()

    def __str__(self):
        return f"{self.date} : {self.price}"

class Subscription(models.Model):
    email=models.EmailField(max_length=60)
    reference=models.IntegerField(default=None)
    bicycle=models.ForeignKey(Bicycle, on_delete=models.CASCADE, related_name="subscription")

    def __str__(self):
        return self.email