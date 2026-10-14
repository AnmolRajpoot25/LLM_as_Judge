"""Rate limiting middleware using slowapi."""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import Request, HTTPException
from src.config.settings import settings

storage_uri = settings.redis_url if (settings.app_env == "production" and settings.redis_url) else "memory://"

limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[f"{settings.rate_limit_requests}/{settings.rate_limit_window}"],
    storage_uri=storage_uri,
)


def rate_limit_exceeded_handler(request: Request, exc: RateLimitExceeded) -> HTTPException:
    return HTTPException(
        status_code=429,
        detail=f"Rate limit exceeded: {exc.detail}",
        headers={"Retry-After": str(exc.retry_after)},
    )