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

from ..constants import USER_AGENTS
from .metrics import get_metrics
from ..models import Bicycle
from ..strategies.factory import strategy_factory
from ....core.utils import create_bicycles


logger = logging.getLogger(__name__)

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
            
            strategy = strategy_factory(web)

            while counter <= last_page:
                url = strategy.get_list_url(counter)
                logger.debug(f"Url: {url}")

                try:
                    html = await get_html(page, url)
                    if not html:
                        logger.debug(f"Page {counter} didn't load. Exit loop")
                        break
                    soup = BeautifulSoup(html, "html.parser")
                    # product_elements_html = await get_product_elements_html(web, soup, counter)
                    product_elements_html = await strategy.get_product_elements_html(web, soup)
                    
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

def is_last_page(soup):
    search_number = (re.search(r"Mostrando \d+-(\d+)", soup.text)).group(1)
    number_bicycles = (re.search(r"de (\d+) producto", soup.text)).group(1)
    logger.debug(search_number)
    logger.debug(number_bicycles)
    return number_bicycles == search_number

async def delete_bicycles(bicycle_references_not_in_web, page):
    logger.info({"event": "deleting_bicycles"})
    for reference in bicycle_references_not_in_web:
        try:
            bicycle = await sync_to_async(lambda: get_object_or_404(Bicycle, reference=reference))()
            strategy = strategy_factory(bicycle.web)

            # Look for reference on the corresponding page
            bicycle_exist = await strategy.bicycle_exists(page, reference)
            
            # If bicycle not exist, delete it
            if not bicycle_exist:
                await sync_to_async(bicycle.delete)()
                logger.info({"event": "bicycle_deleted", "reference": reference})

        except Exception as e:
            logger.error({"event": "delete_bicycle_error", "reference": reference, "error": str(e)})



