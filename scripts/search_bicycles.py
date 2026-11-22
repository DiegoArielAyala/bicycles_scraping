import argparse
import asyncio
import logging
import os

import django
from asgiref.sync import sync_to_async

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from apps.catalog.models import Bicycle

logger = logging.getLogger(__name__)

async def search_bicycles(reference):
    bicycles = await sync_to_async(list)(Bicycle.objects.filter(reference=reference))
    logger.info({"event": "search_bicycles", "reference": reference, "count": len(bicycles)})

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Search bicycle by reference")
    parser.add_argument("--reference", required=True)
    args = parser.parse_args()
    asyncio.run(search_bicycles(args.reference))