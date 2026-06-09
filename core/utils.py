import logging
import asyncio
import plotly.graph_objects as go

from asgiref.sync import sync_to_async
from apps.scraping.forms import BicycleForm
from apps.scraping.models import Bicycle, PriceHistory
from apps.scraping.services.metrics import increment
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


def should_send_price_alert(old_price, new_price):

    old_price = Decimal(old_price)
    new_price = Decimal(new_price)

    difference = old_price - new_price

    return difference >= MINIMUM_PRICE_DROP

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