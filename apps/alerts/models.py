import uuid

from django.contrib.auth import get_user_model
from django.db import models

from apps.catalog.models import Bicycle

User = get_user_model()

class Subscription(models.Model):
    email=models.EmailField(max_length=120)
    bicycle=models.ForeignKey(Bicycle, on_delete=models.PROTECT, related_name="subscriptions")
    user=models.ForeignKey(User, on_delete=models.PROTECT, related_name="subscriptions", null=True, blank=True)
    unsubscribe_token=models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at=models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "scraping_subscription"
        constraints = [
            models.UniqueConstraint(
                fields=["user", "bicycle"],
                name="unique_user_bicycle_subscription"
            )
        ]

        indexes = [
            models.Index(fields=["created_at"], name="scraping_su_created_d3fd50_idx"),
        ]

    def __str__(self):
        return f"{self.email} - {self.bicycle} - {self.user}"
    