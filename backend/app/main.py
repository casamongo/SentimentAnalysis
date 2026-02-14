from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.adapters.http_client import close_http_client
from app.api.v1.router import api_v1_router
from app.core.config import settings
from app.core.database import engine
from app.core.redis import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_http_client()
    await close_redis()
    await engine.dispose()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_v1_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
