from django.db import models
from django.utils import timezone

# Create your models here.
class Bicycle(models.Model):
    name=models.TextField(max_length=200)
    img=models.URLField(default="Image not available")
    current_price=models.DecimalField(max_digits=8, decimal_places=2)
    url=models.URLField()
    reference=models.CharField(max_length=30)
    web=models.TextField(max_length=30)

    class Meta:
        app_label="scraping"
        constraints = [
            models.UniqueConstraint(
                fields=["reference", "web"],
                name="unique_reference_per_web"
            )
        ]
        indexes = [
            models.Index(
                fields=["web"]
            ),
            models.Index(
                fields=["reference"]
            )
        ]

    def __str__(self):
        return self.name

class PriceHistory(models.Model):
    bicycle=models.ForeignKey(Bicycle, on_delete=models.CASCADE, related_name="price_history")
    date=models.DateField(default=timezone.now)
    price=models.DecimalField(max_digits=8, decimal_places=2)

    class Meta:
        app_label="scraping"
        constraints = [
            models.UniqueConstraint(
                fields=["bicycle", "date"],
                name="unique_price_per_bicycle_per_day"
                )
        ]
        indexes = [
            models.Index(fields=["bicycle", "date"])
        ]

    def __str__(self):
        return f"{self.date} : {self.price}"

class Subscription(models.Model):
    email=models.EmailField(max_length=60)
    bicycle=models.ForeignKey(Bicycle, on_delete=models.CASCADE, related_name="subscription")

    class Meta:
        app_label="scraping"

    def __str__(self):
        return self.email