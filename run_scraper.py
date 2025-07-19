import asyncio
from scraping.views import run_scraper

if __name__ == "__main__":
    start_page = 1
    last_page = 30
    asyncio.run(run_scraper(start_page, last_page))
