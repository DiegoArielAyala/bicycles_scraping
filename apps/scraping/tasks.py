import argparse
import asyncio
import logging

from celery import shared_task
from playwright.async_api import TimeoutError as PlaywrightTimeoutError

from apps.alerts.services.price_alerts import send_price_drop_emails
from apps.scraping.context_managers import LockNotAcquiredError, RedisLock
from apps.scraping.services.runner import run_scraper


logger = logging.getLogger(__name__)

@shared_task(
    bind=True,
    autoretry_for=(PlaywrightTimeoutError,), 
    retry_kwargs={"max_retries": 2},
    retry_backoff=5,
    queue="scraping",
    )
def run_scraper_task(self, start, end, web, delete=False):
    try:
        with RedisLock(web):
            asyncio.run(run_scraper(start, end, web, delete))
    except LockNotAcquiredError as exc:
        raise self.retry(exc=exc, countdown=5, max_retries=2)


@shared_task(
    queue="emails",
)
def emails_task():
    send_price_drop_emails()

@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=5,
    soft_time_limit=300,
    time_limit=360,
    queue="scraping",
)
def retry_test_task(self):
    logger.info({"event": "retry_test", "attemp": self.request.retries})
    raise self.retry(exc=ValueError("Error de prueba"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", type=int )
    parser.add_argument("--end", type=int)
    parser.add_argument("--web", type=str)
    parser.add_argument("--delete", action="store_true")

    args = parser.parse_args()

    run_scraper_task.apply_async(
        args=[args.start, args.end, args.web, args.delete],
        queue="scraping",
        )