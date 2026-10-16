from django.db import models
from django.utils import timezone


class Bicycle(models.Model):
    name=models.TextField(max_length=200)
    img=models.URLField(null=True, blank=True)
    current_price=models.DecimalField(max_digits=8, decimal_places=2)
    url=models.URLField()
    reference=models.CharField(max_length=30)
    web=models.TextField(max_length=30)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen_at = models.DateField()
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "scraping_bicycle"
        constraints = [
            models.UniqueConstraint(
                fields=["reference", "web"],
                name="unique_reference_per_web"
            )
        ]
        indexes = [
            models.Index(fields=["web"], name="scraping_bi_web_0f1dd8_idx"),
            models.Index(fields=["reference"], name="scraping_bi_referen_393b85_idx"),
            models.Index(fields=["current_price"], name="scraping_bi_current_2709c3_idx"),
        ]

    def __str__(self):
        return f"{self.name} - {self.id}"

class PriceHistory(models.Model):
    bicycle=models.ForeignKey(Bicycle, on_delete=models.PROTECT, related_name="price_history")
    date=models.DateField(default=timezone.now)
    price=models.DecimalField(max_digits=8, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scraping_pricehistory"
        constraints = [
            models.UniqueConstraint(
                fields=["bicycle", "date"],
                name="unique_price_per_bicycle_per_day"
                )
        ]

    def __str__(self):
        return f"{self.date} : {self.price}"

