import math
from dataclasses import dataclass
from decimal import Decimal

from app.adapters.base import RawSentimentData


@dataclass
class AggregationResult:
    """Output of the aggregation engine."""

    score: Decimal  # Weighted aggregate [-1, +1]
    confidence: Decimal  # 0.0 to 1.0
    sentiment_label: str  # 'very_bearish' to 'very_bullish'
    source_breakdown: dict[str, float]  # source_name -> normalized score
    weight_breakdown: dict[str, float]  # source_name -> effective weight used
    sources_available: int
    sources_total: int


class ScoringService:
    """
    Core aggregation engine.
    Takes individual source scores and produces one master score per stock.
    """

    LABEL_THRESHOLDS = [
        (-1.0, -0.6, "very_bearish"),
        (-0.6, -0.2, "bearish"),
        (-0.2, 0.2, "neutral"),
        (0.2, 0.6, "bullish"),
        (0.6, 1.01, "very_bullish"),
    ]

    def aggregate(
        self,
        source_scores: list[RawSentimentData],
        weight_config: dict[str, float],
    ) -> AggregationResult:
        """
        Compute a weighted average of all available source scores.

        Algorithm:
        1. For each source, compute effective_weight = base_weight * data_quality_factor
        2. Weighted average: sum(score_i * effective_weight_i) / sum(effective_weight_i)
        3. Confidence based on source coverage + data quality
        4. Assign sentiment label
        """
        if not source_scores:
            return AggregationResult(
                score=Decimal("0.0"),
                confidence=Decimal("0.0"),
                sentiment_label="neutral",
                source_breakdown={},
                weight_breakdown={},
                sources_available=0,
                sources_total=len(weight_config),
            )

        source_breakdown: dict[str, float] = {}
        weight_breakdown: dict[str, float] = {}
        weighted_sum = 0.0
        total_weight = 0.0

        for ss in source_scores:
            base_weight = weight_config.get(ss.source_name, 1.0)
            quality_factor = self._data_quality_factor(ss.data_points)
            effective_weight = base_weight * quality_factor

            score_float = float(ss.normalized_score)
            weighted_sum += score_float * effective_weight
            total_weight += effective_weight

            source_breakdown[ss.source_name] = round(score_float, 6)
            weight_breakdown[ss.source_name] = round(effective_weight, 4)

        final_score = weighted_sum / total_weight if total_weight > 0 else 0.0
        final_score = max(-1.0, min(1.0, final_score))

        confidence = self._compute_confidence(
            sources_available=len(source_scores),
            sources_total=len(weight_config),
            data_points=[ss.data_points for ss in source_scores],
        )

        label = self._score_to_label(final_score)

        return AggregationResult(
            score=Decimal(str(round(final_score, 6))),
            confidence=Decimal(str(round(confidence, 4))),
            sentiment_label=label,
            source_breakdown=source_breakdown,
            weight_breakdown=weight_breakdown,
            sources_available=len(source_scores),
            sources_total=len(weight_config),
        )

    @staticmethod
    def _data_quality_factor(data_points: int) -> float:
        """
        Boost weight for sources with more data points.
        Uses a logarithmic curve that plateaus.
        - 0 points -> 0.1
        - 1 point  -> ~0.34
        - 10 points -> ~0.85
        - 50+ points -> ~1.0
        """
        if data_points <= 0:
            return 0.1
        return min(1.0, 0.3 + 0.7 * (1 - math.exp(-data_points / 15.0)))

    @staticmethod
    def _compute_confidence(
        sources_available: int,
        sources_total: int,
        data_points: list[int],
    ) -> float:
        """
        Confidence = 60% source coverage + 40% average data quality.
        """
        if sources_total == 0:
            return 0.0

        coverage = sources_available / sources_total

        quality_factors = [
            min(1.0, 0.3 + 0.7 * (1 - math.exp(-dp / 15.0)))
            for dp in data_points
        ] if data_points else [0.0]
        avg_quality = sum(quality_factors) / len(quality_factors)

        return 0.6 * coverage + 0.4 * avg_quality

    def _score_to_label(self, score: float) -> str:
        for low, high, label in self.LABEL_THRESHOLDS:
            if low <= score < high:
                return label
        return "neutral"
