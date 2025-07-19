import asyncio
from scraping.views import run_scraper

def run():
    asyncio.run(run_scraper(1, 30)) 