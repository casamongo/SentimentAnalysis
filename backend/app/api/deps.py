from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_async_session

# Re-export for use as FastAPI dependency
get_db = get_async_session
