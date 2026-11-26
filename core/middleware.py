import logging
import re
import time
import uuid

from core.metrics import http_request_duration_seconds, http_requests_errors_total, http_requests_total, http_requests_in_progress
from core.request_context import request_id


REQUEST_ID_PATTERN = re.compile(r"[a-zA-Z0-9_-]{1,64}")

logger = logging.getLogger(__name__)

def is_valid(value):
    return bool(REQUEST_ID_PATTERN.fullmatch(value))


class RequestIDMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        x_request_id = request.headers.get("X-Request-ID")

        if not x_request_id or not is_valid(x_request_id):
            x_request_id = str(uuid.uuid4())
        
        token = request_id.set(x_request_id)
        request.request_id = x_request_id

        try:
            response = self.get_response(request)
            response["X-Request-ID"] = x_request_id
            
            return response
        
        finally:
            request_id.reset(token)


class MetricsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        start = time.perf_counter()

        http_requests_total.labels(method=request.method).inc()
        http_requests_in_progress.inc()

        status_code = "exception"

        try:
            response = self.get_response(request)
            status_code = response.status_code

            if status_code >= 400:
                http_requests_errors_total.labels(method=request.method, status=str(response.status_code)).inc()
            
            return response

        finally:
            duration = time.perf_counter() - start

            http_requests_in_progress.dec()

            http_request_duration_seconds.labels(method=request.method).observe(duration)

            duration_ms = duration * 1000

            logger.info(
                "HTTP request",
                extra={
                    "event": "http_request",
                    "method": request.method,
                    "path": request.path,
                    "status": status_code,
                    "duration_ms": round(duration_ms, 2),
                },
            )
        