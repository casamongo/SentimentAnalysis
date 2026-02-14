from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.http_client import get_http_client
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter
from app.core.config import settings


@register_adapter("finnhub")
class FinnhubAdapter(AbstractSourceAdapter):
    source_name = "finnhub"
    category = "financial"

    BASE_URL = "https://finnhub.io/api/v1"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=60)
        self._api_key = settings.FINNHUB_API_KEY

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()
        client = get_http_client()

        response = await client.get(
            f"{self.BASE_URL}/news-sentiment",
            params={"symbol": ticker, "token": self._api_key},
        )
        if response.status_code != 200:
            return None

        data = response.json()
        sentiment_data = data.get("sentiment", {})
        buzz = data.get("buzz", {})

        if not sentiment_data:
            return None

        bullish = sentiment_data.get("bullishPercent", 0.5)
        bearish = sentiment_data.get("bearishPercent", 0.5)
        raw_score = bullish - bearish  # Range: -1.0 to +1.0

        return RawSentimentData(
            source_name=self.source_name,
            ticker=ticker,
            raw_score=Decimal(str(round(raw_score, 6))),
            normalized_score=Decimal(str(round(max(-1.0, min(1.0, raw_score)), 6))),
            data_points=buzz.get("articlesInLastWeek", 0),
            fetched_at=datetime.now(timezone.utc),
            metadata={
                "bullish_percent": bullish,
                "bearish_percent": bearish,
                "buzz_articles": buzz.get("articlesInLastWeek", 0),
                "weekly_average": buzz.get("weeklyAverage", 0),
                "company_news_score": sentiment_data.get("companyNewsScore", 0),
            },
        )

    async def health_check(self) -> bool:
        try:
            client = get_http_client()
            resp = await client.get(
                f"{self.BASE_URL}/news-sentiment",
                params={"symbol": "AAPL", "token": self._api_key},
            )
            return resp.status_code == 200
        except Exception:
            return False
