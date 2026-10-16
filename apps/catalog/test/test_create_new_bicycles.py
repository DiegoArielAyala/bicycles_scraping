from datetime import datetime
from django.db import IntegrityError
from django.utils import timezone
from rest_framework.test import APITestCase
from unittest.mock import patch

from apps.catalog.models import Bicycle, PriceHistory
from apps.catalog.services.bicycles import create_new_bicycles
from apps.catalog.services.price_history import save_price_histories
from apps.scraping.dtos import ScrapedBycicles

class TestCreateNewBicycles(APITestCase):
    def setUp(self):
        self.new_bicycles = [ScrapedBycicles("11111", 1000, "Bike Test 1", "test",  "www.biketest1.com", timezone.localdate(), True), ScrapedBycicles("22222", 2000, "Bike Test 2", "test",  "www.biketest2.com", timezone.localdate(), True)]
        
    def test_create_new_bicycles(self):
        create_new_bicycles(self.new_bicycles)
        bicycles = Bicycle.objects.filter(web="test")
        self.assertEqual(bicycles.count(), 2)
        for bicycle in bicycles:
            self.assertIsNotNone(bicycle.id)
            self.assertTrue(PriceHistory.objects.filter(bicycle_id=bicycle.id).exists())
        self.assertEqual(PriceHistory.objects.filter(bicycle__web="test").count(), 2)
    
    def test_create_new_bike_rollback(self):
        with patch(
            "apps.catalog.services.bicycles.PriceHistory.objects.bulk_create",
            side_effect=IntegrityError,
        ):
            with self.assertRaises(IntegrityError):
                create_new_bicycles(self.new_bicycles)
        self.assertEqual(
            Bicycle.objects.filter(web="test").count(), 
            0
        )

    def test_price_history_on_conflict(self):
        create_new_bicycles(self.new_bicycles)
        bicycle = Bicycle.objects.get(reference="11111")
        price_history = [PriceHistory(bicycle_id=bicycle.id, date=datetime.now().date(), price=500)]
        self.assertEqual(PriceHistory.objects.get(bicycle_id=bicycle.id).price, 1000)
        save_price_histories(price_history)
        self.assertEqual(PriceHistory.objects.get(bicycle_id=bicycle.id).price, 500)


