import logging
import time

from functools import wraps

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(name)s - %(message)s"
)

logger = logging.getLogger(__name__)

def log_function(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
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
    return wrapper