import asyncio
import django
import logging
import os
import random

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from playwright.async_api import TimeoutError as PlaywrightTimeoutError
from playwright.async_api import Error as PlaywrightError

from apps.scraping.context_managers import BrowserSession

os.environ.setdefault("DJANGO_SETTINGS_MODULE","config.settings")
django.setup()

from apps.catalog.services.bicycles import create_bicycles, delete_bicycles
from apps.scraping.services.metrics import get_metrics
from apps.scraping.strategies.factory import strategy_factory
from apps.scraping.decorators import log_function
from core.exceptions import CloudflareChallengeError 

logger = logging.getLogger(__name__)

PAGE_DELAY_RANGE = (4, 9)

@log_function
async def run_scraper(start_page, last_page, web=None, delete=False):
    all_product_elements_html, scrape_aborted, delete = await scrape_pages(start_page, last_page, web, delete)

    if scrape_aborted and not all_product_elements_html:
        logger.error({"event": "scrape_aborted_without_products", "web": web})
    else:
        await sync_to_async(create_bicycles)(all_product_elements_html, web)
        if delete:
            await sync_to_async(delete_bicycles)()

    get_metrics()    
    logger.info("Scrape finished.")

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

            if web == "escapa" and strategy.is_last_page(soup):
                logger.info("No hay más productos, finalizando.")
                break
    return all_product_elements_html, scrape_aborted, delete
