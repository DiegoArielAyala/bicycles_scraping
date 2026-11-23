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
        "Task started",
        extra={
            "event": "task_started",
            "task": sender.name if sender else task,
            "task_id": task_id,
        },
    )

@task_postrun.connect
def log_task_finish(sender=None, task_id=None, state=None, **extra):
    start_time = task_start_times.pop(task_id, None)

    if start_time is None:
        return
    
    duration = time.perf_counter() - start_time

    if state == "SUCCESS":
        logger.info(
            "Task completed",
            extra={
                "event": "task_completed",
                "task": sender.name if sender else "unknown",
                "task_id": task_id,
                "duration": round(duration, 2),
            },
        )
    else:
        logger.warning(
            "Task finished",
            extra={
                "event": "task_finished",
                "task": sender.name if sender else "unknown",
                "task_id": task_id,
                "state": state,
                "duration": round(duration, 2),
            },
        )

@task_retry.connect
def log_task_retry(sender=None, request=None, reason=None, **extra):
    logger.warning(
        "Task retry",
        extra={
            "event": "task_retry",
            "task": sender.name if sender else "unknown",
            "task_id": request.id if request else "unknown",
            "retries": request.retries if request else "unknown",
            "reason": reason,
        },
    )


@task_failure.connect
def log_task_failure(sender=None, task_id=None, exception=None, einfo=None, **extra):
    logger.error(
        "Task failed",
        extra={
            "event": "task_failed",
            "task": sender.name if sender else "unknown",
            "task_id": task_id,
            "error": exception,
        },
        exc_info=einfo,
    )