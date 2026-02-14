from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.http_client import get_http_client
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter
from app.core.config import settings


@register_adapter("alpha_vantage")
class AlphaVantageAdapter(AbstractSourceAdapter):
    source_name = "alpha_vantage"
    category = "financial"

    BASE_URL = "https://www.alphavantage.co/query"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=5)
        self._api_key = settings.ALPHA_VANTAGE_KEY

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()
        client = get_http_client()

        response = await client.get(
            self.BASE_URL,
            params={
                "function": "NEWS_SENTIMENT",
                "tickers": ticker,
                "apikey": self._api_key,
                "limit": 50,
            },
        )
        if response.status_code != 200:
            return None

        data = response.json()
        feed = data.get("feed", [])
        if not feed:
            return None

        scores = []
        for article in feed:
            for ts in article.get("ticker_sentiment", []):
                if ts.get("ticker", "").upper() == ticker.upper():
                    score = float(ts.get("ticker_sentiment_score", 0))
                    scores.append(score)

        if not scores:
            return None

        avg_score = sum(scores) / len(scores)
        # Alpha Vantage scores are in [-1, 1] range already
        normalized = max(-1.0, min(1.0, avg_score))

        return RawSentimentData(
            source_name=self.source_name,
            ticker=ticker,
            raw_score=Decimal(str(round(avg_score, 6))),
            normalized_score=Decimal(str(round(normalized, 6))),
            data_points=len(scores),
            fetched_at=datetime.now(timezone.utc),
            metadata={
                "articles_analyzed": len(feed),
                "ticker_mentions": len(scores),
                "avg_relevance": round(
                    sum(
                        float(ts.get("relevance_score", 0))
                        for a in feed
                        for ts in a.get("ticker_sentiment", [])
                        if ts.get("ticker", "").upper() == ticker.upper()
                    ) / max(len(scores), 1),
                    4,
                ),
            },
        )

    async def health_check(self) -> bool:
        try:
            client = get_http_client()
            resp = await client.get(
                self.BASE_URL,
                params={
                    "function": "NEWS_SENTIMENT",
                    "tickers": "AAPL",
                    "apikey": self._api_key,
                    "limit": 1,
                },
            )
            return resp.status_code == 200
        except Exception:
            return False
