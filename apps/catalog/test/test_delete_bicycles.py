import asyncio

from asgiref.sync import sync_to_async
from datetime import timedelta
from django.db import connections
from django.db.utils import OperationalError
from django.test import TransactionTestCase
from django.utils import timezone
from rest_framework.test import APITestCase
from unittest.mock import patch

from apps.catalog.models import Bicycle
from apps.catalog.services.bicycles import delete_bicycles


class TestDeleteBicycles(APITestCase):
    def setUp(self):
        Bicycle.objects.create(reference="11111", current_price=1000, web="biking_point", last_seen_at=timezone.localdate())
        Bicycle.objects.create(reference="22222", current_price=2000, web="biking_point", last_seen_at=timezone.localdate()-timedelta(days=4))

    async def test_delete_bicycle(self):
        with patch("apps.scraping.strategies.biking_point.BikingPointStrategy.bicycle_exists", return_value=False):
            self.assertTrue(await sync_to_async(lambda: Bicycle.objects.filter(reference="11111").exists())())
            await delete_bicycles(["11111"], None)
            self.assertFalse(await sync_to_async(lambda: Bicycle.objects.filter(reference="11111").exists())())
    
    async def test_not_delete_bicycle(self):
        with patch("apps.scraping.strategies.biking_point.BikingPointStrategy.bicycle_exists", return_value=True):
            await delete_bicycles(["11111"], None)
            self.assertTrue(await sync_to_async(lambda: Bicycle.objects.filter(reference="11111").exists())())

    def test_new_delete_bicycle(self):
        delete_bicycles()
        bicycle1 = Bicycle.objects.get(reference="11111")
        bicycle2 = Bicycle.objects.get(reference="22222")
        self.assertTrue(bicycle1.is_active)
        self.assertFalse(bicycle2.is_active)

class DeleteBicyclesTest(TransactionTestCase):
    def setUp(self):
        # Crear una bicicleta
        self.reference = 11122
        self.bicycle = Bicycle.objects.create(
            name="Bicicleta Test",
            img="example.com/test.jpg",
            current_price=999,
            url="example.com/test",
            reference=self.reference,
            web="biking_point",
        )

    def test_bicycle_deletion(self):
        self.assertEqual(Bicycle.objects.filter(reference=self.reference).count(), 1)

        asyncio.run(delete_bicycles([self.reference]))

        self.assertEqual(Bicycle.objects.filter(reference=self.reference).count(), 0)

        for conn in connections.all():
            try:
                conn.close()
            except OperationalError:
                pass