from collections import Counter
import logging

from apps.scraping.context_managers import log_context
from apps.scraping.decorators import log_function
from apps.scraping.dto import BicycleDTO
from apps.scraping.emails.services import EmailService
from apps.scraping.models import Bicycle, PriceHistory, Subscription
from apps.scraping.services.metrics import increment
from apps.scraping.strategies.factory import strategy_factory
from core.exceptions import PriceNotFoundError, ReferenceNotFoundError, InvalidFormError
from core.utils import get_href, save_new_bicycle, validated_bicycle_form, should_send_price_alert
from django.db import transaction
from decimal import Decimal

logger = logging.getLogger(__name__)

"""
    Refactorizando create_bicycles:
    - Solucionar el problema que no se encuentran correctamente las imagenes en la web de biking point.
    - en Number of Bicycle references saved in DB: no se estan removiendo las bicicletas que son scrapeadas
    - Mejorar la arquitectura del proyecto
"""

@log_function
def create_bicycles(product_elements_html, web, bicycle_references_in_db):
    bicycle_references_in_db = set(bicycle_references_in_db)

    logger.debug({"event": "create_bicycles_start", "web": web, "items": len(product_elements_html)})
    if len(product_elements_html) == 0:
        logger.debug({"event": "any_bicycle_scraped", "web": web, "items": len(product_elements_html)})
        return

    strategy = strategy_factory(web)

    bicycles_data_in_db = list(Bicycle.objects.filter(reference__in=bicycle_references_in_db, web=web).values_list("reference", "id", "current_price"))

    reference_to_id = {
        reference: bicycle_id
        for reference, bicycle_id, current_price in bicycles_data_in_db
    }

    id_to_current_price = {
        bicycle_id: current_price
        for reference, bicycle_id, current_price in bicycles_data_in_db
    }

    price_history_updates, new_bicycles = process_product_elements_html(product_elements_html, web, strategy, bicycle_references_in_db, reference_to_id)
    
    new_bicycles_cleaned = clean_duplicates_bicycles(new_bicycles)
    
    new_bicycles_data = scrape_new_bicycles(new_bicycles_cleaned, strategy)
    create_new_bicycles(new_bicycles_data)

    if price_history_updates:
        deleted_references = []
        for price_history in price_history_updates:
            bicycle_references_in_db.discard(price_history["reference"])
            deleted_references.append(price_history["reference"])
        logger.debug({"event": "discard_references", "references": deleted_references, "remaining items": len(bicycle_references_in_db)})

        update_price_histories(price_history_updates, id_to_current_price)

    return bicycle_references_in_db

def update_price_histories(price_history_updates, id_to_current_price):
    price_history_objects = []
    for price_history in price_history_updates:
        price_history_objects.append(PriceHistory(bicycle_id=price_history["bicycle_id"], price=price_history["current_price"]))        

    price_drops = save_price_data(price_history_objects, id_to_current_price)

    send_price_drop_emails(price_drops)

def process_product_elements_html(product_elements_html, web, strategy, bicycle_references_in_db, reference_to_id):
    price_history_updates = []
    new_bicycles = []
    seen_references = set()
    bicycle_index = 1

    for product_element in product_elements_html:
        bicycle_index += 1
        
        with log_context("process_product", web=web, index=bicycle_index):
            try:
                reference = strategy.get_reference(product_element)
                current_price = strategy.get_price(product_element)
            except PriceNotFoundError:
                increment("PriceNotFoundError", web=web)
                logger.warning({"event": "price_not_found_error", "web": web, "reference": reference})
                continue
            except ReferenceNotFoundError:
                logger.warning({"event": "reference_not_found", "web": web})
                continue

            if reference not in bicycle_references_in_db:
                bicycle_href = get_href(product_element)
                if not bicycle_href:
                    logger.error({"event": "href_not_found", "web": web})
                    continue

                new_bicycles.append({"product_element":product_element, "web":web, "bicycle_href":bicycle_href, "reference":reference, "strategy":strategy})
                continue

            if reference in seen_references:
                continue

            seen_references.add(reference)
            price_history_updates.append({
                "reference":reference,
                "current_price":current_price,
                "bicycle_id":reference_to_id.get(reference),
                })
    return price_history_updates, new_bicycles

