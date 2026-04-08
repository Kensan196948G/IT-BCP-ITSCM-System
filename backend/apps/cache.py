"""Redis cache module for IT-BCP-ITSCM-System.

Provides a thin async wrapper around redis.asyncio with:
- Graceful degradation: cache misses and connection failures return None
  so the caller falls back to the database without raising
- JSON serialization/deserialization for any JSON-serializable value
- TTL-based expiry with sensible defaults per data category
"""

from __future__ import annotations

import json
import logging
from typing import Any

import redis.asyncio as aioredis

from config import settings

logger = logging.getLogger(__name__)

# Default TTL values (seconds) — tuned to BCP data update cadences
TTL_DASHBOARD = 60  # readiness dashboard: refresh every minute
TTL_SYSTEM_LIST = 300  # system list: rarely changes
TTL_EXERCISE_LIST = 300  # exercise list: rarely changes
TTL_INCIDENT_LIST = 30  # active incidents: update frequently
TTL_BIA = 600  # BIA data: changes infrequently
TTL_DEFAULT = 120  # fallback


_pool: aioredis.Redis[bytes] | None = None


def _get_client() -> aioredis.Redis[bytes] | None:
    """Return a singleton Redis client, initialising on first call.

    Returns None if the connection cannot be established so callers
    can degrade gracefully rather than raising at import time.
    """
    global _pool
    if _pool is None:
        try:
            _pool = aioredis.from_url(
                settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2,
                socket_timeout=2,
            )
        except Exception as exc:
            logger.warning("Redis unavailable — cache disabled: %s", exc)
            return None
    return _pool


async def get_cached(key: str) -> Any | None:
    """Return the cached value for *key*, or None on miss / error."""
    client = _get_client()
    if client is None:
        return None
    try:
        raw = await client.get(key)
        if raw is None:
            return None
        return json.loads(raw)
    except Exception as exc:
        logger.debug("Cache GET failed for %s: %s", key, exc)
        return None


async def set_cached(key: str, value: Any, ttl: int = TTL_DEFAULT) -> bool:
    """Serialise *value* as JSON and store under *key* with *ttl* seconds.

    Returns True on success, False on error (cache failure is non-fatal).
    """
    client = _get_client()
    if client is None:
        return False
    try:
        await client.setex(key, ttl, json.dumps(value, default=str))
        return True
    except Exception as exc:
        logger.debug("Cache SET failed for %s: %s", key, exc)
        return False


async def invalidate_cache(*keys: str) -> int:
    """Delete one or more cache keys.

    Returns the number of keys actually deleted (0 if Redis is unavailable).
    """
    if not keys:
        return 0
    client = _get_client()
    if client is None:
        return 0
    try:
        return await client.delete(*keys)
    except Exception as exc:
        logger.debug("Cache DELETE failed for %s: %s", keys, exc)
        return 0


async def invalidate_pattern(pattern: str) -> int:
    """Delete all keys matching a glob *pattern* (e.g. 'dashboard:*').

    Uses SCAN to avoid blocking the Redis server on large keyspaces.
    Returns the number of keys deleted.
    """
    client = _get_client()
    if client is None:
        return 0
    deleted = 0
    try:
        async for key in client.scan_iter(match=pattern, count=100):
            await client.delete(key)
            deleted += 1
    except Exception as exc:
        logger.debug("Cache SCAN/DELETE failed for pattern %s: %s", pattern, exc)
    return deleted


async def ping() -> bool:
    """Return True if Redis is reachable, False otherwise."""
    client = _get_client()
    if client is None:
        return False
    try:
        return await client.ping()
    except Exception:
        return False
