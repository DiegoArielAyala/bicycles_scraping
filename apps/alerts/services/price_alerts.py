import logging
import threading

from decimal import Decimal

from apps.alerts.emails.services import EmailService
from apps.alerts.models import Subscription

logger = logging.getLogger(__name__)

MINIMUM_PRICE_DROP = Decimal("50.00")

def should_send_price_alert(old_price, new_price):
    old_price = Decimal(old_price)
    new_price = Decimal(new_price)

    difference = old_price - new_price

    return difference >= MINIMUM_PRICE_DROP

def send_price_drop_emails(price_drops):
    drops_by_bicycle_id = {
        drop["bicycle_id"]: drop for drop in price_drops
    }

    subscriptions = list(
            Subscription.objects.filter(
                bicycle_id__in=drops_by_bicycle_id.keys()
            ).select_related("bicycle")
        )

    sent_count = 0
    sent_count_lock = threading.Lock()

    def send_one(subscription, bicycle, old_price, new_price):
        nonlocal sent_count
        if EmailService.send_price_drop_email(subscription, bicycle, old_price, new_price):
            with sent_count_lock:
                sent_count += 1

    threads = []
    for subscription in subscriptions:
        drop = drops_by_bicycle_id[subscription.bicycle_id]
        thread = threading.Thread(
            target=send_one,
            args=[subscription, subscription.bicycle, drop["old_price"], drop["new_price"]]
        )
        thread.start()
        threads.append(thread)

    for thread in threads:
        thread.join()

    logger.info(
        "Send emails",
        extra={
            "event": "send_emails",
            "count": sent_count,
        },
    )