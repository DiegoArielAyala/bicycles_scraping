from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.catalog.models import Bicycle, PriceHistory
from apps.catalog.services.bicycles import update_last_seen_at

class TestBicycles(APITestCase):
    def setUp(self):
        bicycle = Bicycle.objects.create(reference="11111", current_price=1000, last_seen_at=timezone.localdate()-timedelta(days=4))
        self.price_history_updates = [PriceHistory(
        bicycle_id = bicycle.id,
        price = 1000,
        )]

    def test_update_last_seen_at(self):
        update_last_seen_at(self.price_history_updates)
        bicycle = Bicycle.objects.get(reference="11111")
        self.assertEqual(bicycle.last_seen_at,timezone.localdate())
