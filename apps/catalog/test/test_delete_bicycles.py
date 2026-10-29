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
        Bicycle.objects.create(reference="11111", current_price=1000, web="test_web", last_seen_at=timezone.localdate())
        Bicycle.objects.create(reference="22222", current_price=2000, web="test_web", last_seen_at=timezone.localdate()-timedelta(days=4))

    def test_delete_bicycle(self):
        self.assertTrue(Bicycle.objects.get(reference="22222").is_active)
        delete_bicycles("test_web")
        self.assertFalse(Bicycle.objects.get(reference="22222").is_active)
    
    def test_not_delete_bicycle(self):
        delete_bicycles("test_web")
        self.assertTrue(Bicycle.objects.get(reference="11111").is_active)

    def test_new_delete_bicycle(self):
        delete_bicycles("test_web")
        bicycle1 = Bicycle.objects.get(reference="11111")
        bicycle2 = Bicycle.objects.get(reference="22222")
        self.assertTrue(bicycle1.is_active)
        self.assertFalse(bicycle2.is_active)

class DeleteBicyclesTest(TransactionTestCase):
    def setUp(self):
        self.reference = "33333"
        Bicycle.objects.create(
            name="Bicycle Test",
            img="example.com/test.jpg",
            current_price=999,
            url="example.com/test",
            reference=self.reference,
            web="test_web",
            last_seen_at=timezone.localdate() - timedelta(days=4),
        )

    def test_bicycle_deletion(self):
        self.assertEqual(Bicycle.objects.filter(reference=self.reference).count(), 1)

        delete_bicycles("test_web")

        bicycle = Bicycle.objects.get(reference=self.reference)
        self.assertFalse(bicycle.is_active)
        for conn in connections.all():
            try:
                conn.close()
            except OperationalError:
                pass
