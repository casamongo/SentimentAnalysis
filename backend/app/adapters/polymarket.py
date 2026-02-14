from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.http_client import get_http_client
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter


@register_adapter("polymarket")
class PolymarketAdapter(AbstractSourceAdapter):
    source_name = "polymarket"
    category = "prediction_market"

    GAMMA_API_URL = "https://gamma-api.polymarket.com"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=60)

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()
        client = get_http_client()

        # Search for markets related to this stock/company
        response = await client.get(
            f"{self.GAMMA_API_URL}/markets",
            params={"tag": ticker, "active": True, "limit": 10},
        )
        if response.status_code != 200:
            return None

        markets = response.json()
        if not markets:
            return None

        probabilities = []
        market_titles = []
        for market in markets:
            outcome_prices = market.get("outcomePrices", "")
            if outcome_prices:
                try:
                    prices = [
                        float(p)
                        for p in outcome_prices.strip("[]").split(",")
                        if p.strip()
                    ]
                    if prices:
                        probabilities.append(prices[0])
                        market_titles.append(market.get("question", ""))
                except (ValueError, IndexError):
                    continue

        if not probabilities:
            return None

        avg_probability = sum(probabilities) / len(probabilities)
        # Map [0.0, 1.0] probability to [-1.0, +1.0]
        normalized = self.normalize_score(avg_probability, source_min=0.0, source_max=1.0)

        return RawSentimentData(
            source_name=self.source_name,
            ticker=ticker,
            raw_score=Decimal(str(round(avg_probability, 6))),
            normalized_score=normalized,
            data_points=len(probabilities),
            fetched_at=datetime.now(timezone.utc),
            metadata={
                "markets_found": len(markets),
                "avg_probability": round(avg_probability, 4),
                "market_titles": market_titles[:5],
            },
        )

    async def health_check(self) -> bool:
        try:
            client = get_http_client()
            resp = await client.get(
                f"{self.GAMMA_API_URL}/markets", params={"limit": 1}
            )
            return resp.status_code == 200
        except Exception:
            return False
