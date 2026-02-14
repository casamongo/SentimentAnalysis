import asyncio
import json
from typing import AsyncGenerator

import redis.asyncio as aioredis
from fastapi import APIRouter, Query
from sse_starlette.sse import EventSourceResponse

from app.core.config import settings

router = APIRouter()


async def score_event_generator(tickers: list[str]) -> AsyncGenerator[dict, None]:
    """Subscribe to Redis pub/sub and yield SSE events for requested tickers."""
    r = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    pubsub = r.pubsub()
    await pubsub.subscribe("sentiment_updates")

    try:
        while True:
            message = await pubsub.get_message(
                ignore_subscribe_messages=True, timeout=1.0
            )
            if message and message["type"] == "message":
                data = json.loads(message["data"])
                if data.get("ticker") in tickers:
                    yield {
                        "event": "score_update",
                        "data": json.dumps(data),
                    }
            else:
                # Send keepalive comment every second to detect disconnects
                await asyncio.sleep(1)
    finally:
        await pubsub.unsubscribe("sentiment_updates")
        await r.close()


@router.get("/sse/scores")
async def stream_scores(
    tickers: list[str] = Query(..., description="Stock tickers to subscribe to"),
):
    """SSE endpoint for real-time score updates."""
    return EventSourceResponse(score_event_generator(tickers))
