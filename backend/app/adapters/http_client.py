import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

_client: httpx.AsyncClient | None = None


def get_http_client() -> httpx.AsyncClient:
    """Get or create the shared async HTTP client."""
    global _client
    if _client is None:
        _client = httpx.AsyncClient(
            timeout=httpx.Timeout(30.0, connect=10.0),
            follow_redirects=True,
            limits=httpx.Limits(max_connections=100, max_keepalive_connections=20),
        )
    return _client


async def close_http_client():
    """Close the shared HTTP client. Call on app shutdown."""
    global _client
    if _client is not None:
        await _client.aclose()
        _client = None


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type((httpx.TimeoutException, httpx.NetworkError)),
)
async def resilient_get(url: str, **kwargs) -> httpx.Response:
    """GET request with automatic retries on transient failures."""
    client = get_http_client()
    return await client.get(url, **kwargs)
