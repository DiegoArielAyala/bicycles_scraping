import os
import django
import asyncio

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bicyclesscraping.settings")
django.setup()

from scraping.views import run_scraper 

def run():
    asyncio.run(run_scraper(1, 30))

if __name__ == "__main__":
    run()
