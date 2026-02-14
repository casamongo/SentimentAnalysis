from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.http_client import get_http_client
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter


@register_adapter("swaggy_stocks")
class SwaggyStocksAdapter(AbstractSourceAdapter):
    source_name = "swaggy_stocks"
    category = "social"

    BASE_URL = "https://api.swaggystocks.com/wsb"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=30)

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()
        client = get_http_client()

        response = await client.get(
            f"{self.BASE_URL}/sentiment/ticker",
            params={"ticker": ticker},
        )
        if response.status_code != 200:
            return None

        data = response.json()
        if not data:
            return None

        # SwaggyStocks returns sentiment data points over time
        if isinstance(data, list):
            sentiments = []
            for entry in data[-10:]:  # Last 10 data points
                score = entry.get("sentiment", entry.get("score"))
                if score is not None:
                    sentiments.append(float(score))

            if not sentiments:
                return None

            avg_score = sum(sentiments) / len(sentiments)
            # Normalize if not already in [-1, 1]
            if all(-1 <= s <= 1 for s in sentiments):
                normalized = avg_score
            else:
                normalized = float(self.normalize_score(avg_score, source_min=-100, source_max=100))

            return RawSentimentData(
                source_name=self.source_name,
                ticker=ticker,
                raw_score=Decimal(str(round(avg_score, 6))),
                normalized_score=Decimal(str(round(max(-1.0, min(1.0, normalized)), 6))),
                data_points=len(sentiments),
                fetched_at=datetime.now(timezone.utc),
                metadata={
                    "data_points_used": len(sentiments),
                    "avg_score": round(avg_score, 4),
                },
            )

        # Handle dict response
        if isinstance(data, dict):
            score = data.get("sentiment", data.get("score"))
            if score is None:
                return None
            score = float(score)
            normalized = max(-1.0, min(1.0, score))

            return RawSentimentData(
                source_name=self.source_name,
                ticker=ticker,
                raw_score=Decimal(str(round(score, 6))),
                normalized_score=Decimal(str(round(normalized, 6))),
                data_points=1,
                fetched_at=datetime.now(timezone.utc),
                metadata={"raw_response_type": "dict"},
            )

        return None

    async def health_check(self) -> bool:
        try:
            client = get_http_client()
            resp = await client.get(
                f"{self.BASE_URL}/sentiment/ticker",
                params={"ticker": "AAPL"},
            )
            return resp.status_code == 200
        except Exception:
            return False
