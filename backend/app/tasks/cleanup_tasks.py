from datetime import datetime, timedelta, timezone

from app.core.celery_app import celery_app
from app.core.config import settings


@celery_app.task(name="app.tasks.cleanup_tasks.purge_old_data")
def purge_old_data():
    """
    Delete old data based on retention policy.
    - source_scores: DATA_RETENTION_DAYS (90)
    - aggregate_scores: 2x DATA_RETENTION_DAYS (180)
    - fetch_logs: 30 days
    """
    from app.core.database import get_sync_session
    from app.models.aggregate_score import AggregateScore
    from app.models.fetch_log import FetchLog
    from app.models.source_score import SourceScore

    cutoff_source = datetime.now(timezone.utc) - timedelta(days=settings.DATA_RETENTION_DAYS)
    cutoff_aggregate = datetime.now(timezone.utc) - timedelta(days=settings.DATA_RETENTION_DAYS * 2)
    cutoff_logs = datetime.now(timezone.utc) - timedelta(days=30)

    with get_sync_session() as session:
        deleted_sources = (
            session.query(SourceScore)
            .filter(SourceScore.fetched_at < cutoff_source)
            .delete(synchronize_session=False)
        )
        deleted_agg = (
            session.query(AggregateScore)
            .filter(AggregateScore.computed_at < cutoff_aggregate)
            .delete(synchronize_session=False)
        )
        deleted_logs = (
            session.query(FetchLog)
            .filter(FetchLog.started_at < cutoff_logs)
            .delete(synchronize_session=False)
        )
        session.commit()

    return {
        "deleted_source_scores": deleted_sources,
        "deleted_aggregate_scores": deleted_agg,
        "deleted_fetch_logs": deleted_logs,
    }
