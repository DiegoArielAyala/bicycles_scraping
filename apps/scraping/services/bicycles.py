import logging

from apps.scraping.context_managers import log_context
from apps.scraping.decorators import log_function
from apps.scraping.forms import validated_bicycle_form
from apps.scraping.models import Bicycle, PriceHistory
from apps.scraping.services.metrics import increment
from apps.scraping.services.price_history import update_price_histories
from apps.scraping.strategies.factory import strategy_factory
from apps.scraping.utils.html import get_href
from core.exceptions import InvalidFormError, ReferenceNotFoundError, PriceNotFoundError
from datetime import datetime, timedelta
from django.db import transaction
from django.utils import timezone

logger = logging.getLogger(__name__)

@log_function
def create_bicycles(product_elements_html, web):
    logger.debug({"event": "create_bicycles_start", "web": web, "items": len(product_elements_html)})

    if len(product_elements_html) == 0:
        logger.debug({"event": "any_bicycle_scraped", "web": web, "items": len(product_elements_html)})
        return

    strategy = strategy_factory(web)

    bicycles_by_reference, current_prices_by_id = get_bicycles_data(web)

    price_history_updates, new_bicycles = process_product_elements_html(product_elements_html, web, strategy, bicycles_by_reference)
        
    create_new_bicycles(new_bicycles)

    if price_history_updates:
        update_price_histories(price_history_updates, current_prices_by_id)
        update_last_seen_at(price_history_updates)
        
def create_new_bicycles(new_bicycles):
    with log_context("create_new_bicycles"):
        validated_bicycle_forms = []
        for new_bicycle in new_bicycles:
            try:
                bicycle_form = validated_bicycle_form(new_bicycle)
                validated_bicycle_forms.append(bicycle_form.save(commit=False))
            except InvalidFormError as e:
                logger.warning({"event": "invalid_form", "web": new_bicycle["web"], "reference": new_bicycle["reference"], "error": e})
                continue
        
        save_new_bicycles(validated_bicycle_forms)


def process_product_elements_html(product_elements_html, web, strategy, bicycles_by_reference):
    new_bicycles = []
    price_history_updates = []
    seen_references = set()
    bicycle_index = 1

    for product_element in product_elements_html:
        bicycle_index += 1
        
        with log_context("process_product", web=web, index=bicycle_index):
            try:
                reference = strategy.get_reference(product_element)
            except ReferenceNotFoundError:
                logger.warning({"event": "reference_not_found", "web": web})
                continue
            
            if reference in seen_references:
                continue

            try:
                current_price = strategy.get_price(product_element)
            except PriceNotFoundError:
                increment("PriceNotFoundError", web=web)
                logger.warning({"event": "price_not_found_error", "web": web, "reference": reference})
                continue
            
            seen_references.add(reference)

            if reference not in bicycles_by_reference:
                new_bicycle = prepare_new_bicycle(product_element, web, reference, current_price, strategy)

                if new_bicycle:
                    new_bicycles.append(new_bicycle)
                continue

            price_history_updates.append({
                "reference":reference,
                "current_price":current_price,
                "bicycle_id":bicycles_by_reference[reference]["bicycle_id"],
                })

    return price_history_updates, new_bicycles

def prepare_new_bicycle(product_element, web, reference, current_price, strategy):
    bicycle_href = get_href(product_element)

    if not bicycle_href:
        logger.error({"event": "href_not_found", "web": web})
        return None
    
    bicycle_name, bicycle_img = strategy.get_product_info(product_element)

    return {"name": bicycle_name, "img": bicycle_img, "url":bicycle_href, "reference":reference, "current_price": current_price, "web":web, "last_seen_at":timezone.localdate()}

def save_new_bicycles(validated_bicycle_forms):
    logger.info({"event": "saving_new_bicycles", "number_of_new_bicycles": len(validated_bicycle_forms)})
    with transaction.atomic():
        new_bicycles = Bicycle.objects.bulk_create(validated_bicycle_forms)
        new_price_histories = []
        today = datetime.now().date()

        for new_bicycle in new_bicycles:
            new_price_histories.append(PriceHistory(bicycle_id=new_bicycle.id, date=today, price=new_bicycle.current_price))
            
        PriceHistory.objects.bulk_create(new_price_histories, update_conflicts=True, update_fields=["price"], unique_fields=["bicycle", "date"]) 

def get_bicycles_data(web):
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

def delete_bicycles():
    logger.info({"event": "start_inactive_bicycles"})
    bicycles = Bicycle.objects.all()
    now = timezone.localdate()

    inactive_bicycles = []
    for bicycle in bicycles:
        if now - bicycle.last_seen_at > timedelta(days=3):
            bicycle.is_active = False
            inactive_bicycles.append(bicycle)
            
    logger.info({"event": "inactive_bicycles", "inactive bicycles": inactive_bicycles})
    Bicycle.objects.bulk_update(inactive_bicycles, ["is_active"])


def update_last_seen_at(price_history_updates):
    bicycles_id = []
    for price_history in price_history_updates:
        print(price_history)
        print(type(price_history))
        bicycles_id.append(price_history["bicycle_id"])
    
    bicycles = list(Bicycle.objects.filter(id__in=bicycles_id))

    for bicycle in bicycles:
        bicycle.last_seen_at = timezone.localdate()
    
    Bicycle.objects.bulk_update(bicycles, ["last_seen_at"])