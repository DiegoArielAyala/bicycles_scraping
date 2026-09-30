import logging 
from apps.scraping.models import PriceHistory, Bicycle
from apps.scraping.services.price_alerts import send_price_drop_emails, should_send_price_alert
from django.db import transaction

logger = logging.getLogger(__name__)


def update_price_histories(price_history_updates, current_prices_by_id, bicycles_by_reference):
    price_history_objects = create_price_history_objects(price_history_updates)

    new_price_histories = save_price_histories(price_history_objects)

    bicycles_objects, price_drops = prepare_current_price_updates(new_price_histories, current_prices_by_id)

    save_current_prices(bicycles_objects)

    if price_drops:
        send_price_drop_emails(price_drops)

    for price_history in price_history_updates:
        bicycles_by_reference.pop(price_history["reference"])
    
    return bicycles_by_reference

def create_price_history_objects(price_history_updates):
    price_history_objects = []
    for price_history in price_history_updates:
        price_history_objects.append(PriceHistory(bicycle_id=price_history["bicycle_id"], price=price_history["current_price"])) 
    return price_history_objects

def save_price_histories(price_history_objects):
    with transaction.atomic():
        logger.info({"event": f"Save today's PriceHistory for {len(price_history_objects)} bicycles"})

        new_price_histories = PriceHistory.objects.bulk_create(price_history_objects, update_conflicts=True, update_fields=["price"], unique_fields=["bicycle_id", "date"])

        return new_price_histories

def prepare_current_price_updates(new_price_histories, current_prices_by_id):
    bicycles_objects = []
    price_drops = []

    for price_history in new_price_histories:
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

def save_current_prices(bicycles_objects):
    logger.info({"event": f"Updating current_price for {len(bicycles_objects)} bicycles"})
    Bicycle.objects.bulk_update(bicycles_objects, ["current_price"])