from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.http_client import get_http_client
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter
from app.core.config import settings


@register_adapter("quiver_quant")
class QuiverQuantAdapter(AbstractSourceAdapter):
    source_name = "quiver_quant"
    category = "alternative"

    BASE_URL = "https://api.quiverquant.com/beta"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=30)
        self._api_key = settings.QUIVER_QUANT_KEY

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()
        client = get_http_client()

        headers = {"Authorization": f"Token {self._api_key}"}

        # Fetch WSB mentions as a proxy for social sentiment
        response = await client.get(
            f"{self.BASE_URL}/historical/wallstreetbets/{ticker}",
            headers=headers,
        )

        if response.status_code != 200:
            return None

        data = response.json()
        if not data:
            return None

        # Use recent mention data
        recent = data[-10:] if len(data) > 10 else data

        sentiments = []
        for entry in recent:
            sentiment = entry.get("sentiment", 0)
            if sentiment is not None:
                sentiments.append(float(sentiment))

        if not sentiments:
            # Fall back to mention volume as a signal
            mentions = [entry.get("mentions", 0) for entry in recent]
            if not mentions or sum(mentions) == 0:
                return None
            # Higher mentions = more interest, slightly bullish
            avg_mentions = sum(mentions) / len(mentions)
            normalized = min(1.0, avg_mentions / 100.0) * 0.5  # Cap at 0.5

            return RawSentimentData(
                source_name=self.source_name,
                ticker=ticker,
                raw_score=Decimal(str(round(avg_mentions, 6))),
                normalized_score=Decimal(str(round(normalized, 6))),
                data_points=len(mentions),
                fetched_at=datetime.now(timezone.utc),
                metadata={
                    "data_type": "mentions_only",
                    "avg_mentions": round(avg_mentions, 2),
                },
            )

        avg_sentiment = sum(sentiments) / len(sentiments)
        normalized = max(-1.0, min(1.0, avg_sentiment))

        return RawSentimentData(
            source_name=self.source_name,
            ticker=ticker,
            raw_score=Decimal(str(round(avg_sentiment, 6))),
            normalized_score=Decimal(str(round(normalized, 6))),
            data_points=len(sentiments),
            fetched_at=datetime.now(timezone.utc),
            metadata={
                "data_type": "sentiment",
                "avg_sentiment": round(avg_sentiment, 4),
                "data_points_used": len(recent),
            },
        )

    async def health_check(self) -> bool:
        try:
            client = get_http_client()
            headers = {"Authorization": f"Token {self._api_key}"}
            resp = await client.get(
                f"{self.BASE_URL}/historical/wallstreetbets/AAPL",
                headers=headers,
            )
            return resp.status_code == 200
        except Exception:
            return False
