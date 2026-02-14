from datetime import datetime

from pydantic import BaseModel, Field


class SourceConfigRead(BaseModel):
    source_name: str
    display_name: str
    weight: float
    is_enabled: bool
    category: str
    rate_limit_rpm: int
    last_healthy_at: datetime | None

    model_config = {"from_attributes": True}


class SourceConfigUpdate(BaseModel):
    weight: float | None = Field(None, ge=0.0, le=10.0)
    is_enabled: bool | None = None


class SourceHealthRead(BaseModel):
    source_name: str
    display_name: str
    is_enabled: bool
    last_healthy_at: datetime | None
    is_healthy: bool
