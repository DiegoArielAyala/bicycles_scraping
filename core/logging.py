import logging
import asyncio
import time

from functools import wraps
from contextlib import contextmanager


@contextmanager
def log_context(context_name, logger=None, **kwargs):
    context_logger = logger or logging.getLogger(__name__)
    start = time.perf_counter()

    context_logger.debug(
        "Context started", 
        extra={
            "event": "context_started", 
            "context": context_name, 
            **kwargs,
            }
        )
        
    try:
        yield
    except Exception:
        raise
    else:
        duration_ms = (time.perf_counter() - start) * 1000

        context_logger.debug(
            "Context completed", 
            extra={
                "event": "context_completed",
                "context": context_name,
                "duration_ms": round(duration_ms, 2),
                **kwargs,
            })


def log_function(func):
    function_logger = logging.getLogger(func.__module__)
    def log_start():
        function_logger.debug(
            "Function started", 
            extra={
                "event": "function_started",
                "function": func.__qualname__,
            },
        )

    def log_completion(start):
        duration_ms = (time.perf_counter() - start) * 1000

        function_logger.debug(
            "Function completed",
            extra={
                "event": "function_completed",
                "function": func.__qualname__,
                "duration_ms": round(duration_ms, 2),
            },
        )

    def log_error(start):
        duration_ms = (time.perf_counter() - start) * 1000

        function_logger.exception(
            "Function failed",
            extra={
                "event": "function_failed",
                "function": func.__qualname__,
                "duration_ms": round(duration_ms, 2),
            },
        )

    if asyncio.iscoroutinefunction(func):

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.perf_counter()
            log_start()

            try:
                result = await func(*args, **kwargs)
            except Exception:
                log_error(start)
                raise
            
            log_completion(start)
            return result

        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.perf_counter()
        log_start()

        try:
            result = func(*args, **kwargs)
        except Exception:
            log_error(start)
            raise

        log_completion(start)
        return result

    return sync_wrapper