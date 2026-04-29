import logging

from asgiref.sync import sync_to_async
from django.shortcuts import get_object_or_404
from django.db import DatabaseError, IntegrityError
from django.http import Http404
from datetime import datetime

from .decorators import log_function
from .exceptions import PriceNotFoundError, ReferenceNotFoundError, NameNotFoundError, ImgNotFoundError
from .forms import BicycleForm
from .metrics import increment
from .models import Bicycle, PriceHistory
from .strategies.factory import strategy_factory


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

logger = logging.getLogger(__name__)

"""
    Refactorizando create_bicycles:
    - Solucionar el problema que no se encuentran correctamente las imagenes en la web de biking point.
    - en Number of Bicycle references saved in DB: no se estan removiendo las bicicletas que son scrapeadas
    - Mejorar la arquitectura del proyecto
"""

@log_function
async def create_bicycles(product_elements_html, web, bicycle_references_in_db):
    logger.debug(f"create_bicycles started for {web} with {len(product_elements_html)} product_elements_html finded on the page")
    bicycle_index = 1
    strategy = strategy_factory(web)

    for product_element in product_elements_html:
        logger.debug(f"Number of Bicycle references saved in DB: {len(bicycle_references_in_db)}")
        logger.debug(f"Bicycle_index: {bicycle_index}")
        bicycle_index+=1
        
        bicycle_href = get_href(product_element)
        if not bicycle_href:
            logger.error({"event": "href_not_found", "web": web})
            continue
        
        try:
            bicycle_reference = strategy.get_reference(product_element)

        except ReferenceNotFoundError:
            logger.warning({"event": "reference_not_found", "web": web})
            continue
        
        # Buscar en la DB si existe esa referencia
        try:
            bicycle_object = await sync_to_async(lambda: get_object_or_404(Bicycle, reference=bicycle_reference))()

        # Create new Bicycle if it not exist yet
        except Http404:
            logger.info(f"Creating a new bicycle for reference {bicycle_reference}")
            await create_new_bicycle(product_element, web, bicycle_href, bicycle_reference, strategy)
            continue
        
        try:
            bicycle_price = strategy.get_price(product_element, bicycle_reference)
        except PriceNotFoundError:
            increment("PriceNotFoundError", web=web)
            logger.warning({"event": "get_todays_price_error", "web": web, "reference": bicycle_reference})
            continue

        await sync_to_async(add_todays_price)(bicycle_object, bicycle_price)
        # Update Current Price if it changed
        await update_current_price(bicycle_object, bicycle_price)
            
        try:
            logger.debug(f"Before delete reference: {len(bicycle_references_in_db)}")
            bicycle_references_in_db.remove(int(bicycle_reference))
            logger.debug(f"After delete reference: {len(bicycle_references_in_db)}")
        except (ValueError, TypeError):
            logger.debug(f"Reference {bicycle_reference} not in bicycle_references_in_db")
            continue
        
        await clean_duplicates(bicycle_reference)
 
    return bicycle_references_in_db
    

async def create_new_bicycle(product_element, web, bicycle_href, bicycle_reference, strategy):
    try:
        bicycle_price = strategy.get_price(product_element, bicycle_reference)
    except PriceNotFoundError:
        logger.warning({"event": "get_todays_price_error", "web": web, "reference": bicycle_reference})
        increment("price_not_found", web=web)
        return
    except Exception as e:
        logger.exception(f"Unexpected error during get todays price for reference {bicycle_reference}: {e}")
        return
    
    try:
        bicycle_data = strategy.get_product_info(product_element, bicycle_reference)
    except NameNotFoundError:
        logger.warning({"event": "name_not_found", "web": web, "reference": bicycle_reference})
        increment("name_not_found", web=web)
        bicycle_data = ("Bicycle", None)
    except ImgNotFoundError:
        logger.warning({"event": "img_not_found", "web": web, "reference": bicycle_reference})
        increment("img_not_found", web=web)
        bicycle_data = ("Bicycle", None)
    except Exception as e:
        logger.exception(f"Unexpected error during get product info for reference {bicycle_reference}: {e}")
        bicycle_data = ("Bicycle", None)

    bicycle_name, bicycle_img = bicycle_data

    bicycle_form = BicycleForm(
        {
            "name": bicycle_name,
            "img": bicycle_img,
            "current_price": bicycle_price,
            "url": bicycle_href,
            "reference": bicycle_reference,
            "web": web
        }
    )
    is_valid = await sync_to_async(bicycle_form.is_valid)()
    if is_valid:
        try:
            new_bicycle = await sync_to_async(bicycle_form.save)()
            increment("New bike created", web=web)
            logger.info(f"Created new bike. Id: {new_bicycle.id}")
        except Exception as e:
            logger.exception(f"Unexpecting error saving new bike: {e}")

        try:
            price_history = PriceHistory(
                bicycle=new_bicycle,
                date=datetime.now().date(),
                price=bicycle_price,
            )
            await sync_to_async(price_history.save)()
            logger.info(f"Price History saved for {new_bicycle.reference}")
        except IntegrityError as e:
            logger.warning(f"Duplicate price history for {new_bicycle.reference}: {e}")
        except DatabaseError as e:
            logger.error(f"DB error saving price history: {e}")
            raise
        except Exception as e:
            logger.exception(f"Unexpecting error saving price history: {e}")
            raise

        """ Continuar con el punto 4 del chat Branch-Plan de estudio"""
    else:
        logger.error(f"Invalid form: {bicycle_form.errors}")


