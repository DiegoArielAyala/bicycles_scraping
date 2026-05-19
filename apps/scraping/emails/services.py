import logging

from django.conf import settings
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)


class EmailService:

    @staticmethod
    def send_price_drop_email(
        subscription,
        bicycle,
        old_price,
        new_price,
    ):

        try:

            difference = old_price - new_price

            subject = f"Price Drop Alert: {bicycle.name}"

            context = {
                "subscription": subscription,
                "bicycle": bicycle,
                "old_price": old_price,
                "new_price": new_price,
                "difference": difference,
                "unsubscribe_url": (
                    f"{settings.FRONTEND_URL}/unsubscribe/"
                    f"{subscription.unsubscribe_token}"
                ),
            }

            html_content = render_to_string(
                "emails/price_drop.html",
                context,
            )

            plain_message = f"""
            Price drop detected!

            {bicycle.name}

            Old price: €{old_price}
            New price: €{new_price}

            You save: €{difference}
            """

            email = EmailMultiAlternatives(
                subject=subject,
                body=plain_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[subscription.email],
            )

            email.attach_alternative(html_content, "text/html")

            email.send()

            logger.info(
                f"Price drop email sent to {subscription.email}"
            )

        except Exception:

            logger.exception(
                f"Failed to send email to {subscription.email}"
            )