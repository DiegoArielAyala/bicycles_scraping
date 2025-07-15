from celery import shared_task
import asyncio

@shared_task
def run_scraper_task(start_page, last_page):
    print("run_scraper_task function start")
    from .views import run_scraper
    asyncio.run(run_scraper(start_page, last_page))