import asyncio
import django
import logging
import os
import random

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from playwright.async_api import Error as PlaywrightError
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
django.setup()

from apps.scraping.constants import CHROME_USER_AGENT
from apps.scraping.services.metrics import get_metrics
from apps.scraping.services.bicycles import create_bicycles 
from apps.scraping.models import Bicycle
from apps.scraping.strategies.factory import strategy_factory
from apps.scraping.decorators import log_function
from core.exceptions import CloudflareChallengeError 

logger = logging.getLogger(__name__)

CLOUDFLARE_MARKER = "cdn-cgi/challenge-platform"
LISTING_READY_SELECTOR = "li.item.product.product-item, article.product-miniature"
CLOUDFLARE_WAIT_MS = 45000
PAGE_DELAY_RANGE = (4, 9)
CLOUDFLARE_RETRY_DELAY_RANGE = (15, 25)
PAGES_PER_SESSION = 2

@log_function
async def run_scraper(start_page, last_page, web=None, delete=False):
    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=True, 
            args=["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"]
        )
        context, page = await open_session(browser)

        try:
            all_product_elements_html, scrape_aborted, delete, context, page = await scrape_pages(start_page, last_page, web, browser, context, page, delete)

            if scrape_aborted and not all_product_elements_html:
                logger.error({"event": "scrape_aborted_without_products", "web": web})
            else:
                bicycles_to_delete = await sync_to_async(create_bicycles)(all_product_elements_html, web)

                if delete and bicycles_to_delete:
                    await delete_bicycles(bicycles_to_delete, page, web)
        finally:
            await close_session(context, page)
            await browser.close()

    get_metrics()    
    logger.info("Scrape finished.")

async def scrape_pages(start_page, last_page, web, browser, context, page, delete):
    page_number = int(start_page)
    pages_in_session = 0            
    strategy = strategy_factory(web)
    scrape_aborted = False
    all_product_elements_html = []

    while page_number <= last_page:
        if pages_in_session >= PAGES_PER_SESSION:
            logger.info({"event": "rotate_browser_session", "next_page": page_number})
            await close_session(context, page)
            context, page = await open_session(browser)
            pages_in_session = 0

        if page_number > int(start_page):
            delay = random.uniform(*PAGE_DELAY_RANGE) 
            await asyncio.sleep(delay)

        url = strategy.get_list_url(page_number)
        logger.debug({"event": "get_url", "url": url})

        try:
            html, pages_in_session, context, page = await get_html(context, page, url, page_number, browser, pages_in_session)
        except CloudflareChallengeError:
            scrape_aborted = True
            delete = False
            break
        except PlaywrightTimeoutError:
            logger.error({"event": "page_timeout", "url": url, "page": page_number})
            delete = False
            break
        except PlaywrightError as e:
            logger.error({"event": "playwright_error", "url": url, "page": page_number, "error": str(e)})
            delete = False
            break

        if not html:
            logger.debug(f"Page {page_number} didn't load. Exit loop")
            delete = False
            break

        soup = BeautifulSoup(html, "html.parser")
        product_elements_html = strategy.get_product_elements_html(soup)

        if not product_elements_html:
            break

        all_product_elements_html.extend(product_elements_html)
        page_number += 1
        pages_in_session += 1

        if web == "escapa" and strategy.is_last_page(soup):
            logger.info("No hay más productos, finalizando.")
            break
    return all_product_elements_html, scrape_aborted, delete, context, page

async def open_session(browser):
    context = await browser.new_context(
        user_agent=CHROME_USER_AGENT,
        viewport={"width": 1366, "height": 768},
        locale="es-ES",
    )
    stealth = Stealth()
    await stealth.apply_stealth_async(context)
    page = await context.new_page()
    return context, page

async def close_session(context, page):
    await page.close()
    await context.close()

async def get_html(context, page, url, scrape_page, browser, pages_in_session):
    async def fetch_html(page):
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        html = await page.content()

        if CLOUDFLARE_MARKER in html:
            logger.warning({"event": "cloudflare_challenge_detected", "url": url})
            html = await wait_for_cloudflare_clear(page)

        return html

    try:
        html = await fetch_html(page)
        return html, pages_in_session, context, page

    except CloudflareChallengeError:
        logger.warning({"event": "cloudflare_rotate_session", "url": url, "page": scrape_page})

        await asyncio.sleep(random.uniform(*CLOUDFLARE_RETRY_DELAY_RANGE))

        await close_session(context, page)
        context, page = await open_session(browser)
        pages_in_session = 0

        try:
            html = await fetch_html(page)
            return html, pages_in_session, context, page
        except CloudflareChallengeError:
            logger.error({"event": "cloudflare_abort", "url": url, "page": scrape_page})
            raise
     

async def wait_for_cloudflare_clear(page):
    try:
        await page.wait_for_function(
            """() => {
                const html = document.documentElement.innerHTML;
                const challengeGone = !html.includes('cdn-cgi/challenge-platform');
                const hasListing = !!document.querySelector(
                    'li.item.product.product-item, article.product-miniature'
                );
                return challengeGone || hasListing;
            }""",
            timeout=CLOUDFLARE_WAIT_MS,
        )
    except PlaywrightTimeoutError:
        logger.error({"event": "cloudflare_challenge_timeout"})
        raise CloudflareChallengeError("Cloudflare challenge did not clear")

    html = await page.content()
    has_listing = await page.query_selector(LISTING_READY_SELECTOR)
    if CLOUDFLARE_MARKER in html and not has_listing:
        raise CloudflareChallengeError("Cloudflare challenge still present")

    logger.info({"event": "cloudflare_challenge_cleared"})
    return html


"Se podria mejorar cambiando la estrategia para buscar si la bicycleta existe. Si delete_references es mayor a cierto numero, extraer las referencias de todas las paginas de busqueda de bicicleta y eliminarlas de delete_references. Esto se puede hacer mas eficiente si se guardan las referencias ya encontradas en el scraping (esto es util si se pudo scrapear la mayoria de paginas y delete_references queda de un tamaño pequeño). Si delete_references no es tan extenso, buscar bicicleta por bicicleta si existe o no"
async def delete_bicycles(delete_references, page, web):
    logger.info({"event": "deleting_bicycles", "number_of_references": len(delete_references), "references_to_delete": delete_references})
    bicycles = await sync_to_async(lambda: list(Bicycle.objects.filter(reference__in=delete_references)))()
    strategy = strategy_factory(web)

    for bicycle in bicycles:
        try:
            # Look for reference on the corresponding web
            bicycle_exist = await strategy.bicycle_exists(page, bicycle.reference, bicycle.url)

            # If bicycle not exist in web, delete it
            if not bicycle_exist:
                await sync_to_async(bicycle.delete)()
                logger.info({"event": "bicycle_deleted", "reference": bicycle.reference})
            else:
                logger.info({"event": "bicycle_exists", "reference": bicycle.reference})

        except Exception as e:
            logger.error({"event": "delete_bicycle_error", "reference": bicycle.reference, "error": str(e)})

