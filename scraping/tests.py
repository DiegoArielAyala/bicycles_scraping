from django.test import TransactionTestCase
from scraping.views import delete_bicycles
from .models import Bicycle
import asyncio
from django.db import connections
from django.db.utils import OperationalError

# Create your tests here.

# Crear la funcion de crear una bicicleta

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
