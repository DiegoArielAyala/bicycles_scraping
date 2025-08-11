from bs4 import BeautifulSoup
from .forms import BicycleForm
from django.shortcuts import get_object_or_404
from datetime import datetime
from .models import Bicycle, PriceHistory
from asgiref.sync import sync_to_async
import asyncio, random
from playwright.async_api import async_playwright
from playwright_stealth.stealth import Stealth

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


async def create_bicycles(bicycles, USER_AGENTS, web, bicycles_reference):
    print("Creando lista de bicicletas")
    bicycle_index = 1
    
    print(f"bicycles_reference: {bicycles_reference}")
    for bicycle in bicycles:
        print(f"\n\nLongitud bicycles: {len(bicycles)}")
        print(f"Bicycle_index: {bicycle_index}")
        bicycle_index+=1
        bicycle_href = bicycle.find("a")["href"]
        print(f"href: {bicycle_href}")

        if web == "biking_point":
            bicycle_img = bicycle.find("img")["src"]
            bicycle_name = bicycle.find("strong", class_="product-item-name").text.strip()
            bicycle_price = get_todays_price(bicycle, web)
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
                    print(f"response status: {response.status}")
                    if response.status == 200:
                        html = await detail_page.content()
                        bicycle_reference = (
                            BeautifulSoup(html, "html.parser")
                            .find("div", itemprop="sku")
                            .text
                        )
                        print(f"bicycle_reference: {bicycle_reference}" )
                        try:
                            bicycles_reference.remove(int(bicycle_reference))
                        except ValueError:
                            print(f"Reference {bicycle_reference} not in bicycles_reference")
                        await clean_duplicates(bicycle_reference)
                except Exception as e:
                    print("Error during get reference", e)
                
        elif web == "escapa":
            bicycle_img = bicycle.find("img")["data-src"]
            print(f"bicycle_img: {bicycle_img}")
            bicycle_name = bicycle.find("h3", class_="h3 product-title").text.strip()
            print(f"bicycle_name: {bicycle_name}")
            bicycle_price = get_todays_price(bicycle, web)
            print(f"bicycle_price: {bicycle_price}")
            bicycle_reference = bicycle["data-id-product"]
            print(f"bicycle_reference: {bicycle_reference}\n")
            try:
                bicycles_reference.remove(int(bicycle_reference))
            except ValueError:
                print(f"Reference {bicycle_reference} not in bicycles_reference")
            await clean_duplicates(bicycle_reference)

        try:
            # Buscar en la DB si existe esa referencia
            try:
                bicycle_object = await sync_to_async(lambda: get_object_or_404(Bicycle, reference=bicycle_reference))()
                #await add_todays_price(bicycle_object, USER_AGENTS, web)

                # add_todays_price:
                new_price_history = PriceHistory(
                    bicycle=bicycle_object, date=datetime.now().date(), price=bicycle_price
                )
                await sync_to_async(new_price_history.save)()
                print(f"New price history saved: {new_price_history}")
                
                #if bicycle_object.current_price != float(bicycle_price):
                #    bicycle_object.current_price = float(bicycle_price)
                
                # Update Current Price if it changed
                if round(bicycle_object.current_price, 2) != round(float(bicycle_price), 2):
                    bicycle_object.current_price = float(bicycle_price)
                    await sync_to_async(bicycle_object.save)()
                    print(
                        f"{bicycle_object.reference} changed price from {bicycle_object.current_price} to {bicycle_price}"
                    )
            # Create new Bicycle if it not exist yet
            except:
                print("Bicycle not exist")
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
                    print(f"Saved bike for: {new_bicycle.id}")

                    try:
                        price_history = PriceHistory(
                            bicycle=new_bicycle,
                            date=datetime.now().date(),
                            price=bicycle_price,
                        )
                        await sync_to_async(price_history.save)()
                        print(f"PriceHistory saved for {new_bicycle.reference}")
                    except Exception as e:
                        print("Error creating price_history:", e)

                else:
                    print("Invalid form:", bicycle_form.errors)
        
        except Exception as e:
            print("Error durante el guardado de Bicycle o add_todays_price")
            
    return bicycles_reference


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


async def add_todays_price(bicycle, USER_AGENTS, web):
    print(f"\nAdding todays price for {bicycle.reference}")
    from .views import urls
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        try:
            bicycle_page = await browser.new_page(user_agent=random.choice(USER_AGENTS))
            stealth = Stealth()
            await stealth.apply_stealth_async(bicycle_page)
            await asyncio.sleep(random.uniform(3, 6))
            
            if web == "biking_point":
                response = await bicycle_page.goto(urls[web]["search_endpoint"].format(bicycle.reference), wait_until="domcontentloaded")
            elif web == "escapa":
                response = await bicycle_page.goto(bicycle.url)
            print(f"Response.status: {response.status}")
        except Exception as e:
            print(f"Error durante add_todays_price: {e}")
        return

        if response.status == 200:
            html = await bicycle_page.content()
            reference_soup = BeautifulSoup(html, "html.parser")
            if "La búsqueda no ha devuelto ningún resultado." in reference_soup.text:
                print(f"Reference {bicycle.reference} was deleted")
                await sync_to_async(bicycle.delete)()
            else:
                todays_price = (
                    reference_soup.find_all("span", class_="price")[0]
                    .text.replace("\xa0", "")
                    .replace("€", "")
                    .replace(".", "")
                    .replace(",", ".")
                )
                new_price_history = PriceHistory(
                    bicycle=bicycle, date=datetime.now().date(), price=todays_price
                )
                await sync_to_async(new_price_history.save)()
                if bicycle.current_price != float(todays_price):
                    bicycle.current_price = float(todays_price)
                    await sync_to_async(bicycle.save)()
                    print(
                        f"{bicycle.reference} changed price from {bicycle.current_price} to {todays_price}"
                    )


# Recibe la soup de una bicicleta y retorna su precio actual
def get_todays_price(bicycle, web):
    if web == "biking_point":
        return [
            price.text.replace("\xa0", "")
            .replace("€", "")
            .replace(".", "")
            .replace(",", ".")
            for price in bicycle.find_all("span", class_="price")
        ][0]
    elif web == "escapa":
        price_spam = bicycle.find("span", class_= "price current-price-discount") or bicycle.find("span", class_= "price")
        return [
            price.text.replace("\xa0", "")
            .replace("€", "")
            .replace(".", "")
            .replace(",", ".")
            for price in price_spam
        ][0]
        