def clean_duplicates_bicycles(new_bicycles):
    seen = set()
    new_bicycles_cleaned = []
    for new_bicycle in new_bicycles:
        key = (new_bicycle["reference"], new_bicycle["web"])
        if key in seen:
            continue
        else:
            new_bicycles_cleaned.append(new_bicycle)
            seen.add(key)
    return new_bicycles_cleaned

def save_price_data(price_history_objects, id_to_current_price):
    with transaction.atomic():
        logger.info({"event": f"Creating todays PriceHistory for {len(price_history_objects)} bicycles"})

        keys = [obj.bicycle_id for obj in price_history_objects]
        duplicates = [key for key, count in Counter(keys).items() if count > 1]
        logger.debug({"event": "duplicates", "duplicates": duplicates})

        new_price_histories = PriceHistory.objects.bulk_create(price_history_objects, update_conflicts=True, update_fields=["price"], unique_fields=["bicycle_id", "date"])

        return update_current_prices(new_price_histories, id_to_current_price)

def update_current_prices(new_price_histories, id_to_current_price):
    bicycles_objects = []
    price_drops = []

    for price_history in new_price_histories:
        current_price = id_to_current_price.get(price_history.bicycle_id)
        if price_history.price != current_price:
            bicycles_objects.append(Bicycle(id=price_history.bicycle_id, current_price=price_history.price))
            old_price = Decimal(current_price)
            new_price = Decimal(price_history.price)
            if should_send_price_alert(old_price, new_price):
                price_drops.append({
                    "bicycle_id": price_history.bicycle_id,
                    "old_price": old_price,
                    "new_price": new_price,
                })

    logger.info({"event": f"Updating current_price for {len(bicycles_objects)} bicycles"})
    Bicycle.objects.bulk_update(bicycles_objects, ["current_price"])
    
    return price_drops

def send_price_drop_emails(price_drops):
    if not price_drops:
        return

    drops_by_bicycle_id = {
        drop["bicycle_id"]: drop for drop in price_drops
    }

    subscriptions = list(
            Subscription.objects.filter(
                bicycle_id__in=drops_by_bicycle_id.keys()
            ).select_related("bicycle")
        )

    for subscription in subscriptions:
        drop = drops_by_bicycle_id[subscription.bicycle_id]
        EmailService.send_price_drop_email(
            subscription=subscription,
            bicycle=subscription.bicycle,
            old_price=drop["old_price"],
            new_price=drop["new_price"],
        )


@log_function
def scrape_new_bicycles(new_bicycles, strategy):
    new_bicycles_data = []

    for new_bicycle in new_bicycles:
        logger.info({"event": "scrape_new_bicycle", "reference": new_bicycle["reference"]})
        
        product_element = new_bicycle["product_element"]
        web = new_bicycle["web"]
        reference = new_bicycle["reference"]
        
        current_price = strategy.get_price(product_element)
        bicycle_name, bicycle_img = strategy.get_product_info(product_element)
        
        if current_price is None:
            logger.warning({"event": "price_not_found", "web": web, "reference": reference})
            increment("price_not_found")
            continue

        new_bicycles_data.append({"name":bicycle_name, "img":bicycle_img, "url":new_bicycle["bicycle_href"], "reference":reference, "web":web, "current_price":current_price})
    return new_bicycles_data

def create_new_bicycles(new_bicycles_data):
    with log_context("create_new_bicycles"):
        validated_bicycle_forms = []
        for new_bicycle_data in new_bicycles_data:
        
            """ Agregar un try/except para capturar errores en la creación del objeto bicicleta, y loggear el error con el reference para poder debuggear después. """

            bicycle = BicycleDTO(
                name=new_bicycle_data["name"],
                img=new_bicycle_data["img"],
                url=new_bicycle_data["url"],
                reference=new_bicycle_data["reference"],
                price=new_bicycle_data["current_price"],
                web=new_bicycle_data["web"]
            )

            try:
                bicycle_form = validated_bicycle_form(bicycle.name, bicycle.img, bicycle.price, bicycle.url, bicycle.reference, bicycle.web)
                validated_bicycle_forms.append(bicycle_form.save(commit=False))
            except InvalidFormError as e:
                logger.warning({"event": "invalid_form", "web": new_bicycle_data["web"], "reference": new_bicycle_data["reference"], "error": e})
                continue
        
        save_new_bicycle(validated_bicycle_forms)

