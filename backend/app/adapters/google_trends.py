import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter


@register_adapter("google_trends")
class GoogleTrendsAdapter(AbstractSourceAdapter):
    source_name = "google_trends"
    category = "alternative"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=10)

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()

        try:
            from pytrends.request import TrendReq

            loop = asyncio.get_event_loop()
            pytrends = TrendReq(hl="en-US", tz=360)

            # Build payload and get interest over time
            await loop.run_in_executor(
                None,
                lambda: pytrends.build_payload([ticker], timeframe="now 7-d"),
            )
            df = await loop.run_in_executor(None, pytrends.interest_over_time)

            if df is None or df.empty or ticker not in df.columns:
                return None

            values = df[ticker].tolist()
            if not values:
                return None

            current = values[-1]
            avg_7d = sum(values) / len(values)

            # Momentum-based scoring: above average = positive signal
            if avg_7d == 0:
                momentum = 0.0
            else:
                momentum = (current - avg_7d) / max(avg_7d, 1)

            # Clamp to [-1, 1]
            normalized = max(-1.0, min(1.0, momentum))

            return RawSentimentData(
                source_name=self.source_name,
                ticker=ticker,
                raw_score=Decimal(str(round(current, 6))),
                normalized_score=Decimal(str(round(normalized, 6))),
                data_points=len(values),
                fetched_at=datetime.now(timezone.utc),
                metadata={
                    "current_interest": current,
                    "avg_7d_interest": round(avg_7d, 2),
                    "momentum": round(momentum, 4),
                    "peak_interest": max(values),
                },
            )
        except Exception:
            return None

    async def health_check(self) -> bool:
        try:
            from pytrends.request import TrendReq

            loop = asyncio.get_event_loop()
            pytrends = TrendReq(hl="en-US", tz=360)
            await loop.run_in_executor(
                None,
                lambda: pytrends.build_payload(["AAPL"], timeframe="now 1-d"),
            )
            df = await loop.run_in_executor(None, pytrends.interest_over_time)
            return df is not None and not df.empty
        except Exception:
            return False
