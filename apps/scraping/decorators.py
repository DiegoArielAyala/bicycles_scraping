import asyncio
import logging
from os import sync
import time

from functools import wraps

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

def log_function(func):
    if asyncio.iscoroutinefunction(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            logger.info(f"Executing {func.__name__}")
            try:
                start = time.time()
                result = await func(*args, **kwargs)
                end = time.time()
                logger.info(f"End function {func.__name__}. Duration {end - start}s")
                return result
            except Exception as e:
                logger.exception(f"Error during {func.__name__}: {e}")
                raise
        return async_wrapper

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        logger.info(f"Executing {func.__name__}")
        try:
            start = time.time()
            result = func(*args, **kwargs)
            logger.info(f"End function {func.__name__}")
            return result
        except Exception as e:
            logger.exception(f"Error during {func.__name__}")
            raise
    return sync_wrapper