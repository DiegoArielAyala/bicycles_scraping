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
    logger.info("Scraping started", extra={
        "event": "scraping_started",
        "web": web,
        "start_page": start_page,
        "last_page": last_page
    })
    all_product_elements_html = await scrape_pages(start_page, last_page, web)

    if not all_product_elements_html:
        logger.warning("No products found", extra={
            "event": "no_products_found",
            "web": web
        })
    else:
        scraped_prices, strategy = await sync_to_async(get_scraped_prices)(all_product_elements_html, web)

        new_scraped_prices, price_history_updates, current_prices_by_id = await sync_to_async(process_scraped_prices)(scraped_prices, web)

        new_bicycles = await sync_to_async(prepare_new_bicycles)(new_scraped_prices, web, strategy)

        await sync_to_async(process_scraped_bicycles)(new_bicycles, price_history_updates, current_prices_by_id)

        if delete:
            await sync_to_async(delete_bicycles)(web)

        logger.info("Scraping completed", extra={
            "event": "scraping_completed", 
            "web": web,
        })
    
    get_metrics()    

def get_scraped_prices(all_product_elements_html, web):
    logger.debug("Get scraped prices", extra={
        "event": "create_scraped_prices", 
        "items": len(all_product_elements_html),
        })
    
    strategy = strategy_factory(web)

    scraped_prices = process_product_elements_html(all_product_elements_html, web, strategy)

    return scraped_prices, strategy

def process_product_elements_html(product_elements_html, web, strategy):
    scraped_prices = []
    seen_references = set()

    with log_context("process_product", web=web, products=len(product_elements_html)):
        references_not_found = 0
        prices_not_found = 0
        for product_element in product_elements_html:        
            try:
                reference = strategy.get_reference(product_element)
            except ReferenceNotFoundError:
                references_not_found+=1
                continue
            
            if reference in seen_references:
                continue

            try:
                current_price = strategy.get_price(product_element)
            except PriceNotFoundError:
                increment("PriceNotFoundError", web=web)
                prices_not_found+=1
                continue
            
            seen_references.add(reference)

            scraped_prices.append(ScrapedPrices(reference, current_price, product_element))

        if references_not_found > 0 or prices_not_found > 0:
            logger.warning("Data not found", extra={
                "event": "data_not_found", 
                "references_not_found": references_not_found, 
                "prices_not_found": prices_not_found,
                })

    return scraped_prices


def prepare_new_bicycles(new_scraped_prices, web, strategy):
    scraped_products = []
    for new_scraped_price in new_scraped_prices:
        bicycle_href = get_href(new_scraped_price.product_element)

        if not bicycle_href:
            logger.warning("Href not found", extra={
                "event": "href_not_found", 
                "web": web
                })
            continue
        
        bicycle_name, bicycle_img = strategy.get_product_info(new_scraped_price.product_element)

        scraped_product = ScrapedBycicles(new_scraped_price.reference, new_scraped_price.current_price, bicycle_name, web,  bicycle_href, last_seen_at=timezone.localdate(), is_active=True, img=bicycle_img)

        scraped_products.append(scraped_product)

    return scraped_products


async def scrape_pages(start_page, last_page, web):
    page_number = int(start_page)     
    strategy = strategy_factory(web)
    all_product_elements_html = []

    async with BrowserSession() as browser_session:
        while page_number <= last_page:
            if page_number > int(start_page):
                delay = random.uniform(*PAGE_DELAY_RANGE) 
                await asyncio.sleep(delay)

            url = strategy.get_list_url(page_number)
            logger.debug("Get url", extra={
                "event": "get_url", 
                "url": url
                })
            
            try:
                html = await browser_session.get_html(url, page_number, strategy.get_end_of_catalog_text())
            except CloudflareChallengeError:
                logger.warning("Cloudflare abort", extra={
                    "event": "cloudflare_abort", 
                    "url": url, 
                    "page": page_number,
                    })
                break
            except PlaywrightTimeoutError:
                raise
            except PlaywrightError as e:
                logger.error("Playwright error interrupted scraping", extra={
                    "event": "playwright_error",
                    "url": url,
                    "page": page_number,
                    "error": str(e),
                })
                break

            if not html:
                logger.warning("Html not reviced", extra={
                    "event": "html_not_recived", 
                    "page_number": page_number,
                    })
                break

            soup = BeautifulSoup(html, "html.parser")
            product_elements_html = strategy.get_product_elements_html(soup)

            if not product_elements_html:
                break

            all_product_elements_html.extend(product_elements_html)
            page_number += 1

    return all_product_elements_html
