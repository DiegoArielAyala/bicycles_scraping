import os
import django
import asyncio
import argparse

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bicyclesscraping.settings")
django.setup()

from scraping.users.views.views import run_scraper

def main():
    parser = argparse.ArgumentParser(description="Run scraper with page range")
    parser.add_argument("--start", type=int, default=1, help="Start page")
    parser.add_argument("--end", type=int, default=25, help="End page")
    parser.add_argument("--web", type=str, default=None, help="Shop name")
    parser.add_argument("--delete", action="store_true", help="Activate delete functionality")
    args = parser.parse_args()

    asyncio.run(run_scraper(args.start, args.end, args.web, args.delete))

if __name__ == "__main__":
    main()
