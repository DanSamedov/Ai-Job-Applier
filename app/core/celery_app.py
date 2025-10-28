# app/core/celery_app.py
from celery import Celery
from app.core.config import settings


celery = Celery(
    "tasks",
    broker=settings.redis_url,
    backend=settings.redis_url,
)

celery.autodiscover_tasks([
    "app.core",
])
