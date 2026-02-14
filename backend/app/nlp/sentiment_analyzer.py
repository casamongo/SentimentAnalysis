import re

from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


class SentimentAnalyzer:
    """
    Wraps VADER sentiment analyzer for scoring financial text.
    Returns compound score in range [-1.0, +1.0].
    """

    def __init__(self):
        self._vader = SentimentIntensityAnalyzer()

    def score(self, text: str) -> float:
        """Score a single text. Returns [-1.0, +1.0]."""
        cleaned = self._preprocess(text)
        if not cleaned:
            return 0.0
        return self._vader.polarity_scores(cleaned)["compound"]

    def batch_score(self, texts: list[str]) -> list[float]:
        """Score multiple texts. Returns list of [-1.0, +1.0] values."""
        return [self.score(t) for t in texts]

    def average_score(self, texts: list[str]) -> float:
        """Score multiple texts and return their average."""
        scores = self.batch_score(texts)
        if not scores:
            return 0.0
        return sum(scores) / len(scores)

    @staticmethod
    def _preprocess(text: str) -> str:
        """Basic text cleaning for sentiment analysis."""
        if not text:
            return ""
        # Remove URLs
        text = re.sub(r"https?://\S+", "", text)
        # Remove excessive whitespace
        text = re.sub(r"\s+", " ", text).strip()
        return text
