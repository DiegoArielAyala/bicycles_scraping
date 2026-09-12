from rest_framework.response import Response
from rest_framework.views import APIView

from apps.scraping.emails.services import EmailService
from apps.scraping.models import Bicycle, Subscription


class TestEmailView(APIView):

    def get(self, request):

        subscription = Subscription.objects.first()

        bicycle = Bicycle.objects.first()

        EmailService.send_price_drop_email(
            subscription=subscription,
            bicycle=bicycle,
            old_price=5000,
            new_price=4500,
        )

        return Response({"detail": "Email sent"})