import json
from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import RawSentimentData
from app.core.celery_app import celery_app
from app.services.scoring_service import ScoringService


@celery_app.task(name="app.tasks.aggregation_tasks.aggregate_scores_for_stock")
def aggregate_scores_for_stock(fetch_results: list[dict | None], ticker: str, cycle_id: str):
    """
    Chord callback: receives results from all fetch tasks for one stock.

    1. Filter out None results (failed sources)
    2. Reconstruct RawSentimentData from dicts
    3. Load weight config from DB
    4. Call ScoringService.aggregate()
    5. Persist AggregateScore
    6. Publish SSE event via Redis pub/sub
    """
    valid_results = [r for r in fetch_results if r is not None]

    if not valid_results:
        return {"ticker": ticker, "status": "no_data"}

    source_scores = [
        RawSentimentData(
            source_name=r["source_name"],
            ticker=r["ticker"],
            raw_score=Decimal(r["normalized_score"]),
            normalized_score=Decimal(r["normalized_score"]),
            data_points=r["data_points"],
            fetched_at=datetime.fromisoformat(r["fetched_at"]),
        )
        for r in valid_results
    ]

    from app.core.database import get_sync_session
    from app.models.source_config import SourceConfig

    with get_sync_session() as session:
        configs = session.query(SourceConfig).filter(SourceConfig.is_enabled.is_(True)).all()
        weight_config = {c.source_name: float(c.weight) for c in configs}

    scoring = ScoringService()
    result = scoring.aggregate(source_scores, weight_config)

    _persist_aggregate_score(ticker, result)
    _publish_sse_update(ticker, result)

    return {
        "ticker": ticker,
        "score": str(result.score),
        "confidence": str(result.confidence),
        "label": result.sentiment_label,
        "sources": result.sources_available,
    }


def _persist_aggregate_score(ticker, result):
    from app.core.database import get_sync_session
    from app.models.aggregate_score import AggregateScore
    from app.models.stock import Stock
    from sqlalchemy import desc

    with get_sync_session() as session:
        stock = session.query(Stock).filter(Stock.ticker == ticker).first()
        if not stock:
            return

        previous = (
            session.query(AggregateScore)
            .filter(AggregateScore.stock_id == stock.id)
            .order_by(desc(AggregateScore.computed_at))
            .first()
        )

        previous_score = previous.score if previous else None
        delta = result.score - previous_score if previous_score is not None else None

        agg = AggregateScore(
            stock_id=stock.id,
            score=result.score,
            confidence=result.confidence,
            sources_available=result.sources_available,
            sources_total=result.sources_total,
            source_breakdown=result.source_breakdown,
            weight_breakdown=result.weight_breakdown,
            sentiment_label=result.sentiment_label,
            previous_score=previous_score,
            score_delta=delta,
        )
        session.add(agg)
        session.commit()


def _publish_sse_update(ticker, result):
    """Push update to Redis pub/sub for SSE endpoint to pick up."""
    from app.core.redis import get_sync_redis

    r = get_sync_redis()
    message = json.dumps({
        "event": "score_update",
        "ticker": ticker,
        "score": str(result.score),
        "confidence": str(result.confidence),
        "label": result.sentiment_label,
        "sources_available": result.sources_available,
        "source_breakdown": result.source_breakdown,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })
    r.publish("sentiment_updates", message)
