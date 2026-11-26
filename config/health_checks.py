import logging
from django.http.response import HttpResponse
from rest_framework.status import HTTP_200_OK, HTTP_503_SERVICE_UNAVAILABLE
from django.db import DatabaseError, connection

logger = logging.getLogger(__name__)

def live(request):
    return HttpResponse("Service is alive", status=HTTP_200_OK)
    

def ready(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return HttpResponse("Database connection ready", status=HTTP_200_OK)

    except DatabaseError:
        logger.exception(
            "Database readiness check failed", 
            extra={
                "event": "readiness_check_failed",
            },
        )
        return HttpResponse("Database connection not ready", status=HTTP_503_SERVICE_UNAVAILABLE)