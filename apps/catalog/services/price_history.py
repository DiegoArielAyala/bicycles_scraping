import logging 

from django.db import transaction

from apps.alerts.services.price_alerts import should_send_price_alert
from apps.catalog.models import PriceHistory, Bicycle

logger = logging.getLogger(__name__)


def prepare_price_history_objects(price_history_updates):
    price_history_objects = []
    for price_history in price_history_updates:
        price_history_objects.append(PriceHistory(bicycle_id=price_history["bicycle_id"], price=price_history["current_price"])) 
    return price_history_objects

def prepare_current_price_updates(price_history_objects, current_prices_by_id):
    bicycles_objects = []
    price_drops = []

    for price_history in price_history_objects:
        current_price = current_prices_by_id[price_history.bicycle_id]
        if price_history.price != current_price:
            bicycles_objects.append(Bicycle(id=price_history.bicycle_id, current_price=price_history.price))
            if should_send_price_alert(current_price, price_history.price):
                price_drops.append({
                    "bicycle_id": price_history.bicycle_id,
                    "old_price": current_price,
                    "new_price": price_history.price,
                })
    
    return bicycles_objects, price_drops

def save_prices(price_history_objects, bicycles_objects):
    with transaction.atomic():
        logger.info({"event": "save_prices", "count": {len(price_history_objects)}})

        PriceHistory.objects.bulk_create(price_history_objects, update_conflicts=True, update_fields=["price"], unique_fields=["bicycle_id", "date"])

        Bicycle.objects.bulk_update(bicycles_objects, ["current_price"])


    