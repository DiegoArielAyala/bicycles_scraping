import logging

from asgiref.sync import sync_to_async
from django.db import transaction
from apps.scraping.forms import BicycleForm
from apps.scraping.models import Bicycle, PriceHistory
from core.exceptions import InvalidFormError
from datetime import datetime
from decimal import Decimal


url = "https://www.bikingpoint.es/es/"
search_endpoint = "catalogsearch/result/?q={}"
headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
    "Accept-Encoding": "gzip, deflate, br",
    "Accept-Language": "es-ES,es;q=0.9",
    "Connection": "keep-alive",
    "Upgrade-Insecure-Requests": "1",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
    "Sec-Fetch-User": "?1",
    "Referer": "https://www.google.com/",
}
MINIMUM_PRICE_DROP = Decimal("50.00")

logger = logging.getLogger(__name__)



def validated_bicycle_form(bicycle_name, bicycle_img, bicycle_price, bicycle_href, bicycle_reference, web):
    bicycle_form = BicycleForm({
        "name": bicycle_name,
        "img": bicycle_img,
        "current_price": bicycle_price,
        "url": bicycle_href,
        "reference": bicycle_reference,
        "web": web
    })

    if not bicycle_form.is_valid():
        raise InvalidFormError(bicycle_form.errors)

    return bicycle_form

def save_new_bicycle(validated_bicycle_forms):
    with transaction.atomic():
        new_bicycles = Bicycle.objects.bulk_create(validated_bicycle_forms)
        new_price_histories = []
        today = datetime.now().date()

        for new_bicycle in new_bicycles:
            new_price_histories.append(PriceHistory(bicycle_id=new_bicycle.id, date=today, price=new_bicycle.current_price))
            
        create_price_history(new_price_histories)

def create_price_history(new_price_histories):
    PriceHistory.objects.bulk_create(new_price_histories, update_conflicts=True, update_fields=["price"], unique_fields=["bicycle", "date"])

def get_href(product_element):
    a_tag = product_element.find("a")
    if not a_tag or not a_tag.get("href"):
        return None
    bicycle_href = a_tag.get("href")
    logger.debug(f"Bicycle href: {bicycle_href}")
    return bicycle_href


def add_todays_price(bicycles_objects):
    PriceHistory.objects.bulk_create(bicycles_objects)

def should_send_price_alert(old_price, new_price):

    old_price = Decimal(old_price)
    new_price = Decimal(new_price)

    difference = old_price - new_price

    return difference >= MINIMUM_PRICE_DROP

def is_last_product(soup):
    return "No podemos encontrar productos que coincida con la selección." in soup.text
