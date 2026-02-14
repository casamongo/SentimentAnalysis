from datetime import datetime

from pydantic import BaseModel


class SourceScoreRead(BaseModel):
    source_name: str
    raw_score: float | None
    normalized_score: float
    data_points: int
    metadata_json: dict
    fetched_at: datetime

    model_config = {"from_attributes": True}


class AggregateScoreRead(BaseModel):
    ticker: str
    company_name: str
    score: float
    confidence: float
    sentiment_label: str
    sources_available: int
    sources_total: int
    source_breakdown: dict[str, float]
    weight_breakdown: dict[str, float]
    previous_score: float | None
    score_delta: float | None
    computed_at: datetime

    model_config = {"from_attributes": True}


class ScoreHistoryPoint(BaseModel):
    score: float
    confidence: float
    sentiment_label: str
    sources_available: int
    computed_at: datetime


class ScoreHistory(BaseModel):
    ticker: str
    data: list[ScoreHistoryPoint]
    total: int


class ScoreSummary(BaseModel):
    ticker: str
    company_name: str
    score: float
    confidence: float
    sentiment_label: str
    score_delta: float | None
    sources_available: int
    computed_at: datetime | None
