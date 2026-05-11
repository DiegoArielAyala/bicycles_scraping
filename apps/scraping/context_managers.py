import logging

from contextlib import contextmanager

logger = logging.getLogger(__name__)

@contextmanager
def log_context(name, **kwargs):
    logger.info({"event": "start", "name": name, **kwargs})
    try:
        yield
    except Exception:
        logger.exception({"event": "error", "name": name, **kwargs})
        raise
    finally:
        logger.info({"event": "end", "name": name, **kwargs})