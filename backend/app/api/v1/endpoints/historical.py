from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.aggregate_score import AggregateScore
from app.models.source_score import SourceScore
from app.models.stock import Stock

router = APIRouter()


@router.get("/historical/{ticker}")
async def get_historical(
    ticker: str,
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    resolution: str = Query("1h", regex="^(15m|1h|4h|1d)$"),
    include_sources: bool = Query(False),
    limit: int = Query(500, ge=1, le=5000),
    db: AsyncSession = Depends(get_db),
):
    """Historical sentiment data with configurable resolution."""
    result = await db.execute(
        select(Stock).filter(Stock.ticker == ticker.upper())
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    if from_time is None:
        from_time = datetime.now(timezone.utc) - timedelta(days=7)
    if to_time is None:
        to_time = datetime.now(timezone.utc)

    # Fetch all aggregate scores in range
    agg_result = await db.execute(
        select(AggregateScore)
        .filter(
            AggregateScore.stock_id == stock.id,
            AggregateScore.computed_at >= from_time,
            AggregateScore.computed_at <= to_time,
        )
        .order_by(AggregateScore.computed_at)
        .limit(limit)
    )
    scores = agg_result.scalars().all()

    # Resample based on resolution
    resampled = _resample_scores(scores, resolution)

    response = {
        "ticker": stock.ticker,
        "from": from_time.isoformat(),
        "to": to_time.isoformat(),
        "resolution": resolution,
        "data_points": len(resampled),
        "data": resampled,
    }

    if include_sources:
        source_result = await db.execute(
            select(SourceScore)
            .filter(
                SourceScore.stock_id == stock.id,
                SourceScore.fetched_at >= from_time,
                SourceScore.fetched_at <= to_time,
            )
            .order_by(SourceScore.fetched_at)
            .limit(limit * 13)
        )
        source_scores = source_result.scalars().all()
        response["source_data"] = [
            {
                "source_name": s.source_name,
                "normalized_score": float(s.normalized_score),
                "data_points": s.data_points,
                "fetched_at": s.fetched_at.isoformat(),
            }
            for s in source_scores
        ]

    return response


@router.get("/historical/{ticker}/heatmap")
async def get_heatmap(
    ticker: str,
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    db: AsyncSession = Depends(get_db),
):
    """Source x time heatmap data for visualization."""
    result = await db.execute(
        select(Stock).filter(Stock.ticker == ticker.upper())
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    if from_time is None:
        from_time = datetime.now(timezone.utc) - timedelta(days=7)
    if to_time is None:
        to_time = datetime.now(timezone.utc)

    source_result = await db.execute(
        select(SourceScore)
        .filter(
            SourceScore.stock_id == stock.id,
            SourceScore.fetched_at >= from_time,
            SourceScore.fetched_at <= to_time,
        )
        .order_by(SourceScore.fetched_at)
    )
    scores = source_result.scalars().all()

    # Build heatmap: list of {source, time, score}
    heatmap = [
        {
            "source_name": s.source_name,
            "score": float(s.normalized_score),
            "time": s.fetched_at.isoformat(),
        }
        for s in scores
    ]

    return {
        "ticker": stock.ticker,
        "from": from_time.isoformat(),
        "to": to_time.isoformat(),
        "data": heatmap,
    }


def _resample_scores(scores: list, resolution: str) -> list[dict]:
    """Resample scores to the given resolution by bucketing and averaging."""
    if not scores:
        return []

    bucket_seconds = {
        "15m": 900,
        "1h": 3600,
        "4h": 14400,
        "1d": 86400,
    }
    bucket_size = bucket_seconds.get(resolution, 3600)

    # If resolution is 15m, return raw data (that's our native resolution)
    if resolution == "15m":
        return [
            {
                "score": float(s.score),
                "confidence": float(s.confidence),
                "sentiment_label": s.sentiment_label,
                "sources_available": s.sources_available,
                "computed_at": s.computed_at.isoformat(),
            }
            for s in scores
        ]

    # Bucket and average
    buckets: dict[int, list] = {}
    for s in scores:
        ts = int(s.computed_at.timestamp())
        bucket_key = ts - (ts % bucket_size)
        if bucket_key not in buckets:
            buckets[bucket_key] = []
        buckets[bucket_key].append(s)

    resampled = []
    for bucket_key in sorted(buckets.keys()):
        items = buckets[bucket_key]
        avg_score = sum(float(s.score) for s in items) / len(items)
        avg_confidence = sum(float(s.confidence) for s in items) / len(items)
        avg_sources = sum(s.sources_available for s in items) // len(items)

        resampled.append({
            "score": round(avg_score, 6),
            "confidence": round(avg_confidence, 4),
            "sentiment_label": items[-1].sentiment_label,
            "sources_available": avg_sources,
            "computed_at": datetime.fromtimestamp(bucket_key, tz=timezone.utc).isoformat(),
        })

    return resampled
