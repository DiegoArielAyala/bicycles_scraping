import logging

from dataclasses import asdict
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone

from apps.alerts.services.price_alerts import send_price_drop_emails
from apps.catalog.forms import validated_bicycle_form
from apps.catalog.services.price_history import create_price_history_objects, prepare_current_price_updates, save_current_prices, save_price_histories
from apps.scraping.dtos import ScrapedBycicles
from apps.catalog.models import Bicycle, PriceHistory
from core.exceptions import InvalidFormError
from core.logging import log_function, log_context

logger = logging.getLogger(__name__)


def process_scraped_prices(scraped_prices, web):
    bicycles_by_reference, current_prices_by_id = get_bicycles_data_from_db(web)
    new_scraped_prices = []
    price_history_updates = []

    for scraped_price in scraped_prices:
        if scraped_price.reference not in bicycles_by_reference:
            scraped_prices.append(scraped_price)

        price_history_updates.append({
            "reference":scraped_price.reference,
            "current_price":scraped_price.current_price,
            "bicycle_id":bicycles_by_reference[scraped_price.reference]["bicycle_id"],
            })
    
    return new_scraped_prices, price_history_updates, current_prices_by_id

@log_function
def process_scraped_bicycles(new_bicycles: list[ScrapedBycicles], price_history_updates, current_prices_by_id):
    logger.debug({"event": "process_scraped_bicycles", "new_bicycles": len(new_bicycles), "price_history_updates": len(price_history_updates)})

    create_new_bicycles(new_bicycles)

    if price_history_updates:
        update_existing_bicycles(price_history_updates, current_prices_by_id)


def update_existing_bicycles(price_history_updates, current_prices_by_id):
    price_history_objects = create_price_history_objects(price_history_updates)

    new_price_histories = save_price_histories(price_history_objects)

    bicycles_objects, price_drops = prepare_current_price_updates(new_price_histories, current_prices_by_id)

    save_current_prices(bicycles_objects)

    update_last_seen_at(price_history_updates)

    if price_drops:
        send_price_drop_emails(price_drops)
        
def create_new_bicycles(new_bicycles):
    with log_context("create_new_bicycles"):
        validated_bicycle_forms = []
        
        for new_bicycle in new_bicycles:
            new_bicycle_dict = asdict(new_bicycle)
            try:
                bicycle_form = validated_bicycle_form(new_bicycle_dict)
                validated_bicycle_forms.append(bicycle_form.save(commit=False))
            except InvalidFormError as e:
                logger.warning({"event": "invalid_form", "reference": new_bicycle_dict["reference"], "error": e})
                continue
        
        save_new_bicycles(validated_bicycle_forms)


def save_new_bicycles(validated_bicycle_forms):
    logger.info({"event": "saving_new_bicycles", "number_of_new_bicycles": len(validated_bicycle_forms)})
    with transaction.atomic():
        new_bicycles = Bicycle.objects.bulk_create(validated_bicycle_forms)
        new_price_histories = []
        today = datetime.now().date()

        for new_bicycle in new_bicycles:
            new_price_histories.append(PriceHistory(bicycle_id=new_bicycle.id, date=today, price=new_bicycle.current_price))
            
        PriceHistory.objects.bulk_create(new_price_histories, update_conflicts=True, update_fields=["price"], unique_fields=["bicycle", "date"]) 

def get_bicycles_data_from_db(web):
    bicycles = list(Bicycle.objects.filter(web=web).values_list("reference", "id", "current_price"))

    bicycles_by_reference = {}
    current_prices_by_id = {}

    for reference, bicycle_id, current_price in bicycles:
        bicycles_by_reference[reference] = {
            "bicycle_id": bicycle_id,
            "current_price": current_price,
        }
        current_prices_by_id[bicycle_id] = current_price

    return bicycles_by_reference, current_prices_by_id

def delete_bicycles(web):
    logger.info({"event": "start_inactive_bicycles"})

    cutoff = timezone.localdate() - timedelta(days=2)
    inactive_bicycles = Bicycle.objects.filter(web=web, is_active=True, last_seen_at__lt=cutoff).update(is_active=False)
      
    logger.info({"event": "inactive_bicycles", "count": len(inactive_bicycles), "inactive bicycles": inactive_bicycles})


def update_last_seen_at(price_history_updates):
    bicycles_ids = [update["bicycle_id"] for update in price_history_updates]
    
    bicycles = Bicycle.objects.filter(id__in=bicycles_ids).update(last_seen_at=timezone.localdate(), is_active=True)

    logger.info({"event": "update_last_seen_at", "count": bicycles})