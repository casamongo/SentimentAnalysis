from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.http_client import get_http_client
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter
from app.core.config import settings


@register_adapter("gdelt")
class GDELTAdapter(AbstractSourceAdapter):
    source_name = "gdelt"
    category = "news"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=60)
        self._base_url = settings.GDELT_BASE_URL

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()
        client = get_http_client()

        response = await client.get(
            f"{self._base_url}/doc/doc",
            params={
                "query": ticker,
                "mode": "tonechart",
                "format": "json",
                "timespan": "24h",
            },
        )
        if response.status_code != 200:
            return None

        data = response.json()
        if not data:
            return None

        # GDELT tone chart returns time-series of average tone
        # Tone ranges from roughly -10 to +10
        tones = []
        if isinstance(data, list):
            for entry in data:
                tone = entry.get("tone", entry.get("value"))
                if tone is not None:
                    tones.append(float(tone))
        elif isinstance(data, dict):
            timeline = data.get("timeline", [])
            for series in timeline:
                for point in series.get("data", []):
                    tone = point.get("value")
                    if tone is not None:
                        tones.append(float(tone))

        if not tones:
            return None

        avg_tone = sum(tones) / len(tones)
        # Normalize tone from [-10, 10] to [-1, 1]
        normalized = self.normalize_score(avg_tone, source_min=-10.0, source_max=10.0)

        return RawSentimentData(
            source_name=self.source_name,
            ticker=ticker,
            raw_score=Decimal(str(round(avg_tone, 6))),
            normalized_score=normalized,
            data_points=len(tones),
            fetched_at=datetime.now(timezone.utc),
            metadata={
                "avg_tone": round(avg_tone, 4),
                "data_points_raw": len(tones),
            },
        )

    async def health_check(self) -> bool:
        try:
            client = get_http_client()
            resp = await client.get(
                f"{self._base_url}/doc/doc",
                params={"query": "Apple", "mode": "tonechart", "format": "json", "timespan": "1h"},
            )
            return resp.status_code == 200
        except Exception:
            return False
