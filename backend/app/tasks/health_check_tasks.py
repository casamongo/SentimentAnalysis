import asyncio
from datetime import datetime, timezone

from app.core.celery_app import celery_app


@celery_app.task(name="app.tasks.health_check_tasks.check_all_sources")
def check_all_sources():
    """Check health of all enabled source adapters and update last_healthy_at."""
    from app.core.database import get_sync_session
    from app.models.source_config import SourceConfig
    from app.adapters.registry import get_adapter
    from app.tasks.fetch_tasks import _ensure_adapters_loaded, _get_or_create_event_loop

    _ensure_adapters_loaded()

    with get_sync_session() as session:
        configs = session.query(SourceConfig).filter(SourceConfig.is_enabled.is_(True)).all()
        results = {}

        loop = _get_or_create_event_loop()

        for config in configs:
            try:
                adapter = get_adapter(config.source_name)
                is_healthy = loop.run_until_complete(adapter.health_check())
                if is_healthy:
                    config.last_healthy_at = datetime.now(timezone.utc)
                results[config.source_name] = is_healthy
            except Exception:
                results[config.source_name] = False

        session.commit()

    return results
