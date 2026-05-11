import logging
import asyncio
import plotly.graph_objects as go

from asgiref.sync import sync_to_async
from datetime import datetime

from ..apps.scraping.context_managers import log_context
from ..apps.scraping.decorators import log_function
from ..apps.scraping.dto import BicycleDTO
from .exceptions import PriceNotFoundError, ReferenceNotFoundError, InvalidFormError
from ..apps.scraping.forms import BicycleForm
from ..apps.scraping.metrics import increment
from ..apps.scraping.models import Bicycle, PriceHistory
from ..apps.scraping.strategies.factory import strategy_factory


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
                bicycle_price = strategy.get_price(product_element, bicycle_reference)
            except ReferenceNotFoundError:
                logger.warning({"event": "reference_not_found", "web": web})
                continue
            except PriceNotFoundError:
                increment("PriceNotFoundError", web=web)
                logger.warning({"event": "get_todays_price_error", "web": web, "reference": bicycle_reference})
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
    bicycle_price = strategy.get_price(product_element, bicycle_reference)
    bicycle_name, bicycle_img = strategy.get_product_info(product_element, bicycle_reference)
    
    if bicycle_price is None:
        logger.warning({"event": "price_not_found", "web": web, "reference": bicycle_reference})
        increment("price_not_found")
        return
    
    logger.debug({"event": "scraped_product", "web": web, "reference": bicycle_reference, "price": bicycle_price, "name": bicycle_name})

    bicycle = BicycleDTO(
        name=bicycle_name,
        img=bicycle_img,
        url=bicycle_href,
        reference=bicycle_reference,
        price=bicycle_price,
        web=web
    )

    bicycle_form = await sync_to_async(validated_bicycle_form)(bicycle.name, bicycle.img, bicycle.price, bicycle.url, bicycle.reference, bicycle.web)
    
    new_bicycle = await save_new_bicycle(bicycle_form)

    await save_price_history(new_bicycle, bicycle.price)


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
        logger.warning({"event": "invalid_form", "web": web, "reference": bicycle_reference})
        raise InvalidFormError(bicycle_form.errors)

    return bicycle_form

async def save_new_bicycle(bicycle_form):
    new_bicycle = await sync_to_async(bicycle_form.save)()
    increment("new_bike_created", web=new_bicycle.web)
    logger.info({"event": "bicycle_created", "id": new_bicycle.id, "reference": new_bicycle.reference})
    return new_bicycle

async def save_price_history(new_bicycle, bicycle_price):
    price_history = PriceHistory(
        bicycle = new_bicycle,
        date = datetime.now().date(),
        price = bicycle_price,
    )
    await sync_to_async(price_history.save)()
    logger.info({"event": "price_history_saved", "reference": new_bicycle.reference, "price": bicycle_price})


def get_href(product_element):
    a_tag = product_element.find("a")
    if not a_tag or not a_tag.get("href"):
        return None
    bicycle_href = a_tag.get("href")
    logger.debug(f"Bicycle href: {bicycle_href}")
    return bicycle_href

async def clean_duplicates(reference):
    logger.debug("Cleaning duplicates")
    try:
        bicycles = await sync_to_async(lambda: list(
            Bicycle.objects.filter(reference=reference).order_by("id")
        ))()
        if len(bicycles) > 1:
            duplicates = bicycles[1:]
            logger.info({"event": "deleting_duplicates", "reference": reference, "count": len(duplicates)})
            results = await asyncio.gather(*[sync_to_async(bicycle.delete)() for bicycle in duplicates], return_exceptions=True)

            success = 0
            errors = 0

            for result in results:
                if isinstance(result, Exception):
                    errors += 1
                    logger.error({"event": "deleted_duplicate_error", "reference": reference, "error": str(result)})
                else:
                    success += 1

            logger.info({"event": "deleted_duplicates", "reference": reference, "success": success, "errors": errors})
            increment("deleted_bicycle", count=success)
            if errors >= 1:
                increment("deleted_errors", count=errors)
        else:
            logger.info({"event": "not_found_duplicates", "reference": reference})
    except Exception as e:
        logger.exception(f"Error searching Bicycle in DB: {e}")


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


async def update_current_price(bicycle_object, bicycle_price):
    new_price = round(float(bicycle_price), 2)
    current_price = round(bicycle_object.current_price, 2)

    if new_price != current_price:
        old_price = bicycle_object.current_price
        bicycle_object.current_price = new_price
        await sync_to_async(bicycle_object.save)()
        logger.info(f"{bicycle_object.reference} changed price from {old_price} to {new_price}")


def is_last_product(soup):
    return "No podemos encontrar productos que coincida con la selección." in soup.text

def get_price_graphic(dates, prices, bicycle):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=dates, y=prices, mode="lines+markers", name="Precio"))
    fig.update_layout(
        plot_bgcolor="#212529",
        paper_bgcolor="#212529",
        title={
            "text": f"{bicycle.name}",
            "x": 0.5,
            "xanchor": "center",
            "font": {"size": 24, "family": "system-ui"},
        },
        xaxis=dict(
            title=dict(text="Date", font=dict(color="#f8f9fa")),
            color="#f8f9fa",
            gridcolor="#343a40",
            linecolor="#f8f9fa",
            tickfont=dict(color="#f8f9fa"),
        ),
        yaxis=dict(
            title=dict(text="Price (€)", font=dict(color="#f8f9fa")),
            color="#f8f9fa",
            gridcolor="#343a40",
            linecolor="#f8f9fa",
            tickfont=dict(color="#f8f9fa"),
        ),
        hovermode="x unified",
        font=dict(
            family="system-ui, -apple-system, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif",
            size=16,
            color="#f8f9fa",
        ),
        margin=dict(t=100, b=40, l=40, r=20),
    )
    graphic = fig.to_html()

    return graphic