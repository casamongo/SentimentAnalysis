import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class StockCreate(BaseModel):
    ticker: str = Field(..., min_length=1, max_length=10, description="Stock ticker symbol")
    company_name: str = Field(..., min_length=1, max_length=255)
    sector: str | None = None


class StockUpdate(BaseModel):
    company_name: str | None = None
    sector: str | None = None
    is_active: bool | None = None


class StockRead(BaseModel):
    id: uuid.UUID
    ticker: str
    company_name: str
    sector: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class StockList(BaseModel):
    stocks: list[StockRead]
    total: int
