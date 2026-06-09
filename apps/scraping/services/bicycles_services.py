import logging

from asgiref.sync import sync_to_async
from apps.scraping.context_managers import log_context
from apps.scraping.decorators import log_function
from apps.scraping.dto import BicycleDTO
from apps.scraping.emails.services import EmailService
from apps.scraping.models import Bicycle, Subscription
from apps.scraping.services.metrics import increment
from apps.scraping.strategies.factory import strategy_factory
from core.exceptions import PriceNotFoundError, ReferenceNotFoundError, InvalidFormError
from core.utils import get_href, add_todays_price, clean_duplicates, save_new_bicycle, validated_bicycle_form, save_price_history, should_send_price_alert
from decimal import Decimal

logger = logging.getLogger(__name__)

"""
    Refactorizando create_bicycles:
    - Solucionar el problema que no se encuentran correctamente las imagenes en la web de biking point.
    - en Number of Bicycle references saved in DB: no se estan removiendo las bicicletas que son scrapeadas
    - Mejorar la arquitectura del proyecto
"""

@log_function
async def create_bicycles(product_elements_html, web, bicycle_references_in_db):
    bicycle_references_in_db = set(bicycle_references_in_db)

    logger.debug({"event": "create_bicycles_start", "web": web, "items": len(product_elements_html)})
    bicycle_index = 1
    strategy = strategy_factory(web)

    for product_element in product_elements_html:
        bicycle_index += 1
        
        with log_context("process_product", web=web, index=bicycle_index):

            bicycle_href = get_href(product_element)
            if not bicycle_href:
                logger.error({"event": "href_not_found", "web": web})
                continue
            
            try:
                bicycle_reference = strategy.get_reference(product_element)
                bicycle_price = strategy.get_price(product_element)
            except ReferenceNotFoundError:
                logger.warning({"event": "reference_not_found", "web": web})
                continue
            except PriceNotFoundError:
                increment("PriceNotFoundError", web=web)
                logger.warning({"event": "price_not_found_error", "web": web, "reference": bicycle_reference})
                continue
            
            # Buscar en la DB si existe esa referencia
            try:
                bicycle_object = await sync_to_async(lambda: Bicycle.objects.get(reference=bicycle_reference))()

            # Create new Bicycle if it not exist yet
            except Bicycle.DoesNotExist:
                with log_context("create_new_bicycle", web=web, reference=bicycle_reference):
                    logger.info({"event": "creating_bicycle", "reference": bicycle_reference})
                    await create_new_bicycle(product_element, web, bicycle_href, bicycle_reference, strategy)
                    continue
                    
            await sync_to_async(add_todays_price)(bicycle_object, bicycle_price)
            # Update Current Price if it changed
            await update_current_price(bicycle_object, bicycle_price)
                
            bicycle_references_in_db.discard(int(bicycle_reference))
            logger.debug({"event": "discard_reference", "items": len(bicycle_references_in_db)})

            with log_context("clean_duplicates", reference=bicycle_reference):
                await clean_duplicates(bicycle_reference)
 
    return bicycle_references_in_db


@log_function
async def create_new_bicycle(product_element, web, bicycle_href, bicycle_reference, strategy):
    bicycle_price = strategy.get_price(product_element)
    bicycle_name, bicycle_img = strategy.get_product_info(product_element)
    
    if bicycle_price is None:
        logger.warning({"event": "price_not_found", "web": web, "reference": bicycle_reference})
        increment("price_not_found")
        return
    
    logger.debug({"event": "scraped_product", "web": web, "reference": bicycle_reference, "price": bicycle_price, "name": bicycle_name})

    """ Agregar un try/except para capturar errores en la creación del objeto bicicleta, y loggear el error con el reference para poder debuggear después. """

    bicycle = BicycleDTO(
        name=bicycle_name,
        img=bicycle_img,
        url=bicycle_href,
        reference=bicycle_reference,
        price=bicycle_price,
        web=web
    )

    try:
        bicycle_form = await sync_to_async(validated_bicycle_form)(bicycle.name, bicycle.img, bicycle.price, bicycle.url, bicycle.reference, bicycle.web)
    except InvalidFormError as e:
        logger.warning({"event": "invalid_form", "web": web, "reference": bicycle_reference, "error": e})
        return
    
    new_bicycle = await save_new_bicycle(bicycle_form)

    await save_price_history(new_bicycle, bicycle.price)

async def update_current_price(bicycle_object, bicycle_price):
    new_price = Decimal(bicycle_price)
    old_price = Decimal(bicycle_object.current_price)

    if new_price != old_price:

        bicycle_object.current_price = new_price

        await sync_to_async(bicycle_object.save)()

        logger.info(
            f"{bicycle_object.reference} changed "
            f"price from {old_price} to {new_price}"
        )

        if should_send_price_alert(old_price, new_price):

            subscriptions = await sync_to_async(
                lambda: list(
                    Subscription.objects.filter(
                        bicycle=bicycle_object
                    )
                )
            )()

            for subscription in subscriptions:

                await sync_to_async(
                    EmailService.send_price_drop_email
                )(
                    subscription=subscription,
                    bicycle=bicycle_object,
                    old_price=old_price,
                    new_price=new_price,
                )