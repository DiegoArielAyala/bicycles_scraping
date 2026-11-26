import asyncio
import django
import logging
import os
import random

from asgiref.sync import sync_to_async
from bs4 import BeautifulSoup
from django.core.exceptions import ObjectDoesNotExist
from playwright.async_api import async_playwright, Error as PlaywrightError, TimeoutError as PlaywrightTimeoutError

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Bicycle
from apps.scraping.constants import USER_AGENTS
from apps.scraping.strategies.biking_point import BikingPointStrategy

logger = logging.getLogger(__name__)

# Use Playwright to get the correct img url from each bicycle reference

async def update_bicycles_image_urls():
    references = await get_bicycles_references_from_db()
    correct_imgs_counter = 0
    img_url_saved_counter = 0

    for reference in references:
        try:
            html = await fetch_biking_point_html(reference)
            img_url = extract_image_url(html)
            if img_url is None:
                logger.warning(
                    "Image url not found",
                    extra={
                        "event": "img_url_not_found",
                        "reference": reference,
                    },
                )
                continue
            try:
                bicycle = await get_bicycle_by_reference(reference)
            
            except ObjectDoesNotExist:
                logger.warning(
                    "Reference not exists",
                    extra={
                        "event": "reference_not_exists",
                        "reference": reference,
                    },
                )
                continue
            
            if bicycle.img == img_url:
                correct_imgs_counter+=1
                continue
            bicycle.img = img_url
            await sync_to_async(lambda: bicycle.save())()
            img_url_saved_counter+=1
        
        except PlaywrightTimeoutError:
            logger.warning(
                "Playwright timeout",
                extra={
                    "event": "playwright_timeout",
                    "reference": reference,
                },
            )
            continue
        except PlaywrightError:
            logger.warning(
                "Playwright error",
                extra={
                    "event": "playwright_error",
                    "reference": reference,
                },
            )
        except Exception:
            logger.exception(
                "Unexpected error",
                extra={
                    "event": "unexpected_error",
                    "reference": reference,
                },
            )
        
    logger.info(
        "Correct images",
        extra={
            "event": "correct_imgs",
            "count": correct_imgs_counter,
        },
    )
    logger.info(
        "Image urls saved",
        extra={
            "event": "img_urls_saved",
            "count": img_url_saved_counter,
        },
    )
             
        
async def get_bicycles_references_from_db():
    bicycles_references = await sync_to_async(lambda: list(Bicycle.objects.filter(web="biking_point").values_list("reference", flat=True)))()
    return bicycles_references

async def fetch_biking_point_html(reference):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args= ["--no-sandbox", "--disable-dev-shm-usage", "--disable-blink-features=AutomationControlled"])
        page = await browser.new_page(user_agent=random.choice(USER_AGENTS))
        await page.goto(BikingPointStrategy.SEARCH_ENDPOINT.format(reference))
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