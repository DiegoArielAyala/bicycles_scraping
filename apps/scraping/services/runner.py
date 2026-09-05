import asyncio
import django
import logging
import os
import random
import re

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from django.shortcuts import get_object_or_404
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import async_playwright
from playwright_stealth import Stealth

os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
django.setup()

from apps.scraping.constants import CHROME_USER_AGENT
from apps.scraping.services.metrics import get_metrics
from apps.scraping.services.bicycles_services import create_bicycles 
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
            counter = int(start_page)
            scrape_aborted = False
            pages_in_session = 0

        # Array with all bicycles references in the DB for the current web
            bicycle_references_in_db = await sync_to_async(
                lambda: list(Bicycle.objects.filter(web=web).values_list("reference", flat=True,))
                )()
            
            strategy = strategy_factory(web)

            all_product_elements_html = []

            while counter <= last_page:
                if pages_in_session >= PAGES_PER_SESSION:
                    logger.info({"event": "rotate_browser_session", "next_page": counter})
                    await close_session(context, page)
                    context, page = await open_session(browser)
                    pages_in_session = 0

                if counter > int(start_page):
                    delay = random.uniform(*PAGE_DELAY_RANGE)
                    await asyncio.sleep(delay)

                url = strategy.get_list_url(counter)
                logger.debug(f"Url: {url}")

                try:
                    html = await get_html(page, url)
                except CloudflareChallengeError:
                    logger.warning({"event": "cloudflare_rotate_session", "url": url, "page": counter})
                    await asyncio.sleep(random.uniform(*CLOUDFLARE_RETRY_DELAY_RANGE))
                    await close_session(context, page)
                    context, page = await open_session(browser)
                    pages_in_session = 0
                    try:
                        html = await get_html(page, url)
                    except CloudflareChallengeError:
                        logger.error({"event": "cloudflare_abort", "url": url, "page": counter})
                        scrape_aborted = True
                        delete = False
                        break
                except Exception as e:
                    logger.error(f"Error en la página {counter}: {e}")
                    delete = False
                    break

                if not html:
                    logger.debug(f"Page {counter} didn't load. Exit loop")
                    delete = False
                    break

                soup = BeautifulSoup(html, "html.parser")
                product_elements_html = strategy.get_product_elements_html(soup)

                if not product_elements_html:
                    break

                all_product_elements_html.extend(product_elements_html)
                counter += 1
                pages_in_session += 1

                if web == "escapa" and is_last_page(soup):
                    logger.info("No hay más productos, finalizando.")
                    break

            if scrape_aborted and not all_product_elements_html:
                logger.error({"event": "scrape_aborted_without_products", "web": web})
            else:
                bicycle_references_in_db = await sync_to_async(create_bicycles)(all_product_elements_html, web, bicycle_references_in_db)

                if delete and bicycle_references_in_db:
                    await delete_bicycles(bicycle_references_in_db, page)
        finally:
            await close_session(context, page)
            await browser.close()

    get_metrics()    
    logger.info("Scraping terminado.")

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

async def get_html(page, url):
    """
    Returns page HTML as string, or None if something failed.
    Raises CloudflareChallengeError if the challenge does not clear.
    """
    html = None
    
    try:
        await page.goto(url, wait_until="domcontentloaded", timeout=60000)
        html = await page.content()

        if CLOUDFLARE_MARKER in html:
            logger.warning({"event": "cloudflare_challenge_detected", "url": url})
            html = await wait_for_cloudflare_clear(page)

    except CloudflareChallengeError:
        raise
    except Exception as e:
        logger.error(f"Error during get html: {e}")
        return None
    
    return html


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

def is_last_page(soup):
    search_number = (re.search(r"Mostrando \d+-(\d+)", soup.text)).group(1)
    number_bicycles = (re.search(r"de (\d+) producto", soup.text)).group(1)
    logger.debug(search_number)
    logger.debug(number_bicycles)
    return number_bicycles == search_number

async def delete_bicycles(bicycle_references_not_in_web, page):
    logger.info({"event": "deleting_bicycles", "references_to_delete": bicycle_references_not_in_web})
    for reference in bicycle_references_not_in_web:
        try:
            bicycle = await sync_to_async(lambda: get_object_or_404(Bicycle, reference=reference))()
            strategy = strategy_factory(bicycle.web)

            # Look for reference on the corresponding web
            bicycle_exist = await strategy.bicycle_exists(page, reference)
            
            # If bicycle not exist in web, delete it
            if not bicycle_exist:
                await sync_to_async(bicycle.delete)()
                logger.info({"event": "bicycle_deleted", "reference": reference})

        except Exception as e:
            logger.error({"event": "delete_bicycle_error", "reference": reference, "error": str(e)})



