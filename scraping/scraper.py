import asyncio
import django
import random
import re
import os

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

os.environ.setdefault("DJANGO_SETTINGS_MODULE","bicyclesscraping.settings")
django.setup()

from .constants import USER_AGENTS
from .models import Bicycle
from .utils import create_bicycles

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
    print("run_scraper function start")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        context = await browser.new_context(user_agent=random.choice(USER_AGENTS))
        stealth = Stealth()
        await stealth.apply_stealth_async(context)
        counter = int(start_page)

        # Array with all bicycles references in the DB for the current web
        bicycle_references_in_db = await sync_to_async(
            lambda: list(Bicycle.objects.filter(web=web).values_list("reference", flat=True,))
            )()

        while counter <= last_page:
            url = (urls[web]["bicycles_endpoint"]).format(counter)
            print(f"url: {url}")
            bicycle_references_not_in_web = []

            try:
                html = await get_html(context, url)
                if not html:
                    print(f"Page {counter} didn't load. Exit loop")
                    break
                soup = BeautifulSoup(html, "html.parser")
                product_elements_html = await get_product_elements_html(web, soup, counter)
                
                if not product_elements_html:
                    break
                                
                # Call to create_bicycles and return an arrays with referencies that not exist in web
                """
                Revisar que el flujo de esta variable bicycle_references_in_db sea correcto. Aparentemente bicycle_references_not_in_web solo se estaria quedando con las referencias que no existen de la ultima iteracion de create_bicycles y deberia ir acumulando todas las referencias de cada iteracion, para luego pasarselo a delete_bicycles 
                """
                """
                Buscar la forma que no se ejecute create_bicycles si la bicicleta ya se encuentra en la DB, y solo se agregue el precio de hoy (ejecutando add_todays_price)
                """
                bicycle_references_not_in_web = await create_bicycles(product_elements_html, web, bicycle_references_in_db, context)
                print(f"bicycle_references_not_in_web: {bicycle_references_not_in_web}")
                
                counter += 1

                # Check if total searched bicycle's numbers is equal to actual search bicycle's number
                if web == "escapa" and is_last_page(soup):
                    print("No hay más productos, finalizando.")
                    break

            except Exception as e:
                print(f"Error en la página {counter}: {e}")
                break
        
        # Delete bicycles that no longer exists
        if delete:
            await delete_bicycles(bicycle_references_not_in_web, context)

    print("Scraping terminado.")

async def get_html(context, url):
    """
    Returns page HTML as string, or None if something failed.
    """
    list_page = await context.new_page()
    html = None
    
    try:
        await asyncio.sleep(random.uniform(3, 6))
        await list_page.goto(url, wait_until="domcontentloaded")

        try:
            await list_page.wait_for_function("() => !document.body.innerText.includes('Verifying you are human')", timeout=180000)
        except Exception:
            print(f"Error cloudflare challenge no se resolvio")

        html = await list_page.content()
    
    finally:
        await list_page.close()
    
    return html

async def get_product_elements_html(web, soup, counter):
    if web == "biking_point":
        if is_last_product(soup):
            print("No hay más productos, finalizando.")
            return []
        else:
            product_elements_html = soup.find_all("li", class_="item product product-item")
            print(f"Página {counter}: Encontradas {len(product_elements_html)} bicicletas")
            return product_elements_html
    
    if web == "escapa":
        product_elements_html = soup.find_all("article", class_="product-miniature js-product-miniature mb-3")
        return product_elements_html

def is_last_page(soup):
    search_number = (re.search(r"Mostrando \d+-(\d+)", soup.text)).group(1)
    number_bicycles = (re.search(r"de (\d+) producto", soup.text)).group(1)
    print(search_number)
    print(number_bicycles)
    return number_bicycles == search_number

async def delete_bicycles(bicycle_references_not_in_web, context):
    print("Deleting bicycles")
    for reference in bicycle_references_not_in_web:
        try:
            page = await context.new_page()
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


"""
Funcion original para preguntarle al chat despues si los cambios que hice son los correctos

async def run_scraper(start_page, last_page, web=None, delete=False):
    print("run_scraper function start")
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        counter = int(start_page)

        # Array with all bicycles references in the DB for the current web
        bicycle_references = await sync_to_async(
            lambda: list(Bicycle.objects.filter(web=web).values_list("reference", flat=True,))
            )()

        while counter <= last_page:

            url = (urls[web]["bicycles_endpoint"]).format(counter)
            print(f"url: {url}")
            try:
                list_page = await browser.new_page(user_agent=random.choice(USER_AGENTS))
                
                stealth = Stealth()
                await stealth.apply_stealth_async(list_page)
                await asyncio.sleep(random.uniform(3, 6))
                await list_page.goto(url, wait_until="domcontentloaded")

                try:
                    await list_page.wait_for_function("() => !document.body.innerText.includes('Verifying you are human')", timeout=180000)
                except:
                    print(f"Error cloudflare challenge no se resolvio")

                html = await list_page.content()
                soup = BeautifulSoup(html, "html.parser")

                if web == "biking_point":
                    if (
                        "No podemos encontrar productos que coincida con la selección."
                        in soup.text
                    ):
                        print("No hay más productos, finalizando.")
                        break
                    else:
                        bicycles = soup.find_all("li", class_="item product product-item")
                        print(f"Página {counter}: Encontradas {len(bicycles)} bicicletas")
                
                if web == "escapa":
                    bicycles = soup.find_all("article", class_="product-miniature js-product-miniature mb-3")
                                
                # Call to create_bicycles and return an arrays with referencies that not exist yet in the DB
                bicycle_references = await create_bicycles(bicycles, USER_AGENTS, web, bicycle_references)
                print(f"bicycle_references: {bicycle_references}")
                
                counter += 1

                if web == "escapa":
                    search_number = (re.search(r"Mostrando \d+-(\d+)", soup.text)).group(1)
                    number_bicycles = (re.search(r"de (\d+) producto", soup.text)).group(1)
                    print(search_number)
                    print(number_bicycles)
                    if (number_bicycles == search_number):
                        print("No hay más productos, finalizando.")
                        break

            except Exception as e:
                print(f"Error en la página {counter}: {e}")
                break
        
        # Delete bicycles that no longer exists
        if delete:
            await delete_bicycles(bicycle_references)

        await browser.close()
    print("Scraping terminado.")
"""