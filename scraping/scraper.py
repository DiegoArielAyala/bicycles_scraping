import asyncio
import django
import random
import re
import os
import logging

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

os.environ.setdefault("DJANGO_SETTINGS_MODULE","bicyclesscraping.settings")
django.setup()

from .constants import USER_AGENTS
from .metrics import get_metrics
from .models import Bicycle
from .utils import create_bicycles


logger = logging.getLogger(__name__)

urls = {
    "escapa": {
        "bicycles_endpoint": "https://www.biciescapa.com/es/bicicletas/?en-stock=1&page={}",
        "web": "https://www.biciescapa.com/es/"
    },
    "biking_point": {
        "bicycles_endpoint": "https://www.bikingpoint.es/es/bicicletas.html/?p={}",
        "search_endpoint": "https://www.bikingpoint.es/es/catalogsearch/result/?q={}",
    }
}


async def run_scraper(start_page, last_page, web=None, delete=False):
    logger.info("run_scraper function start")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1366, "height": 768},
            locale="es-ES"
            )
        page = await context.new_page()

        try:
            stealth = Stealth()
            await stealth.apply_stealth_async(context)
            counter = int(start_page)

        # Array with all bicycles references in the DB for the current web
            bicycle_references_in_db = await sync_to_async(
                lambda: list(Bicycle.objects.filter(web=web).values_list("reference", flat=True,))
                )()

            while counter <= last_page:
                url = (urls[web]["bicycles_endpoint"]).format(counter)
                logger.debug(f"Url: {url}")

                try:
                    html = await get_html(page, url)
                    if not html:
                        logger.debug(f"Page {counter} didn't load. Exit loop")
                        break
                    soup = BeautifulSoup(html, "html.parser")
                    product_elements_html = await get_product_elements_html(web, soup, counter)
                    
                    if not product_elements_html:
                        break
                                    
                    # Call to create_bicycles and return an arrays with referencies that not exist in web

                    bicycle_references_in_db = await create_bicycles(product_elements_html, web, bicycle_references_in_db)
                    
                    counter += 1

                    # Check if total searched bicycle's numbers is equal to actual search bicycle's number
                    if web == "escapa" and is_last_page(soup):
                        logger.info("No hay más productos, finalizando.")
                        break

                except Exception as e:
                    logger.error(f"Error en la página {counter}: {e}")
                    break

        # Delete bicycles that no longer exists
            if delete:
                await delete_bicycles(bicycle_references_in_db, page)
        finally:
            await page.close()
            await context.close()
            await browser.close()

    get_metrics()    
    logger.info("Scraping terminado.")

async def get_html(page, url):
    """
    Returns page HTML as string, or None if something failed.
    """
    html = None
    
    try:
        await page.goto(url, wait_until="networkidle", timeout=30000)
        html = await page.content()

        if "cdn-cgi/challenge-platform" in html:
            logger.error("Cloudflare challenge detected")

    except Exception as e:
        logger.debug(f"Error during get html: {e}")
    
    return html

async def get_product_elements_html(web, soup, counter):
    if web == "biking_point":
        if is_last_product(soup):
            logger.info("No hay más productos, finalizando.")
            return []
        else:
            product_elements_html = soup.find_all("li", class_="item product product-item")
            logger.debug(f"Página {counter}: Encontradas {len(product_elements_html)} bicicletas")
            return product_elements_html
    
    if web == "escapa":
        product_elements_html = soup.find_all("article", class_="product-miniature js-product-miniature mb-3")
        return product_elements_html

def is_last_page(soup):
    search_number = (re.search(r"Mostrando \d+-(\d+)", soup.text)).group(1)
    number_bicycles = (re.search(r"de (\d+) producto", soup.text)).group(1)
    logger.debug(search_number)
    logger.debug(number_bicycles)
    return number_bicycles == search_number

async def delete_bicycles(bicycle_references_not_in_web, page):
    logger.info("Deleting bicycles")
    for reference in bicycle_references_not_in_web:
        try:
            bicycle = await sync_to_async(lambda: get_object_or_404(Bicycle, reference=reference))()

            # Search reference on the corresponding page
            bicycle_exist = True
            if bicycle.web == "biking_point":
                url = urls["biking_point"]["search_endpoint"]
                await page.goto(url.format(reference))
                content = await page.content()
                if "La búsqueda no ha devuelto ningún resultado." in content:
                    bicycle_exist = False

            elif bicycle.web == "escapa":
                url = urls["escapa"]["web"]
                await page.goto(url)
                try:
                    await page.click("button#onetrust-accept-btn-handler", timeout=3000)
                except:
                    pass

                await page.fill("input[name='s']", str(reference))
                await asyncio.sleep(random.uniform(3, 6))
                await page.wait_for_selector("div.dfd-card-flag", timeout=5000)

                content = await page.content()
                soup = BeautifulSoup(content, "html.parser")
                try:
                    div = soup.find("div", class_="dfd-card-flag", attrs={"data-availability":"out-of-stock"})
                
                    if div.text.strip() == "Agotado" or "Prueba de nuevo con otra búsqueda…" in soup.text:
                        bicycle_exist = False
                except Exception as e:
                    print(f"Error finding bicycle in Escapa: {e}")

            # If bicycle not exist, delete it
            if not bicycle_exist:
                await sync_to_async(bicycle.delete)()
                print(f"Reference {reference} was deleted from web {bicycle.web}")

        except Exception as e:
            print("Error during delete bicycle: ", e)


def is_last_product(soup):
    return "No podemos encontrar productos que coincida con la selección." in soup.text
