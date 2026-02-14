import asyncio
from datetime import datetime, timezone
from decimal import Decimal

from app.adapters.base import AbstractSourceAdapter, RawSentimentData
from app.adapters.rate_limiter import RateLimiter
from app.adapters.registry import register_adapter
from app.core.config import settings
from app.nlp.sentiment_analyzer import SentimentAnalyzer


@register_adapter("reddit")
class RedditAdapter(AbstractSourceAdapter):
    source_name = "reddit"
    category = "social"

    SUBREDDITS = ["wallstreetbets", "stocks", "investing", "stockmarket"]
    POSTS_PER_SUBREDDIT = 25
    COMMENTS_PER_POST = 10

    def __init__(self):
        self._rate_limiter = RateLimiter(requests_per_minute=30)
        self._analyzer = SentimentAnalyzer()

    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        await self._rate_limiter.acquire()

        try:
            import praw

            reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
            )

            loop = asyncio.get_event_loop()
            texts = await self._gather_texts(loop, reddit, ticker)

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
                    "subreddits_searched": self.SUBREDDITS,
                    "total_texts": len(texts),
                },
                raw_texts=texts[:50],
            )
        except Exception:
            return None

    async def _gather_texts(self, loop, reddit, ticker: str) -> list[str]:
        texts = []

        for subreddit_name in self.SUBREDDITS:
            try:
                subreddit = reddit.subreddit(subreddit_name)
                submissions = await loop.run_in_executor(
                    None,
                    lambda sub=subreddit: list(
                        sub.search(
                            f"${ticker} OR {ticker}",
                            sort="new",
                            time_filter="day",
                            limit=self.POSTS_PER_SUBREDDIT,
                        )
                    ),
                )
                for submission in submissions:
                    texts.append(f"{submission.title} {submission.selftext}")
                    await loop.run_in_executor(
                        None, lambda s=submission: s.comments.replace_more(limit=0)
                    )
                    for comment in submission.comments.list()[: self.COMMENTS_PER_POST]:
                        texts.append(comment.body)
            except Exception:
                continue

        return texts

    async def health_check(self) -> bool:
        try:
            import praw

            reddit = praw.Reddit(
                client_id=settings.REDDIT_CLIENT_ID,
                client_secret=settings.REDDIT_CLIENT_SECRET,
                user_agent=settings.REDDIT_USER_AGENT,
            )
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None, lambda: list(reddit.subreddit("stocks").hot(limit=1))
            )
            return True
        except Exception:
            return False
