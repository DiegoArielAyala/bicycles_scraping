import django
import os
from playwright.async_api import async_playwright
import random
from bs4 import BeautifulSoup
import asyncio
from asgiref.sync import sync_to_async
from django.core.exceptions import ObjectDoesNotExist

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bicyclesscraping.settings")
django.setup()

from scraping.models import Bicycle
from scraping.views import USER_AGENTS, urls


# Use Playwright to get the correct img url from each bicycle reference

async def update_bicycles_image_urls():
    references = await get_bicycles_references_from_db()

    for reference in references:
        html = await fetch_biking_point_html(reference)
        try:
            img_url = extract_image_url(html)
        except AttributeError:
            print(f"No se encontro la img_url para la referencia {reference}")
            continue
        try:
            bicycle = await get_bicycle_by_reference(reference)
        except ObjectDoesNotExist:
            print(f"Referencia {reference} no existe, continua al siguiente")
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
    img_url = soup.find("img", class_="img-fluid")["src"]
    return img_url

async def get_bicycle_by_reference(reference):
    bicycle = await sync_to_async(lambda: Bicycle.objects.get(reference=reference))()
    return bicycle


asyncio.run(update_bicycles_image_urls())