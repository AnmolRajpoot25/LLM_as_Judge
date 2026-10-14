"""Celery application configuration."""

import logging
from celery import Celery
from src.config.settings import settings

logger = logging.getLogger("llm_judge.worker")

celery_app = Celery(
    "llm_judge_worker",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["src.workers.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    worker_prefetch_multiplier=1,
)

if __name__ == "__main__":
    celery_app.start()
