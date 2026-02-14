from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.aggregate_score import AggregateScore
from app.models.source_score import SourceScore
from app.models.stock import Stock
from app.schemas.score import (
    AggregateScoreRead,
    ScoreHistory,
    ScoreHistoryPoint,
    ScoreSummary,
    SourceScoreRead,
)

router = APIRouter()


@router.get("/scores/{ticker}/latest", response_model=AggregateScoreRead)
async def get_latest_score(
    ticker: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the latest aggregate sentiment score for a stock."""
    stock = await _get_stock_or_404(db, ticker)

    result = await db.execute(
        select(AggregateScore)
        .filter(AggregateScore.stock_id == stock.id)
        .order_by(desc(AggregateScore.computed_at))
        .limit(1)
    )
    agg = result.scalar_one_or_none()
    if not agg:
        raise HTTPException(status_code=404, detail=f"No scores yet for {ticker}")

    return AggregateScoreRead(
        ticker=stock.ticker,
        company_name=stock.company_name,
        score=float(agg.score),
        confidence=float(agg.confidence),
        sentiment_label=agg.sentiment_label,
        sources_available=agg.sources_available,
        sources_total=agg.sources_total,
        source_breakdown=agg.source_breakdown,
        weight_breakdown=agg.weight_breakdown,
        previous_score=float(agg.previous_score) if agg.previous_score else None,
        score_delta=float(agg.score_delta) if agg.score_delta else None,
        computed_at=agg.computed_at,
    )


@router.get("/scores/{ticker}/sources", response_model=list[SourceScoreRead])
async def get_source_scores(
    ticker: str,
    db: AsyncSession = Depends(get_db),
):
    """Get the latest scores from all sources for a stock."""
    stock = await _get_stock_or_404(db, ticker)

    # Get the most recent score from each source using a subquery
    # For simplicity, get scores from the last cycle (last 20 minutes)
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=20)

    result = await db.execute(
        select(SourceScore)
        .filter(
            SourceScore.stock_id == stock.id,
            SourceScore.fetched_at >= cutoff,
        )
        .order_by(desc(SourceScore.fetched_at))
    )
    scores = result.scalars().all()

    # Deduplicate: keep only the latest per source
    seen_sources: set[str] = set()
    unique_scores: list[SourceScore] = []
    for s in scores:
        if s.source_name not in seen_sources:
            seen_sources.add(s.source_name)
            unique_scores.append(s)

    return [SourceScoreRead.model_validate(s) for s in unique_scores]


@router.get("/scores/{ticker}/history", response_model=ScoreHistory)
async def get_score_history(
    ticker: str,
    from_time: datetime | None = Query(None, alias="from"),
    to_time: datetime | None = Query(None, alias="to"),
    limit: int = Query(100, ge=1, le=1000),
    db: AsyncSession = Depends(get_db),
):
    """Get historical aggregate scores for a stock."""
    stock = await _get_stock_or_404(db, ticker)

    if from_time is None:
        from_time = datetime.now(timezone.utc) - timedelta(hours=24)
    if to_time is None:
        to_time = datetime.now(timezone.utc)

    result = await db.execute(
        select(AggregateScore)
        .filter(
            AggregateScore.stock_id == stock.id,
            AggregateScore.computed_at >= from_time,
            AggregateScore.computed_at <= to_time,
        )
        .order_by(desc(AggregateScore.computed_at))
        .limit(limit)
    )
    scores = result.scalars().all()

    return ScoreHistory(
        ticker=stock.ticker,
        data=[
            ScoreHistoryPoint(
                score=float(s.score),
                confidence=float(s.confidence),
                sentiment_label=s.sentiment_label,
                sources_available=s.sources_available,
                computed_at=s.computed_at,
            )
            for s in reversed(scores)  # Oldest first for charting
        ],
        total=len(scores),
    )


@router.get("/scores/summary", response_model=list[ScoreSummary])
async def get_all_summaries(
    db: AsyncSession = Depends(get_db),
):
    """Get a summary of the latest scores for all active stocks."""
    result = await db.execute(
        select(Stock).filter(Stock.is_active.is_(True)).order_by(Stock.ticker)
    )
    stocks = result.scalars().all()

    summaries: list[ScoreSummary] = []
    for stock in stocks:
        agg_result = await db.execute(
            select(AggregateScore)
            .filter(AggregateScore.stock_id == stock.id)
            .order_by(desc(AggregateScore.computed_at))
            .limit(1)
        )
        agg = agg_result.scalar_one_or_none()

        summaries.append(
            ScoreSummary(
                ticker=stock.ticker,
                company_name=stock.company_name,
                score=float(agg.score) if agg else 0.0,
                confidence=float(agg.confidence) if agg else 0.0,
                sentiment_label=agg.sentiment_label if agg else "neutral",
                score_delta=float(agg.score_delta) if agg and agg.score_delta else None,
                sources_available=agg.sources_available if agg else 0,
                computed_at=agg.computed_at if agg else None,
            )
        )

    return summaries


async def _get_stock_or_404(db: AsyncSession, ticker: str) -> Stock:
    result = await db.execute(
        select(Stock).filter(Stock.ticker == ticker.upper())
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    return stock
