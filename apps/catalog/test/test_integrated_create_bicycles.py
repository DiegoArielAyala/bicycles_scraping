from decimal import Decimal
from django.db import IntegrityError, transaction
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.catalog.models import Bicycle, PriceHistory
from apps.catalog.services.bicycles import create_new_bicycles
from apps.scraping.dtos import ScrapedBycicles


class TestCreateBicycles(APITestCase):
    def setUp(self):
        self.new_bicycles = [
            ScrapedBycicles("11111", 1000, "Bike Test 1", "test_web", "https://bikingpoint.es/bike-1", timezone.localdate(), True),
            ScrapedBycicles("22222", 2000, "Bike Test 2", "test_web", "https://bikingpoint.es/bike-2", timezone.localdate(), True),
        ]

    def test_creates_new_bicycles(self):
        create_new_bicycles(self.new_bicycles)
 
        bikes = Bicycle.objects.filter(web="test_web")
        self.assertEqual(bikes.count(), 2)
        self.assertEqual(PriceHistory.objects.count(), 2)
        bike = Bicycle.objects.get(reference="11111")
        self.assertEqual(bike.current_price, Decimal("1000.00"))
        self.assertEqual(bike.url, "https://bikingpoint.es/bike-1")
        self.assertEqual(bike.last_seen_at, timezone.localdate())
    
    def test_existing_bicycle_with_same_price(self):
        create_new_bicycles(self.new_bicycles)
        self.assertEqual(Bicycle.objects.count(), 2)

        with self.assertRaises(IntegrityError):
            with transaction.atomic():
                Bicycle.objects.create(name="bike1", current_price=1000, url="www.biking.com/bike1", reference="11111", web="test_web", last_seen_at=timezone.localdate())

        self.assertEqual(Bicycle.objects.count(), 2)
        self.assertEqual(PriceHistory.objects.count(), 2)
