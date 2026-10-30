import logging
import os
import time

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_retry, task_failure

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("config")

app.config_from_object("django.conf:settings", namespace="CELERY")

app.autodiscover_tasks()

logger = logging.getLogger(__name__)
task_start_times = {}

@task_prerun.connect
def log_task_start(sender=None, task_id=None, task=None, args=None, kwargs=None, **extra):
    task_start_times[task_id] = time.perf_counter()
    logger.info(
        "Task started: task=%s task_id=%s",
        sender.name if sender else task,
        task_id,
    )

@task_postrun.connect
def log_task_finish(sender=None, task_id=None, state=None, **extra):
    start_time = task_start_times.pop(task_id, None)

    if start_time is None:
        return
    
    duration = time.perf_counter() - start_time

    if state == "SUCCESS":
        logger.info(
            "Task completed: task=%s task_id=%s duration=%.2fs",
            sender.name if sender else "unknown",
            task_id, 
            duration,
        )
    else:
        logger.warning(
            "Task finished: task=%s task_id=%s state=%s duration=%.2fs",
            sender.name if sender else "unknown",
            task_id,
            state,
            duration,
        )

@task_retry.connect
def log_task_retry(sender=None, request=None, reason=None, **extra):
    logger.warning(
        "Task retry: task=%s task_id=%s retries=%s reason=%s",
        sender.name if sender else "unknown",
        request.id if request else "unknown",
        request.retries if request else "unknown",
        reason,
    )


@task_failure.connect
def log_task_failure(sender=None, task_id=None, exception=None, **extra):
    logger.error(
        "Task failed: task=%s task_id=%s error=%s",
        sender.name if sender else "unknown",
        task_id,
        exception,
    )