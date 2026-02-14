from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.stock import Stock
from app.schemas.stock import StockCreate, StockList, StockRead, StockUpdate

router = APIRouter()


@router.get("/stocks", response_model=StockList)
async def list_stocks(
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
):
    """List all tracked stocks."""
    query = select(Stock)
    if is_active is not None:
        query = query.filter(Stock.is_active == is_active)
    query = query.order_by(Stock.ticker)

    result = await db.execute(query)
    stocks = result.scalars().all()

    count_query = select(func.count(Stock.id))
    if is_active is not None:
        count_query = count_query.filter(Stock.is_active == is_active)
    total = (await db.execute(count_query)).scalar() or 0

    return StockList(
        stocks=[StockRead.model_validate(s) for s in stocks],
        total=total,
    )


@router.post("/stocks", response_model=StockRead, status_code=201)
async def create_stock(
    stock_in: StockCreate,
    db: AsyncSession = Depends(get_db),
):
    """Add a new stock to track."""
    # Check for duplicate ticker
    existing = await db.execute(
        select(Stock).filter(Stock.ticker == stock_in.ticker.upper())
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Stock {stock_in.ticker} already exists")

    stock = Stock(
        ticker=stock_in.ticker.upper(),
        company_name=stock_in.company_name,
        sector=stock_in.sector,
    )
    db.add(stock)
    await db.commit()
    await db.refresh(stock)
    return StockRead.model_validate(stock)


@router.get("/stocks/{ticker}", response_model=StockRead)
async def get_stock(
    ticker: str,
    db: AsyncSession = Depends(get_db),
):
    """Get stock details by ticker."""
    result = await db.execute(
        select(Stock).filter(Stock.ticker == ticker.upper())
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")
    return StockRead.model_validate(stock)


@router.patch("/stocks/{ticker}", response_model=StockRead)
async def update_stock(
    ticker: str,
    stock_in: StockUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update stock properties."""
    result = await db.execute(
        select(Stock).filter(Stock.ticker == ticker.upper())
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    update_data = stock_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(stock, field, value)

    await db.commit()
    await db.refresh(stock)
    return StockRead.model_validate(stock)


@router.delete("/stocks/{ticker}", status_code=204)
async def delete_stock(
    ticker: str,
    db: AsyncSession = Depends(get_db),
):
    """Remove a stock from tracking."""
    result = await db.execute(
        select(Stock).filter(Stock.ticker == ticker.upper())
    )
    stock = result.scalar_one_or_none()
    if not stock:
        raise HTTPException(status_code=404, detail=f"Stock {ticker} not found")

    await db.delete(stock)
    await db.commit()
