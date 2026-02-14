"""AggregateScore model for combined sentiment scores."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class AggregateScore(Base):
    """Aggregated sentiment score combining multiple sources for a stock."""

    __tablename__ = "aggregate_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    score = Column(Numeric(7, 6), nullable=False)
    confidence = Column(Numeric(5, 4), nullable=False)
    sources_available = Column(Integer, nullable=False)
    sources_total = Column(Integer, nullable=False, server_default="13")
    source_breakdown = Column(JSONB, nullable=False)
    weight_breakdown = Column(JSONB, nullable=False)
    sentiment_label = Column(String(20), nullable=False)
    previous_score = Column(Numeric(7, 6), nullable=True)
    score_delta = Column(Numeric(7, 6), nullable=True)
    computed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    stock = relationship("Stock", back_populates="aggregate_scores")
