from celery import Celery
import os

CELERY_BROKER_URL = os.getenv("CELERY_BROKER_URL", "redis://redis:6379/0")

celery = Celery(
    "tasks",
    broker=CELERY_BROKER_URL,
    backend="redis://redis:6379/0"
)

celery.conf.task_routes = {
    "app.tasks.example_task.*": {"queue": "default"}
}
