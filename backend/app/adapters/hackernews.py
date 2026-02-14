from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.http_client import get_http_client
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter
from app.nlp.sentiment_analyzer import SentimentAnalyzer


@register_adapter("hackernews")
class HackerNewsAdapter(AbstractSourceAdapter):
    source_name = "hackernews"
    category = "social"

    ALGOLIA_URL = "https://hn.algolia.com/api/v1"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=60)
        self._analyzer = SentimentAnalyzer()

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()
        client = get_http_client()

        # Search recent stories and comments
        response = await client.get(
            f"{self.ALGOLIA_URL}/search_by_date",
            params={
                "query": ticker,
                "tags": "(story,comment)",
                "hitsPerPage": 50,
                "numericFilters": "created_at_i>0",
            },
        )
        if response.status_code != 200:
            return None

        data = response.json()
        hits = data.get("hits", [])
        if not hits:
            return None

        texts = []
        for hit in hits:
            title = hit.get("title", "")
            comment_text = hit.get("comment_text", "")
            story_text = hit.get("story_text", "")
            text = title or comment_text or story_text
            if text:
                # Strip HTML tags from comments
                import re

                text = re.sub(r"<[^>]+>", " ", text)
                texts.append(text)

        if not texts:
            return None

        avg_score = self._analyzer.average_score(texts)

        return RawSentimentData(
            source_name=self.source_name,
            ticker=ticker,
            raw_score=Decimal(str(round(avg_score, 6))),
            normalized_score=Decimal(str(round(max(-1.0, min(1.0, avg_score)), 6))),
            data_points=len(texts),
            fetched_at=datetime.now(timezone.utc),
            metadata={
                "hits_found": len(hits),
                "texts_analyzed": len(texts),
                "total_hits": data.get("nbHits", 0),
            },
            raw_texts=texts[:20],
        )

    async def health_check(self) -> bool:
        try:
            client = get_http_client()
            resp = await client.get(
                f"{self.ALGOLIA_URL}/search",
                params={"query": "Apple", "hitsPerPage": 1},
            )
            return resp.status_code == 200
        except Exception:
            return False
