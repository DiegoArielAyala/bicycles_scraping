import asyncio
import django
import logging
import os
import random

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from django.utils import timezone
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import Error as PlaywrightError

from apps.scraping.browser import BrowserSession
from apps.scraping.dtos import ScrapedBycicles
from apps.scraping.dtos import ScrapedPrices
from apps.scraping.utils.html import get_href
from core.logging import log_context

os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
django.setup()

from apps.catalog.services.bicycles import process_scraped_bicycles, delete_bicycles, process_scraped_prices
from apps.scraping.strategies.factory import strategy_factory
from core.exceptions import CloudflareChallengeError, PriceNotFoundError, ReferenceNotFoundError 
from core.metrics import get_metrics, increment
from core.logging import log_function

logger = logging.getLogger(__name__)

PAGE_DELAY_RANGE = (4, 9)

@log_function
async def run_scraper(start_page, last_page, web=None, delete=False):
    all_product_elements_html, scrape_aborted, delete = await scrape_pages(start_page, last_page, web, delete)

    if scrape_aborted and not all_product_elements_html:
        logger.error({"event": "scrape_aborted_without_products", "web": web})
    else:
        scraped_prices, strategy = await sync_to_async(create_scraped_prices)(all_product_elements_html, web)

        new_scraped_prices, price_history_updates, current_prices_by_id = await sync_to_async(process_scraped_prices)(scraped_prices, web)

        new_bicycles = await sync_to_async(prepare_new_bicycles)(new_scraped_prices, web, strategy)

        await sync_to_async(process_scraped_bicycles)(new_bicycles, price_history_updates, current_prices_by_id)

        if delete:
            await sync_to_async(delete_bicycles)(web)

    get_metrics()    
    logger.info("Scrape finished.")

def create_scraped_prices(all_product_elements_html, web):
    logger.debug({"event": "create_scraped_prices", "items": len(all_product_elements_html)})

    if len(all_product_elements_html) == 0:
        logger.debug({"event": "any_bicycle_scraped", "items": len(all_product_elements_html)})
        return
    
    strategy = strategy_factory(web)

    scraped_prices = process_product_elements_html(all_product_elements_html, web, strategy)

    return scraped_prices, strategy

def process_product_elements_html(product_elements_html, web, strategy):
    scraped_prices = []
    seen_references = set()
    bicycle_index = 1

    for product_element in product_elements_html:
        bicycle_index += 1
        
        with log_context("process_product", web=web, index=bicycle_index):
            try:
                reference = strategy.get_reference(product_element)
            except ReferenceNotFoundError:
                logger.warning({"event": "reference_not_found", "web": web})
                continue
            
            if reference in seen_references:
                continue

            try:
                current_price = strategy.get_price(product_element)
            except PriceNotFoundError:
                increment("PriceNotFoundError", web=web)
                logger.warning({"event": "price_not_found_error", "web": web, "reference": reference})
                continue
            
            seen_references.add(reference)

            scraped_prices.append(ScrapedPrices(reference, current_price, product_element))

    return scraped_prices


def prepare_new_bicycles(new_scraped_prices, web, strategy):
    scraped_products = []
    for new_scraped_price in new_scraped_prices:
        bicycle_href = get_href(new_scraped_price.product_element)

        if not bicycle_href:
            logger.error({"event": "href_not_found", "web": web})
            return None
        
        bicycle_name, bicycle_img = strategy.get_product_info(new_scraped_price.product_element)

        scraped_product = ScrapedBycicles(new_scraped_price.reference, new_scraped_price.current_price, bicycle_name, web,  bicycle_href, last_seen_at=timezone.localdate(), is_active=True, img=bicycle_img)

        scraped_products.append(scraped_product)

    return scraped_products


async def scrape_pages(start_page, last_page, web, delete):
    page_number = int(start_page)     
    strategy = strategy_factory(web)
    scrape_aborted = False
    all_product_elements_html = []

    async with BrowserSession() as browser_session:
        while page_number <= last_page:
            if page_number > int(start_page):
                delay = random.uniform(*PAGE_DELAY_RANGE) 
                await asyncio.sleep(delay)

            url = strategy.get_list_url(page_number)
            logger.debug({"event": "get_url", "url": url})
            
            try:
                html = await browser_session.get_html(url, page_number)
            except CloudflareChallengeError:
                logger.error({"event": "cloudflare_abort", "url": url, "page": page_number})
                scrape_aborted = True
                if page_number <= last_page/2:
                    delete = False
                break
            except PlaywrightTimeoutError:
                logger.error({"event": "page_timeout", "url": url, "page": page_number})
                if page_number <= last_page/2:
                    delete = False
                break
            except PlaywrightError as e:
                logger.error({"event": "playwright_error", "url": url, "page": page_number, "error": str(e)})
                if page_number <= last_page/2:
                    delete = False
                break

            if not html:
                logger.debug({"event": "html_not_getted", "page_number": page_number})
                break

            soup = BeautifulSoup(html, "html.parser")
            product_elements_html = strategy.get_product_elements_html(soup)

            if not product_elements_html:
                break

            all_product_elements_html.extend(product_elements_html)
            page_number += 1

    return all_product_elements_html, scrape_aborted, delete