async def get_basic_bicycle_data(product_element, web, bicycle_reference):
    bicycle_name = "Bicycle"
    bicycle_img = None
        
    if web == "biking_point":
        name_tag = product_element.find("strong", class_="product-item-name")
        img_attr = "src"
    elif web == "escapa":
        name_tag = product_element.find("h3", class_="h3 product-title")
        img_attr = "src"
    else:
        name_tag = None

    if name_tag is None:
        logger.warning(f"Name not found for reference {bicycle_reference}")
    else:
        bicycle_name = name_tag.text.strip()
        logger.debug(f"Bicycle name: {bicycle_name}")

    img_tag = product_element.find("img")
    bicycle_img = img_tag.get(img_attr) if img_tag else None

    if not img_tag:
        logger.warning(f"Image not found for reference {bicycle_reference}")  
    elif not bicycle_img:
        logger.warning(f"Image attribute not found for reference {bicycle_reference}")
    else:
        logger.debug(f"Bicycle image: {bicycle_img}")
    
    return bicycle_name, bicycle_img

"""
def get_bicycle_reference(product_element, web):
    if web == "biking_point":
        img_tag = product_element.find("img")
        if img_tag is None:
            return None
        data_src = img_tag.get("data-src")
        match = re.search(r"/(\d+)_([^/]+)\.jpg", data_src)
        
        bicycle_reference = match.group(1)

    elif web == "escapa":
        bicycle_reference = product_element.get("data-id-product")
    else:
        logger.error(f"Web {web} is not valid")
        return None

    logger.debug(f"Bicycle reference: {bicycle_reference}" )
    return bicycle_reference
"""


def get_href(product_element):
    a_tag = product_element.find("a")
    if not a_tag or not a_tag.get("href"):
        return None
    bicycle_href = a_tag.get("href")
    logger.debug(f"Bicycle href: {bicycle_href}")
    return bicycle_href

async def clean_duplicates(reference):
    print("Cleaning duplicates")
    try:
        bicycles = await sync_to_async(lambda: list(
            Bicycle.objects.filter(reference=reference).order_by("id")
        ))()
        if len(bicycles) > 1:
            for bicycle in bicycles[1:]:
                print(f"Delete {bicycle.reference} from DB")
                await sync_to_async(bicycle.delete)()
                increment("Deleted bicycle", web=bicycle.web)
        else:
            print(f"No duplicates found for reference: {reference}")
    except Exception as e:
        print(f"Error searching Bicycle in DB: {e}")


def add_todays_price(bicycle_object, bicycle_price):
    """ Funcion para obtener bicycle_price"""
    new_price_history = PriceHistory(
        bicycle=bicycle_object, date=datetime.now().date(), price=bicycle_price
    )
    PriceHistory.objects.update_or_create(
        bicycle=bicycle_object, 
        date=datetime.now().date(), 
        defaults={"price":bicycle_price}
        )
    logger.debug(f"New price history saved: {new_price_history}")

# Recibe la soup de una bicicleta y retorna su precio actual
"""Funcion movida a las clases especificas de cada web"""
"""
def get_todays_price(product_element, web, bicycle_reference):
    try:
        if web == "biking_point":
            prices = product_element.find_all("span", class_="price")
            if not prices:
                raise PriceNotFoundError(f"Price span not found for reference {bicycle_reference}")
            price_text = prices[0].text
        
        elif web == "escapa":
            price_span = product_element.find("span", class_= "price current-price-discount") or product_element.find("span", class_= "price")
            if not price_span:
                raise PriceNotFoundError(f"Price span not found for reference {bicycle_reference}")
            price_text = price_span.text
        
        else:
            raise PriceNotFoundError(f"Unknown web {web}")

        cleaned_price = (
            price_text
            .replace("\xa0", "")
            .replace("€", "")
            .replace(".", "")
            .replace(",", ".")
            .strip()
        )
        
        if not cleaned_price:
            raise PriceNotFoundError(f"Price text is empty after cleaning for reference {bicycle_reference}")

        return cleaned_price
    
    except Exception as e:
        logger.exception(f"Unexpected error for reference {bicycle_reference}: {e}")
        raise
"""

async def update_current_price(bicycle_object, bicycle_price):
    new_price = round(float(bicycle_price), 2)
    current_price = round(bicycle_object.current_price, 2)

    if new_price != current_price:
        old_price = bicycle_object.current_price
        bicycle_object.current_price = new_price
        await sync_to_async(bicycle_object.save)()
        logger.info(f"{bicycle_object.reference} changed price from {old_price} to {new_price}")


