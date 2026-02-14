from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_db
from app.models.source_config import SEED_SOURCES, SourceConfig
from app.schemas.source_config import SourceConfigRead, SourceConfigUpdate, SourceHealthRead

router = APIRouter()


@router.get("/sources", response_model=list[SourceConfigRead])
async def list_sources(
    db: AsyncSession = Depends(get_db),
):
    """List all source configurations."""
    result = await db.execute(
        select(SourceConfig).order_by(SourceConfig.category, SourceConfig.source_name)
    )
    configs = result.scalars().all()
    return [SourceConfigRead.model_validate(c) for c in configs]


@router.patch("/sources/{source_name}", response_model=SourceConfigRead)
async def update_source(
    source_name: str,
    source_in: SourceConfigUpdate,
    db: AsyncSession = Depends(get_db),
):
    """Update a source's weight or enabled status."""
    result = await db.execute(
        select(SourceConfig).filter(SourceConfig.source_name == source_name)
    )
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail=f"Source {source_name} not found")

    update_data = source_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(config, field, value)

    await db.commit()
    await db.refresh(config)
    return SourceConfigRead.model_validate(config)


@router.post("/sources/reset-weights", response_model=list[SourceConfigRead])
async def reset_weights(
    db: AsyncSession = Depends(get_db),
):
    """Reset all source weights to default values."""
    default_weights = {s["source_name"]: s["weight"] for s in SEED_SOURCES}

    result = await db.execute(select(SourceConfig))
    configs = result.scalars().all()

    for config in configs:
        if config.source_name in default_weights:
            config.weight = default_weights[config.source_name]

    await db.commit()

    # Re-fetch to return updated values
    result = await db.execute(
        select(SourceConfig).order_by(SourceConfig.category, SourceConfig.source_name)
    )
    configs = result.scalars().all()
    return [SourceConfigRead.model_validate(c) for c in configs]


@router.get("/sources/health", response_model=list[SourceHealthRead])
async def get_health(
    db: AsyncSession = Depends(get_db),
):
    """Get health status of all sources."""
    result = await db.execute(
        select(SourceConfig).order_by(SourceConfig.source_name)
    )
    configs = result.scalars().all()

    # Consider a source healthy if last check was within 60 minutes
    cutoff = datetime.now(timezone.utc) - timedelta(minutes=60)

    return [
        SourceHealthRead(
            source_name=c.source_name,
            display_name=c.display_name,
            is_enabled=c.is_enabled,
            last_healthy_at=c.last_healthy_at,
            is_healthy=c.last_healthy_at is not None and c.last_healthy_at >= cutoff,
        )
        for c in configs
    ]
