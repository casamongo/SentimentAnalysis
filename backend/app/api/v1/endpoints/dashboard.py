from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.aggregate_score import AggregateScore
from app.models.source_score import SourceScore
from app.models.stock import Stock

router = APIRouter()


@router.get("/dashboard/{ticker}")
async def get_dashboard_data(
    ticker: str,
    hours: int = Query(24, ge=1, le=168),
    db: AsyncSession = Depends(get_db),
):
    """Full dashboard payload for a single stock: current score, trend, source breakdown."""
    result = await db.execute(
        select(Stock).filter(Stock.ticker == ticker.upper())
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    # Latest aggregate score
    agg_result = await db.execute(
        select(AggregateScore)
        .filter(AggregateScore.stock_id == stock.id)
        .order_by(desc(AggregateScore.computed_at))
        .limit(1)
    )
    latest = agg_result.scalar_one_or_none()

    # Trend data for the last N hours
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    trend_result = await db.execute(
        select(AggregateScore)
        .filter(
            AggregateScore.stock_id == stock.id,
            AggregateScore.computed_at >= cutoff,
        )
        .order_by(AggregateScore.computed_at)
    )
    trend_scores = trend_result.scalars().all()

    # Latest source scores (last 20 minutes)
    source_cutoff = datetime.now(timezone.utc) - timedelta(minutes=20)
    source_result = await db.execute(
        select(SourceScore)
        .filter(
            SourceScore.stock_id == stock.id,
            SourceScore.fetched_at >= source_cutoff,
        )
        .order_by(desc(SourceScore.fetched_at))
    )
    source_scores = source_result.scalars().all()

    # Deduplicate sources
    seen: set[str] = set()
    unique_sources = []
    for s in source_scores:
        if s.source_name not in seen:
            seen.add(s.source_name)
            unique_sources.append({
                "source_name": s.source_name,
                "normalized_score": float(s.normalized_score),
                "data_points": s.data_points,
                "fetched_at": s.fetched_at.isoformat(),
            })

    return {
        "ticker": stock.ticker,
        "company_name": stock.company_name,
        "current": {
            "score": float(latest.score) if latest else None,
            "confidence": float(latest.confidence) if latest else None,
            "sentiment_label": latest.sentiment_label if latest else None,
            "score_delta": float(latest.score_delta) if latest and latest.score_delta else None,
            "sources_available": latest.sources_available if latest else 0,
            "sources_total": latest.sources_total if latest else 13,
            "source_breakdown": latest.source_breakdown if latest else {},
            "weight_breakdown": latest.weight_breakdown if latest else {},
            "computed_at": latest.computed_at.isoformat() if latest else None,
        },
        "trend": [
            {
                "score": float(s.score),
                "confidence": float(s.confidence),
                "sentiment_label": s.sentiment_label,
                "computed_at": s.computed_at.isoformat(),
            }
            for s in trend_scores
        ],
        "sources": unique_sources,
    }


@router.get("/dashboard/overview")
async def get_overview(
    db: AsyncSession = Depends(get_db),
):
    """Multi-stock overview for the main dashboard page."""
    result = await db.execute(
        select(Stock).filter(Stock.is_active.is_(True)).order_by(Stock.ticker)
    )
    stocks = result.scalars().all()

    overview = []
    for stock in stocks:
        agg_result = await db.execute(
            select(AggregateScore)
            .filter(AggregateScore.stock_id == stock.id)
            .order_by(desc(AggregateScore.computed_at))
            .limit(1)
        )
        latest = agg_result.scalar_one_or_none()

        overview.append({
            "ticker": stock.ticker,
            "company_name": stock.company_name,
            "score": float(latest.score) if latest else None,
            "confidence": float(latest.confidence) if latest else None,
            "sentiment_label": latest.sentiment_label if latest else None,
            "score_delta": float(latest.score_delta) if latest and latest.score_delta else None,
            "sources_available": latest.sources_available if latest else 0,
            "computed_at": latest.computed_at.isoformat() if latest else None,
        })

    return {"stocks": overview}
