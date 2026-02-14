import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter
from app.nlp.sentiment_analyzer import SentimentAnalyzer


@register_adapter("yahoo_finance")
class YahooFinanceAdapter(AbstractSourceAdapter):
    source_name = "yahoo_finance"
    category = "financial"

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=60)
        self._analyzer = SentimentAnalyzer()

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()
        loop = asyncio.get_event_loop()

        try:
            import yfinance as yf

            stock = yf.Ticker(ticker)
            news = await loop.run_in_executor(None, lambda: stock.news)

            if not news:
                return None

            titles = [
                item.get("title", "")
                for item in news
                if item.get("title")
            ]

            if not titles:
                return None

            avg_score = self._analyzer.average_score(titles)

            return RawSentimentData(
                source_name=self.source_name,
                ticker=ticker,
                raw_score=Decimal(str(round(avg_score, 6))),
                normalized_score=Decimal(str(round(max(-1.0, min(1.0, avg_score)), 6))),
                data_points=len(titles),
                fetched_at=datetime.now(timezone.utc),
                metadata={
                    "articles_count": len(news),
                    "titles_analyzed": len(titles),
                },
                raw_texts=titles[:20],
            )
        except Exception:
            return None

    async def health_check(self) -> bool:
        try:
            import yfinance as yf

            loop = asyncio.get_event_loop()
            stock = yf.Ticker("AAPL")
            info = await loop.run_in_executor(None, lambda: stock.news)
            return info is not None
        except Exception:
            return False
