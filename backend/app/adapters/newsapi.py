from datetime import datetime, timedelta, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.http_client import get_http_client
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter
from app.core.config import settings
from app.nlp.sentiment_analyzer import SentimentAnalyzer


@register_adapter("newsapi")
class NewsAPIAdapter(AbstractSourceAdapter):
    source_name = "newsapi"
    category = "news"

    BASE_URL = "https://newsapi.org/v2"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=100)
        self._api_key = settings.NEWSAPI_KEY
        self._analyzer = SentimentAnalyzer()

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()
        client = get_http_client()

        from_date = (datetime.now(timezone.utc) - timedelta(days=1)).strftime("%Y-%m-%d")

        response = await client.get(
            f"{self.BASE_URL}/everything",
            params={
                "q": ticker,
                "from": from_date,
                "sortBy": "publishedAt",
                "pageSize": 50,
                "language": "en",
                "apiKey": self._api_key,
            },
        )
        if response.status_code != 200:
            return None

        data = response.json()
        articles = data.get("articles", [])
        if not articles:
            return None

        texts = []
        for article in articles:
            title = article.get("title", "")
            description = article.get("description", "")
            text = f"{title}. {description}" if description else title
            if text.strip():
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
                "total_results": data.get("totalResults", 0),
                "articles_analyzed": len(texts),
            },
            raw_texts=texts[:20],
        )

    async def health_check(self) -> bool:
        try:
            client = get_http_client()
            resp = await client.get(
                f"{self.BASE_URL}/everything",
                params={"q": "AAPL", "pageSize": 1, "apiKey": self._api_key},
            )
            return resp.status_code == 200
        except Exception:
            return False
