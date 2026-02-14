"""SourceScore model for individual source sentiment scores."""
import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.models.base import Base


class SourceScore(Base):
    """Sentiment score from a single data source for a stock."""

    __tablename__ = "source_scores"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    stock_id = Column(UUID(as_uuid=True), ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False)
    source_name = Column(String(50), nullable=False)
    raw_score = Column(Numeric(10, 6), nullable=True)
    normalized_score = Column(Numeric(7, 6), nullable=False)
    data_points = Column(Integer, nullable=False, server_default="0")
    metadata_json = Column(JSONB, nullable=False, server_default="{}")
    fetched_at = Column(DateTime(timezone=True), nullable=False)
    scored_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationship
    stock = relationship("Stock", back_populates="source_scores")
