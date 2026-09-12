from unittest.mock import patch
from asgiref.sync import sync_to_async
from rest_framework.test import APITestCase

from apps.scraping.models import Bicycle
from apps.scraping.services.runner import delete_bicycles


class TestDeleteBicycles(APITestCase):
    def setUp(self):
        Bicycle.objects.create(reference="11111", current_price=1000, web="biking_point")

    async def test_delete_bicycle(self):
        with patch("apps.scraping.strategies.biking_point.BikingPointStrategy.bicycle_exists", return_value=False):
            self.assertTrue(await sync_to_async(lambda: Bicycle.objects.filter(reference="11111").exists())())
            await delete_bicycles(["11111"], None)
            self.assertFalse(await sync_to_async(lambda: Bicycle.objects.filter(reference="11111").exists())())
    
    async def test_not_delete_bicycle(self):
        with patch("apps.scraping.strategies.biking_point.BikingPointStrategy.bicycle_exists", return_value=True):
            await delete_bicycles(["11111"], None)
            self.assertTrue(await sync_to_async(lambda: Bicycle.objects.filter(reference="11111").exists())())
