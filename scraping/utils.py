import logging

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404
from datetime import datetime
from playwright_stealth.stealth import Stealth

from .forms import BicycleForm
from .models import Bicycle, PriceHistory

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
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)
logger = logging.getLogger(__name__)

"""
    Refactorizando create_bicycles:
    - Solucionar el problema que no se encuentran correctamente las imagenes en la web de biking point.
    - Intentar ver si se puede hacer que NO se busquen todos los datos de las bicicletas antes de comprobar si ya existe en la base de datos, para optimizar el scraping.
        - Separar la obtencion de la referencia de get_basic_bicycle_data para poder obtener solo la referencia y ahi buscar si esta la bicicleta en la DB.
        - Crear una funcion que cuando tenga la referencia, la busque en la DB. Esta funcion se tiene que ejecutar en create_bicycles. Del resultado de esta funcion depende como se sigue ejecutando create_bicycles.
            - Si existe la bicicleta -> Ejecutar add_todays_price
            - Si no existe la bicicleta -> Continuar con create_bicycles (es decir, ejecutar get_basic_bicycle_data y guardar la nueva bicicleta en la DB)
"""

async def create_bicycles(product_elements_html, web, bicycle_references_in_db, context):
    logger.debug(f"create_bicycles started for {web} with {len(product_elements_html)} product_elements_html finded on the page")
    bicycle_index = 1

    for bicycle in product_elements_html:
        logger.debug(f"Bicycle references saved in DB: {bicycle_references_in_db}")
        logger.debug(f"Number of Bicycle references saved in DB: {len(bicycle_references_in_db)}")
        logger.debug(f"Bicycle_index: {bicycle_index}")
        bicycle_index+=1
        
        bicycle_href = get_href(bicycle)
        if not bicycle_href:
            logger.error(f"Href not found in web {web} ")
            continue
        
        bicycle_reference = await get_bicycle_reference(bicycle, bicycle_href, context, web)
        if not bicycle_reference:
            logger.error(f"Bicycle reference not found for href {bicycle_href}")
            continue

        try:
            # Buscar en la DB si existe esa referencia
            try:
                bicycle_object = await sync_to_async(lambda: get_object_or_404(Bicycle, reference=bicycle_reference))()

                try:
                    bicycle_price = get_todays_price(bicycle, web, bicycle_reference)
                    if bicycle_price is None:
                        logger.error(f"Error during get todays price for reference {bicycle_reference}")
                        continue
                    await add_todays_price(bicycle_object, bicycle_price)
                except:
                    logger.error(f"Error during add todays price for reference {bicycle_reference}")
                    continue

                # Update Current Price if it changed
                await update_current_price(bicycle_object, bicycle_price)
                
            # Create new Bicycle if it not exist yet
            except:
                logger.info(f"Creating a new bicycle for reference {bicycle_reference}")
                create_new_bicycle(bicycle, web, bicycle_references_in_db, bicycle_href, bicycle_reference)

            try:
                logger.debug(f"Before delete reference: {len(bicycle_references_in_db)}")
                bicycle_references_in_db.remove(int(bicycle_reference))
                logger.debug(f"After delete reference: {len(bicycle_references_in_db)}")
            except (ValueError, TypeError):
                logger.debug(f"Reference {bicycle_reference} not in bicycle_references_in_db")
                continue
            
            await clean_duplicates(bicycle_reference)
                        
        except Exception as e:
            print(f"Error durante el guardado de Bicycle o add_todays_price {e}")
            
    return bicycle_references_in_db
    

async def create_new_bicycle(bicycle, web, bicycle_href, bicycle_reference):
    bicycle_price = get_todays_price(bicycle, web, bicycle_reference)
    if bicycle_price is None:
        logger.error(f"Error during get todays price for reference {bicycle_reference}")
        return
    
    bicycle_data = await get_basic_bicycle_data(bicycle, web, bicycle_reference)
    if bicycle_data is None:
        logger.error(f"Error during get basic data for reference {bicycle_reference}")
        return

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
        new_bicycle = await sync_to_async(bicycle_form.save)()
        logger.info(f"Created new bike. Id: {new_bicycle.id}")

        try:
            price_history = PriceHistory(
                bicycle=new_bicycle,
                date=datetime.now().date(),
                price=bicycle_price,
            )
            await sync_to_async(price_history.save)()
            logger.info(f"Price History saved for {new_bicycle.reference}")
        except Exception:
            logger.exception(f"Error creating price_history for {new_bicycle.reference}")

    else:
        logger.error(f"Invalid form: {bicycle_form.errors}")


async def get_basic_bicycle_data(bicycle, web, bicycle_reference):
    bicycle_name = "Bicycle"
    bicycle_img = None
        
    if web == "biking_point":
        name_tag = bicycle.find("strong", class_="product-item-name")
    elif web == "escapa":
        name_tag = bicycle.find("h3", class_="h3 product-title")
    else:
        name_tag = None

    if name_tag is None:
        logger.warning(f"Name not found for reference {bicycle_reference}")
    else:
        bicycle_name = name_tag.text.strip()
        logger.debug(f"Bicycle name: {bicycle_name}")

    if web == "biking_point":
        img_attr = "src"
    elif web == "escapa":
        img_attr = "data-src"

    img_tag = bicycle.find("img")
    bicycle_img = img_tag.get(img_attr) if img_tag else None

    if not img_tag:
        logger.warning(f"Image not found for reference {bicycle_reference}")  
    elif not bicycle_img:
        logger.warning(f"Image attribute not found for reference {bicycle_reference}")
    else:
        logger.debug(f"Bicycle image: {bicycle_img}")
    
    return bicycle_name, bicycle_img


