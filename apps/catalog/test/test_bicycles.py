from datetime import timedelta
<<<<<<< HEAD
from bs4 import Tag
=======
>>>>>>> origin/master
from django.utils import timezone
from rest_framework.test import APITestCase

from apps.catalog.models import Bicycle, PriceHistory
from apps.catalog.services.bicycles import process_scraped_prices, update_last_seen_at
from apps.scraping.dtos import ScrapedPrices

class TestBicycles(APITestCase):
    def setUp(self):
        bicycle = Bicycle.objects.create(reference="11111", current_price=1000, last_seen_at=timezone.localdate()-timedelta(days=4), web="test_web")
        self.price_history_updates = [PriceHistory(
        bicycle_id = bicycle.id,
        price = 1000,
        )]
        self.scraped_prices = []
        scraped_price = ScrapedPrices("11111", 1000, Tag("soup", name=""))
        self.scraped_prices.append(scraped_price)
        scraped_price = ScrapedPrices("22222", 2000, Tag("soup", name=""))
        self.scraped_prices.append(scraped_price)

    def test_update_last_seen_at(self):
        update_last_seen_at(self.price_history_updates)
        bicycle = Bicycle.objects.get(reference="11111")
        self.assertEqual(bicycle.last_seen_at,timezone.localdate())

    def test_process_scraped_prices(self):
        self.assertTrue(Bicycle.objects.filter(reference="11111").exists())
        new_scraped_prices, price_history_updates, current_prices_by_id = process_scraped_prices(self.scraped_prices, "test_web")
        self.assertEqual(len(new_scraped_prices), 1)
        self.assertEqual(new_scraped_prices[0].reference, "22222")
        self.assertEqual(len(price_history_updates), 1)
        self.assertEqual(price_history_updates[0]["reference"], "11111")


