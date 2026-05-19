import uuid

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
    updated_at = models.DateTimeField(auto_now=True)

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
    created_at = models.DateTimeField(auto_now_add=True)

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
    email=models.EmailField(max_length=120)
    bicycle=models.ForeignKey(Bicycle, on_delete=models.CASCADE, related_name="subscription")

    unsubscribe_token=models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        app_label="scraping"

        constraints = [
            models.UniqueConstraint(
                fields=["email", "bicycle"],
                name="unique_email_bicycle_subscription"
            )
        ]

    def __str__(self):
        return f"{self.email} - {self.bicycle.name}"
    