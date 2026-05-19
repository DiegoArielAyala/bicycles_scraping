import logging

from django.conf import settings
from rest_framework.status import HTTP_202_ACCEPTED
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated

from ...services.github_actions import trigger_github_action
from ..serializers import ScrapingSerializer

logger = logging.getLogger(__name__)

class ScrapingView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = ScrapingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scraping_data = serializer.validated_data

        cron_token = request.headers.get("X-CRON-TOKEN")
        if cron_token != settings.CRON_SECRET_TOKEN:
            logger.error({"event": "invalid_cron_secret"})
            return Response({"error": "Unauthorized"}, status=403)

        trigger_github_action(scraping_data)

        return Response({"message": "Scraping triggered", "job": "github-actions"}, status=HTTP_202_ACCEPTED)