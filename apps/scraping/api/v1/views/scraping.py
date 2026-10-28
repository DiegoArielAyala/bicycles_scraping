from apps.scraping.api.v1.serializers import ScrapingSerializer
from apps.accounts.permissions import IsAdminRole
from apps.scraping.services.github_actions import trigger_github_action
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

class ScrapingView(APIView):
    permission_classes = [IsAdminRole]

    def post(self, request):
        serializer = ScrapingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scraping_data = serializer.validated_data

        trigger_github_action(scraping_data)

        return Response({"message": "Scraping triggered", "job": "github-actions"}, status=status.HTTP_202_ACCEPTED)