"""Celery application for async task processing."""

from celery import Celery
from config import settings

celery_app = Celery(
    "vaakai",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "analytics.qa_agent",
    ],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  # 5 min max per task
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
