from datetime import timedelta
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.scraping.models import Bicycle
from apps.scraping.services.bicycles import update_last_seen_at

class TestBicycles(APITestCase):
    def setUp(self):
        Bicycle.objects.create(reference="11111", current_price=1000, last_seen_at=timezone.localdate()-timedelta(days=4))
        self.price_history_updates = [{
        "reference":"11111",
        "bicycle_id":1,
        }]

    def test_update_last_seen_at(self):
        update_last_seen_at(self.price_history_updates)
