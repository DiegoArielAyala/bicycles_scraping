from decimal import Decimal
from bs4 import BeautifulSoup
from rest_framework.test import APITestCase

from apps.scraping.models import Bicycle, PriceHistory
from apps.scraping.services.bicycles_services import create_bicycles

def biking_point_card(reference, current_price, url, name="Bike Test", img="https://img.test/bike.jpg"):
    html = f'''
    <li class="item product product-item">
      <a href="{url}">
        <img src="{img}" data-src="https://cdn.test/{reference}_foto.jpg" />
        <strong class="product-item-name">{name}</strong>
        <span class="price">{current_price}</span>
      </a>
    </li>
    '''
    return BeautifulSoup(html, "html.parser").li

class TestCreateBicycles(APITestCase):
    def setUp(self):
        self.cards = [
            biking_point_card("11111", "1.000,00 €", "https://bikingpoint.es/bike-1"),
            biking_point_card("22222", "2.000,00 €", "https://bikingpoint.es/bike-2"),
        ]

    def test_creates_new_bicycles_from_html(self):
        remaining = create_bicycles(self.cards, "biking_point", [])

        bikes = Bicycle.objects.filter(web="biking_point")
        self.assertEqual(bikes.count(), 2)
        self.assertEqual(PriceHistory.objects.count(), 2)
        bike = Bicycle.objects.get(reference="11111")
        self.assertEqual(bike.current_price, Decimal("1000.00"))
        self.assertEqual(bike.url, "https://bikingpoint.es/bike-1")
        self.assertEqual(remaining, set())
    
    def test_existing_bicycle_with_same_price(self):
        new_bicycle = Bicycle.objects.create(name="bike1", current_price=1000, url="www.biking.com/bike1", reference="11111", web="biking_point")
        reference_in_db = [new_bicycle.reference]
        cards = [biking_point_card("11111", "1.000,00 €", "https://bikingpoint.es/bike-1")]

        self.assertEqual(Bicycle.objects.count(), 1)
        create_bicycles(cards, "biking_point", reference_in_db)
        self.assertEqual(Bicycle.objects.count(), 1)
        self.assertEqual(PriceHistory.objects.count(), 1)
        price_history = PriceHistory.objects.get(bicycle=new_bicycle)
        self.assertEqual(new_bicycle.current_price, price_history.price)