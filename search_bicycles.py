import django, os, argparse
import asyncio
from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "bicyclesscraping.settings")
django.setup()

from scraping.models import Bicycle

async def search_bicycles(reference):
    database_url=os.getenv("DATABASE_URL_PRODUCTION")
    print(database_url)
    bicycles = await sync_to_async(list)(Bicycle.objects.filter(reference=reference))
    print(bicycles)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search bicycle by reference")
    parser.add_argument("--reference", required=True)
    args = parser.parse_args()
    asyncio.run(search_bicycles(args.reference))