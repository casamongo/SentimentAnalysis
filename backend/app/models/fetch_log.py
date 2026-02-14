"""FetchLog model for tracking data fetch operations."""
import uuid

from sqlalchemy import Column, DateTime, Integer, String, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from app.models.base import Base


class FetchLog(Base):
    """Log entry for a data fetch operation."""

    __tablename__ = "fetch_logs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    cycle_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    source_name = Column(String(50), nullable=False)
    stock_ticker = Column(String(10), nullable=True)
    status = Column(String(20), nullable=False)
    duration_ms = Column(Integer, nullable=True)
    data_points = Column(Integer, nullable=False, server_default="0")
    error_message = Column(Text, nullable=True)
    response_meta = Column(JSONB, nullable=False, server_default="{}")
    started_at = Column(DateTime(timezone=True), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
