"""Initial schema with all tables and seed data

Revision ID: 001
Revises: None
Create Date: 2026-02-13

"""
from typing import Sequence, Union

import uuid
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

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


def upgrade() -> None:
    # stocks
    op.create_table(
        "stocks",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("ticker", sa.String(10), unique=True, nullable=False, index=True),
        sa.Column("company_name", sa.String(255), nullable=False),
        sa.Column("sector", sa.String(100), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # source_configs
    op.create_table(
        "source_configs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("source_name", sa.String(50), unique=True, nullable=False),
        sa.Column("display_name", sa.String(100), nullable=False),
        sa.Column("weight", sa.Numeric(5, 4), nullable=False, server_default="1.0"),
        sa.Column("is_enabled", sa.Boolean, nullable=False, server_default=sa.text("true")),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("rate_limit_rpm", sa.Integer, nullable=False, server_default="60"),
        sa.Column("api_base_url", sa.String(500), nullable=True),
        sa.Column("config_json", JSONB, nullable=False, server_default="{}"),
        sa.Column("last_healthy_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # source_scores
    op.create_table(
        "source_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("stock_id", UUID(as_uuid=True), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_name", sa.String(50), nullable=False),
        sa.Column("raw_score", sa.Numeric(10, 6), nullable=True),
        sa.Column("normalized_score", sa.Numeric(7, 6), nullable=False),
        sa.Column("data_points", sa.Integer, nullable=False, server_default="0"),
        sa.Column("metadata_json", JSONB, nullable=False, server_default="{}"),
        sa.Column("fetched_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("scored_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_source_scores_stock_time", "source_scores", ["stock_id", sa.text("fetched_at DESC")])
    op.create_index("idx_source_scores_source_time", "source_scores", ["source_name", sa.text("fetched_at DESC")])
    op.create_index(
        "idx_source_scores_lookup", "source_scores",
        ["stock_id", "source_name", sa.text("fetched_at DESC")],
    )

    # aggregate_scores
    op.create_table(
        "aggregate_scores",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("stock_id", UUID(as_uuid=True), sa.ForeignKey("stocks.id", ondelete="CASCADE"), nullable=False),
        sa.Column("score", sa.Numeric(7, 6), nullable=False),
        sa.Column("confidence", sa.Numeric(5, 4), nullable=False),
        sa.Column("sources_available", sa.Integer, nullable=False),
        sa.Column("sources_total", sa.Integer, nullable=False, server_default="13"),
        sa.Column("source_breakdown", JSONB, nullable=False),
        sa.Column("weight_breakdown", JSONB, nullable=False),
        sa.Column("sentiment_label", sa.String(20), nullable=False),
        sa.Column("previous_score", sa.Numeric(7, 6), nullable=True),
        sa.Column("score_delta", sa.Numeric(7, 6), nullable=True),
        sa.Column("computed_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("idx_aggregate_scores_stock_time", "aggregate_scores", ["stock_id", sa.text("computed_at DESC")])

    # fetch_logs
    op.create_table(
        "fetch_logs",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("cycle_id", UUID(as_uuid=True), nullable=False, index=True),
        sa.Column("source_name", sa.String(50), nullable=False),
        sa.Column("stock_ticker", sa.String(10), nullable=True),
        sa.Column("status", sa.String(20), nullable=False),
        sa.Column("duration_ms", sa.Integer, nullable=True),
        sa.Column("data_points", sa.Integer, nullable=False, server_default="0"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("response_meta", JSONB, nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_fetch_logs_source_time", "fetch_logs", ["source_name", sa.text("started_at DESC")])

    # Seed source configs
    source_configs_table = sa.table(
        "source_configs",
        sa.column("id", UUID(as_uuid=True)),
        sa.column("source_name", sa.String),
        sa.column("display_name", sa.String),
        sa.column("category", sa.String),
        sa.column("weight", sa.Numeric),
        sa.column("rate_limit_rpm", sa.Integer),
    )
    op.bulk_insert(
        source_configs_table,
        [
            {
                "id": str(uuid.uuid4()),
                "source_name": name,
                "display_name": display,
                "category": cat,
                "weight": weight,
                "rate_limit_rpm": rpm,
            }
            for name, display, cat, weight, rpm in SEED_SOURCES
        ],
    )


def downgrade() -> None:
    op.drop_table("fetch_logs")
    op.drop_table("aggregate_scores")
    op.drop_table("source_scores")
    op.drop_table("source_configs")
    op.drop_table("stocks")
