"""SourceConfig model for data source configuration."""
import uuid

from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.sql import func

from app.models.base import Base

# Seed data for source configurations
SEED_SOURCES = [
    ("polymarket", "Polymarket", "prediction_market", 1.3, 60),
    ("stocktwits", "Stocktwits", "social", 1.0, 100),
    ("reddit", "Reddit", "social", 1.0, 30),
    ("google_trends", "Google Trends", "alternative", 0.5, 10),
    ("newsapi", "NewsAPI", "news", 1.2, 100),
    ("gdelt", "GDELT", "news", 1.0, 60),
    ("mediastack", "MediaStack", "news", 0.9, 100),
    ("hackernews", "Hacker News", "social", 0.7, 60),
    ("yahoo_finance", "Yahoo Finance", "financial", 1.3, 60),
    ("alpha_vantage", "Alpha Vantage Sentiment", "financial", 1.4, 5),
    ("quiver_quant", "Quiver Quantitative", "alternative", 1.1, 30),
    ("swaggy_stocks", "SwaggyStocks", "social", 0.8, 30),
    ("finnhub", "Finnhub", "financial", 1.5, 60),
]


class SourceConfig(Base):
    """Configuration for a data source."""

    __tablename__ = "source_configs"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    source_name = Column(String(50), unique=True, nullable=False)
    display_name = Column(String(100), nullable=False)
    weight = Column(Numeric(5, 4), nullable=False, server_default="1.0")
    is_enabled = Column(Boolean, nullable=False, server_default="true")
    category = Column(String(30), nullable=False)
    rate_limit_rpm = Column(Integer, nullable=False, server_default="60")
    api_base_url = Column(String(500), nullable=True)
    config_json = Column(JSONB, nullable=False, server_default="{}")
    last_healthy_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
