import asyncio
import django
import os
import random
import logging

from playwright.async_api import async_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError
from bs4 import BeautifulSoup
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.scraping.models import Bicycle
from apps.scraping.constants import USER_AGENTS
from apps.scraping.strategies import urls

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelsanme)s - %(name)s - %(message)s "
)
logger = logging.getLogger(__name__)

# Use Playwright to get the correct img url from each bicycle reference

async def update_bicycles_image_urls():
    references = await get_bicycles_references_from_db()

    for reference in references:
        try:
            html = await fetch_biking_point_html(reference)
        except PlaywrightTimeoutError:
            print(f"Timeout Error for reference {reference}")
            continue
        except PlaywrightError as e:
            print(f"Playwright error with reference {reference}: {e}")
        except Exception as e:
            print(f"Unexpected error for reference {reference}: {e}")
             
        img_url = extract_image_url(html)
        if img_url is None:
            logger.warning(f"Img url not found for reference {reference}")
            continue
        try:
            bicycle = await get_bicycle_by_reference(reference)
        except ObjectDoesNotExist:
            print(f"Referencia {reference} no existe, continua al siguiente")
            continue
        if bicycle.img == img_url:
            print(f"Img for reference {reference} is correct")
            continue
        bicycle.img = img_url
        await sync_to_async(lambda: bicycle.save())()
        print(f"Img url for Bicycle reference {reference} saved.")

        # Crear el cron para ejecutar el run_scraper de produccion.
        # Agregar los try/except necesarios
        
async def get_bicycles_references_from_db():
    bicycles_references = await sync_to_async(lambda: list(Bicycle.objects.filter(web="biking_point").values_list("reference", flat=True)))()
    return bicycles_references

async def fetch_biking_point_html(reference):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args= ["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"])
        page = await browser.new_page(user_agent=random.choice(USER_AGENTS))
        await page.goto(urls["biking_point"]["search_endpoint"].format(reference))
        html = await page.content()
        return html

def extract_image_url(html):
    soup = BeautifulSoup(html, "html.parser")
    img_tag = soup.find("img", class_="img-fluid")
    if not img_tag:
        return None
    else:
        img_url = img_tag.get("src")
        return img_url

async def get_bicycle_by_reference(reference):
    bicycle = await sync_to_async(lambda: Bicycle.objects.get(reference=reference))()
    return bicycle


asyncio.run(update_bicycles_image_urls())