# app/core/celery_app.py
from celery import Celery
from app.config import settings

CELERY_BROKER_URL = settings.redis_url

celery = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend="redis://redis:6379/0"
)

celery.conf.task_routes = {
    "app.tasks.example_task.*": {"queue": "default"}
}
