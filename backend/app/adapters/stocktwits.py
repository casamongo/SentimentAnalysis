from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.http_client import get_http_client
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter


@register_adapter("stocktwits")
class StocktwitsAdapter(AbstractSourceAdapter):
    source_name = "stocktwits"
    category = "social"

    BASE_URL = "https://api.stocktwits.com/api/2"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=100)

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()
        client = get_http_client()

        response = await client.get(
            f"{self.BASE_URL}/streams/symbol/{ticker}.json",
        )
        if response.status_code != 200:
            return None

        data = response.json()
        messages = data.get("messages", [])
        if not messages:
            return None

        bulls = 0
        bears = 0
        for msg in messages:
            sentiment = msg.get("entities", {}).get("sentiment", {})
            if sentiment:
                basic = sentiment.get("basic")
                if basic == "Bullish":
                    bulls += 1
                elif basic == "Bearish":
                    bears += 1

        total = bulls + bears
        if total == 0:
            return None

        raw_score = (bulls - bears) / total  # -1 to +1

        return RawSentimentData(
            source_name=self.source_name,
            ticker=ticker,
            raw_score=Decimal(str(round(raw_score, 6))),
            normalized_score=Decimal(str(round(max(-1.0, min(1.0, raw_score)), 6))),
            data_points=total,
            fetched_at=datetime.now(timezone.utc),
            metadata={
                "total_messages": len(messages),
                "bullish_count": bulls,
                "bearish_count": bears,
                "neutral_count": len(messages) - total,
            },
        )

    async def health_check(self) -> bool:
        try:
            client = get_http_client()
            resp = await client.get(f"{self.BASE_URL}/streams/symbol/AAPL.json")
            return resp.status_code == 200
        except Exception:
            return False
