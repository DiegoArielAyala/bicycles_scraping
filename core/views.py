from django.http import HttpResponse
from prometheus_client import generate_latest, REGISTRY
from rest_framework.views import APIView

from apps.accounts.permissions import PrometheusPermission

class MetricsView(APIView):
    authentication_classes = []
    permission_classes = [PrometheusPermission]
    def get(self, request):
        metrics = generate_latest(REGISTRY)

        return HttpResponse(metrics, content_type="text/plain; version=0.0.4; charset=utf-8")