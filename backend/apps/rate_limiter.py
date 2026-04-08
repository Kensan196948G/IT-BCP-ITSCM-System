"""API rate limiting middleware."""

import time
from collections import defaultdict

from fastapi import Request
from fastapi.responses import JSONResponse

from config import settings


class RateLimiter:
    """In-memory rate limiter based on client IP address.

    Tracks request timestamps per IP and rejects requests that exceed
    the configured limit within a 60-second sliding window.
    """

    WHITELIST_PATHS: set[str] = {
        "/api/health",
        "/api/health/ready",
        "/api/health/live",
    }

    def __init__(self, requests_per_minute: int | None = None) -> None:
        self.requests_per_minute = (
            requests_per_minute if requests_per_minute is not None else settings.RATE_LIMIT_PER_MINUTE
        )
        # IP -> list of timestamps
        self._history: dict[str, list[float]] = defaultdict(list)

    def _cleanup(self, ip: str, now: float) -> None:
        """Remove timestamps older than 60 seconds."""
        cutoff = now - 60.0
        self._history[ip] = [ts for ts in self._history[ip] if ts > cutoff]

    def is_allowed(self, ip: str) -> bool:
        """Check whether the IP is within the rate limit."""
        now = time.time()
        self._cleanup(ip, now)
        if len(self._history[ip]) >= self.requests_per_minute:
            return False
        self._history[ip].append(now)
        return True

    async def __call__(self, request: Request, call_next: object) -> JSONResponse:
        """ASGI middleware entry point."""
        # Skip rate limiting for whitelisted paths
        if request.url.path in self.WHITELIST_PATHS:
            response: JSONResponse = await call_next(request)  # type: ignore[operator]
            return response

        client_ip = request.client.host if request.client else "unknown"

        if not self.is_allowed(client_ip):
            return JSONResponse(
                status_code=429,
                content={
                    "detail": "Too Many Requests",
                    "message": (
                        f"Rate limit exceeded. " f"Maximum {self.requests_per_minute} " f"requests per minute."
                    ),
                },
            )

        response = await call_next(request)  # type: ignore[operator]
        return response
