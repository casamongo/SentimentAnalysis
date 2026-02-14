from fastapi import APIRouter

from app.api.v1.endpoints import dashboard, health, historical, scores, sources, sse, stocks

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["health"])
api_v1_router.include_router(stocks.router, tags=["stocks"])
api_v1_router.include_router(scores.router, tags=["scores"])
api_v1_router.include_router(dashboard.router, tags=["dashboard"])
api_v1_router.include_router(historical.router, tags=["historical"])
api_v1_router.include_router(sources.router, tags=["sources"])
api_v1_router.include_router(sse.router, tags=["sse"])
