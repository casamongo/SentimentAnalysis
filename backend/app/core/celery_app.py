from celery import Celery
from celery.schedules import crontab

from app.core.config import settings

celery_app = Celery(
    "sentiment_tasks",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_soft_time_limit=120,
    task_time_limit=180,
    task_routes={
        "app.tasks.fetch_tasks.*": {"queue": "fetch"},
        "app.tasks.aggregation_tasks.*": {"queue": "aggregate"},
        "app.tasks.cleanup_tasks.*": {"queue": "maintenance"},
        "app.tasks.orchestrator.*": {"queue": "orchestrator"},
    },
    beat_schedule={
        "sentiment-refresh-cycle": {
            "task": "app.tasks.orchestrator.run_sentiment_cycle",
            "schedule": settings.REFRESH_INTERVAL_MINUTES * 60,
            "options": {"queue": "orchestrator"},
        },
        "source-health-check": {
            "task": "app.tasks.health_check_tasks.check_all_sources",
            "schedule": crontab(minute="*/30"),
            "options": {"queue": "maintenance"},
        },
        "data-retention-cleanup": {
            "task": "app.tasks.cleanup_tasks.purge_old_data",
            "schedule": crontab(hour=3, minute=0),
            "options": {"queue": "maintenance"},
        },
    },
)

celery_app.autodiscover_tasks([
    "app.tasks",
])