async def get_bicycle_reference(bicycle, bicycle_href, context, web):
    if web == "biking_point":
        html = await get_html(bicycle_href, context)
        if html is None:
            return None
        
        soup = BeautifulSoup(html, "html.parser")
        sku_div = soup.find("div", itemprop="sku")
        if not sku_div:
            return None

        bicycle_reference = sku_div.text.strip()
    elif web == "escapa":
        bicycle_reference = bicycle.get("data-id-product")
    else:
        logger.error(f"Web {web} is not valid")
        return None

    logger.debug(f"Bicycle reference: {bicycle_reference}" )
    return bicycle_reference


def get_href(bicycle):
    a_tag = bicycle.find("a")
    if not a_tag or not a_tag.get("href"):
        return None
    bicycle_href = a_tag.get("href")
    logger.debug(f"Bicycle href: {bicycle_href}")
    return bicycle_href


async def get_html(bicycle_href, context):
    detail_page = await context.new_page()
    stealth = Stealth()
    await stealth.apply_stealth_async(detail_page)
    try:
        response = await detail_page.goto(bicycle_href, wait_until="domcontentloaded")
        if response.status == 200:
            html = await detail_page.content()
            return html
    except Exception as e:
        print("Error during get reference", e)
    finally:
        await detail_page.close()

"""
async def get_bicycle_reference(bicycle_references_in_db, bicycle_href):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        detail_page = await browser.new_page(user_agent=random.choice(USER_AGENTS))
        stealth = Stealth()
        await stealth.apply_stealth_async(detail_page)
        try:
            await asyncio.sleep(random.uniform(3, 6))
            response = await detail_page.goto(bicycle_href, wait_until="domcontentloaded")
            print(f"Response status: {response.status}")
            if response.status == 200:
                html = await detail_page.content()
                bicycle_reference = (
                    BeautifulSoup(html, "html.parser")
                    .find("div", itemprop="sku")
                    .text
                )
                print(f"bicycle_reference: {bicycle_reference}" )
                try:
                    bicycle_references_in_db.remove(int(bicycle_reference))
                except ValueError:
                    print(f"Reference {bicycle_reference} not in bicycle_references_in_db")
                await clean_duplicates(bicycle_reference)
            return bicycle_reference
        except Exception as e:
            print("Error during get reference", e)
"""

async def clean_duplicates(reference):
    print("Cleaning duplicates")
    try:
        bicycles = await sync_to_async(lambda: list(
            Bicycle.objects.filter(reference=reference).order_by("id")
        ))()
        if len(bicycles) > 1:
            for bicycle in bicycles[1:]:
                print(f"Delete {bicycle} from DB")
                await sync_to_async(bicycle.delete)()
        else:
            print(f"No duplicates found for reference: {reference}")
    except Exception as e:
        print("Error al buscar bicicletas en Bicycle.objects: ", e)


async def add_todays_price(bicycle_object, bicycle_price):
    """ Funcion para obtener bicycle_price"""
    new_price_history = PriceHistory(
        bicycle=bicycle_object, date=datetime.now().date(), price=bicycle_price
    )
    await sync_to_async(new_price_history.save)()
    logger.debug(f"New price history saved: {new_price_history}")

# Recibe la soup de una bicicleta y retorna su precio actual
def get_todays_price(bicycle, web, bicycle_reference):
    try:
        if web == "biking_point":
            prices = bicycle.find_all("span", class_="price")
            if not prices:
                raise ValueError(f"Price span not found for reference {bicycle_reference}")
            price_text = prices[0].text
        
        elif web == "escapa":
            price_span = bicycle.find("span", class_= "price current-price-discount") or bicycle.find("span", class_= "price")
            if not price_span:
                raise ValueError(f"Price span not found for reference {bicycle_reference}")
            price_text = price_span.text
        
        else:
            raise ValueError(f"Unknown web {web}")

        return price_text.replace("\xa0", "").replace("€", "").replace(".", "").replace(",", ".").strip()
    
    except ValueError as e:
        logging.warning(f"Price not found for reference {bicycle_reference} | {type(e).__name__} - {e}")
        return None
    
    except Exception as e:
        logging.error(f"Unexpected error for reference {bicycle_reference} | {type(e).__name__} - {e}", exc_info=True)
        return None

async def update_current_price(bicycle_object, bicycle_price):
    new_price = round(float(bicycle_price), 2)
    current_price = round(bicycle_object.current_price, 2)

    if new_price != current_price:
        old_price = bicycle_object.current_price
        bicycle_object.current_price = new_price
        await sync_to_async(bicycle_object.save)()
        logger.info(f"{bicycle_object.reference} changed price from {old_price} to {new_price}")
