from datetime import datetime
from unittest.mock import patch
from django.db import IntegrityError
from django.test import SimpleTestCase
from rest_framework.test import APITestCase

from apps.scraping.models import Bicycle, PriceHistory
from apps.scraping.services.bicycles_services import clean_duplicates_bicycles, create_new_bicycles
from core.utils import create_price_history

class TestCreateNewBicycles(APITestCase):
    def setUp(self):
        self.new_bicycles = [{
            "name": "Bike Test 1",
            "current_price": 1000,
            "url": "www.biketest1.com",
            "img": "www.imagetest1.com",
            "reference": "11111",
            "web": "test",
        }, {
            "name": "Bike Test 2",
            "current_price": 1000,
            "url": "www.biketest2.com",
            "img": "www.imagetest2.com",
            "reference": "22222",
            "web": "test",
        }]
    
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
            "apps.scraping.services.bicycles_services.PriceHistory.objects.bulk_create",
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
        create_price_history(price_history)
        self.assertEqual(PriceHistory.objects.get(bicycle_id=bicycle.id).price, 500)

class TestCleanDuplicatedBicycles(SimpleTestCase):
    def setUp(self):
        self.new_bicycles = [{
            "name": "Bike Test 1",
            "current_price": 1000,
            "url": "www.biketest1.com",
            "img": "www.imagetest1.com",
            "bicycle_reference": "11111",
            "web": "test",
        }, {
            "name": "Bike Test 2",
            "current_price": 1000,
            "url": "www.biketest2.com",
            "img": "www.imagetest2.com",
            "bicycle_reference": "11111",
            "web": "test",
        }]
    
    def test_clean_duplicated_bicycles(self):
        self.assertEqual(len(self.new_bicycles), 2)
        self.cleaned_bicycles = clean_duplicates_bicycles(self.new_bicycles)
        self.assertEqual(len(self.cleaned_bicycles), 1)
        self.assertEqual(self.cleaned_bicycles[0]["name"], "Bike Test 1")

class TestCreateBicycles(APITestCase):
    def setUp(self):    
        self.new_test_bicycles = [{
            "name": "Bike Test 1",
            "current_price": 1000,
            "url": "www.biketest1.com",
            "img": "www.imagetest1.com",
            "reference": "11111",
            "web": "test",
        }, {
            "name": "Bike Test 2",
            "current_price": 2000,
            "url": "www.biketest2.com",
            "img": "www.imagetest2.com",
            "reference": "22222",
            "web": "test",
        }]
