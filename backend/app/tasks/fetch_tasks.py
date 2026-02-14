import asyncio
import uuid
from datetime import datetime, timezone

from app.core.celery_app import celery_app


@celery_app.task(
    name="app.tasks.fetch_tasks.fetch_source_for_stock",
    bind=True,
    max_retries=2,
    default_retry_delay=30,
    soft_time_limit=60,
    time_limit=90,
)
def fetch_source_for_stock(self, source_name: str, ticker: str, cycle_id: str) -> dict | None:
    """
    Fetch sentiment from one source for one stock.
    Returns serializable dict of the result, or None on failure.
    """
    started_at = datetime.now(timezone.utc)

    try:
        # Import here to ensure adapter registration has happened
        _ensure_adapters_loaded()

        from app.adapters.registry import get_adapter

        adapter = get_adapter(source_name)

        # Run async adapter in sync Celery context
        loop = _get_or_create_event_loop()
        result = loop.run_until_complete(adapter.fetch_sentiment(ticker))

        if result is None:
            _log_fetch(cycle_id, source_name, ticker, "no_data", started_at)
            return None

        _persist_source_score(result)
        _log_fetch(
            cycle_id, source_name, ticker, "success", started_at,
            data_points=result.data_points,
        )

        return {
            "source_name": result.source_name,
            "ticker": result.ticker,
            "normalized_score": str(result.normalized_score),
            "data_points": result.data_points,
            "fetched_at": result.fetched_at.isoformat(),
        }

    except Exception as exc:
        _log_fetch(cycle_id, source_name, ticker, "error", started_at, error=str(exc))
        try:
            raise self.retry(exc=exc)
        except self.MaxRetriesExceededError:
            return None


def _get_or_create_event_loop() -> asyncio.AbstractEventLoop:
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            raise RuntimeError
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop


_adapters_loaded = False


def _ensure_adapters_loaded():
    """Import all adapter modules so their @register_adapter decorators run."""
    global _adapters_loaded
    if _adapters_loaded:
        return
    import app.adapters.finnhub  # noqa: F401
    import app.adapters.alpha_vantage  # noqa: F401
    import app.adapters.yahoo_finance  # noqa: F401
    import app.adapters.newsapi  # noqa: F401
    import app.adapters.gdelt  # noqa: F401
    import app.adapters.mediastack  # noqa: F401
    import app.adapters.reddit  # noqa: F401
    import app.adapters.stocktwits  # noqa: F401
    import app.adapters.swaggy_stocks  # noqa: F401
    import app.adapters.polymarket  # noqa: F401
    import app.adapters.quiver_quant  # noqa: F401
    import app.adapters.hackernews  # noqa: F401
    import app.adapters.google_trends  # noqa: F401
    _adapters_loaded = True


def _persist_source_score(result):
    """Write the source score to the database."""
    from app.core.database import get_sync_session
    from app.models.source_score import SourceScore
    from app.models.stock import Stock

    with get_sync_session() as session:
        stock = session.query(Stock).filter(Stock.ticker == result.ticker).first()
        if not stock:
            return
        score = SourceScore(
            stock_id=stock.id,
            source_name=result.source_name,
            raw_score=result.raw_score,
            normalized_score=result.normalized_score,
            data_points=result.data_points,
            metadata_json=result.metadata,
            fetched_at=result.fetched_at,
        )
        session.add(score)
        session.commit()


def _log_fetch(cycle_id, source_name, ticker, status, started_at, data_points=0, error=None):
    """Write fetch log entry."""
    from app.core.database import get_sync_session
    from app.models.fetch_log import FetchLog

    completed_at = datetime.now(timezone.utc)
    duration_ms = int((completed_at - started_at).total_seconds() * 1000)

    with get_sync_session() as session:
        log = FetchLog(
            cycle_id=uuid.UUID(cycle_id),
            source_name=source_name,
            stock_ticker=ticker,
            status=status,
            duration_ms=duration_ms,
            data_points=data_points,
            error_message=error,
            started_at=started_at,
            completed_at=completed_at,
        )
        session.add(log)
        session.commit()
