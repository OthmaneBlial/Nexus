from __future__ import annotations

import os

from celery import Celery

BROKER_URL = os.getenv("NEXUS_CELERY_BROKER", "redis://localhost:6379/0")
RESULT_BACKEND = os.getenv("NEXUS_CELERY_BACKEND", BROKER_URL)

celery_app = Celery("nexus", broker=BROKER_URL, backend=RESULT_BACKEND)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    task_track_started=True,
    result_extended=True,
    worker_send_task_events=True,
    timezone="UTC",
)

__all__ = ["celery_app"]
