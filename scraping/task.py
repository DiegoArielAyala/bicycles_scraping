from celery import shared_task
from .utils import create_bicycles

@shared_task
def create_bicycles_task(bicycles):
    create_bicycles(bicycles)


