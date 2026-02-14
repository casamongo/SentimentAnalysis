from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any


@dataclass
class RawSentimentData:
    """Standardized output from every adapter."""

    source_name: str
    ticker: str
    raw_score: Decimal | None
    normalized_score: Decimal  # Always -1.0 to +1.0
    data_points: int
    fetched_at: datetime
    metadata: dict[str, Any] = field(default_factory=dict)
    raw_texts: list[str] = field(default_factory=list)


class AbstractSourceAdapter(ABC):
    """
    Base class for all 13 data source adapters.

    Each adapter must:
      1. Fetch raw data from its source
      2. Derive a sentiment signal
      3. Normalize to [-1, +1]
      4. Return RawSentimentData
    """

    source_name: str
    category: str  # 'prediction_market', 'social', 'news', 'financial', 'alternative'

    @abstractmethod
    async def fetch_sentiment(self, ticker: str) -> RawSentimentData | None:
        """
        Fetch and score sentiment for a single stock ticker.
        Returns None if the source cannot provide data for this ticker.
        """
        ...

    @abstractmethod
    async def health_check(self) -> bool:
        """Return True if the source API is reachable and responding."""
        ...

    @staticmethod
    def normalize_score(raw_value: float, source_min: float, source_max: float) -> Decimal:
        """Linearly map a raw value from [source_min, source_max] to [-1.0, +1.0]."""
        if source_max == source_min:
            return Decimal("0.0")
        normalized = 2.0 * (raw_value - source_min) / (source_max - source_min) - 1.0
        clamped = max(-1.0, min(1.0, normalized))
        return Decimal(str(round(clamped, 6)))
