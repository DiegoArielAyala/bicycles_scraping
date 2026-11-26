import logging

from core.request_context import request_id

class RequestIDFilter(logging.Filter):
    def filter(self, record):
        record.request_id = request_id.get() or "-"
        return True