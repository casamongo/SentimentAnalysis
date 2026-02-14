import uuid
from datetime import datetime, timezone

from celery import chord, group

from app.core.celery_app import celery_app
from app.tasks.fetch_tasks import fetch_source_for_stock
from app.tasks.aggregation_tasks import aggregate_scores_for_stock


@celery_app.task(name="app.tasks.orchestrator.run_sentiment_cycle", bind=True)
def run_sentiment_cycle(self):
    """
    Master orchestrator task. Runs every 15 minutes via Celery Beat.

    Flow:
    1. Generate a unique cycle_id
    2. Get all active stocks and enabled sources from DB
    3. For each stock: fan out fetch tasks for all sources (parallel via chord)
    4. After all fetches complete: run aggregation (chord callback)
    """
    cycle_id = str(uuid.uuid4())
    started_at = datetime.now(timezone.utc).isoformat()

    from app.core.database import get_sync_session
    from app.models.stock import Stock
    from app.models.source_config import SourceConfig

    with get_sync_session() as session:
        active_stocks = session.query(Stock).filter(Stock.is_active.is_(True)).all()
        enabled_sources = session.query(SourceConfig).filter(SourceConfig.is_enabled.is_(True)).all()
        stock_tickers = [s.ticker for s in active_stocks]
        source_names = [s.source_name for s in enabled_sources]

    if not stock_tickers or not source_names:
        return {
            "cycle_id": cycle_id,
            "started_at": started_at,
            "stocks": 0,
            "sources": 0,
            "status": "skipped_no_data",
        }

    for ticker in stock_tickers:
        fetch_group = group(
            fetch_source_for_stock.s(
                source_name=source_name,
                ticker=ticker,
                cycle_id=cycle_id,
            )
            for source_name in source_names
        )

        chord(fetch_group)(
            aggregate_scores_for_stock.s(
                ticker=ticker,
                cycle_id=cycle_id,
            )
        )

    return {
        "cycle_id": cycle_id,
        "started_at": started_at,
        "stocks": len(stock_tickers),
        "sources": len(source_names),
    }
