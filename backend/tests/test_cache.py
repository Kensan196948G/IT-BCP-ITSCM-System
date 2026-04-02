"""Tests for the Redis cache module (apps/cache.py).

All tests mock the Redis client so no real Redis instance is required.
This ensures the test suite passes in CI without infrastructure dependencies.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

import apps.cache as cache_module
from apps.cache import (
    TTL_DEFAULT,
    get_cached,
    invalidate_cache,
    invalidate_pattern,
    ping,
    set_cached,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_redis_mock(**method_overrides) -> AsyncMock:
    """Return an AsyncMock mimicking a redis.asyncio.Redis client."""
    mock = AsyncMock()
    for attr, value in method_overrides.items():
        setattr(mock, attr, value)
    return mock


# ---------------------------------------------------------------------------
# _get_client
# ---------------------------------------------------------------------------


class TestGetClient:
    def setup_method(self):
        # Reset singleton between tests
        cache_module._pool = None

    def teardown_method(self):
        cache_module._pool = None

    def test_returns_none_on_connection_error(self):
        with patch("apps.cache.aioredis.from_url", side_effect=Exception("refused")):
            client = cache_module._get_client()
        assert client is None

    def test_reuses_existing_pool(self):
        mock_redis = _make_redis_mock()
        cache_module._pool = mock_redis
        client = cache_module._get_client()
        assert client is mock_redis


# ---------------------------------------------------------------------------
# get_cached
# ---------------------------------------------------------------------------


class TestGetCached:
    def setup_method(self):
        cache_module._pool = None

    def teardown_method(self):
        cache_module._pool = None

    @pytest.mark.asyncio
    async def test_returns_none_when_client_unavailable(self):
        with patch("apps.cache._get_client", return_value=None):
            result = await get_cached("some_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_on_cache_miss(self):
        mock_client = _make_redis_mock(get=AsyncMock(return_value=None))
        with patch("apps.cache._get_client", return_value=mock_client):
            result = await get_cached("missing_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_deserialized_value(self):
        import json

        payload = {"status": "healthy", "score": 95}
        mock_client = _make_redis_mock(get=AsyncMock(return_value=json.dumps(payload)))
        with patch("apps.cache._get_client", return_value=mock_client):
            result = await get_cached("dashboard:readiness")
        assert result == payload

    @pytest.mark.asyncio
    async def test_returns_none_on_redis_error(self):
        mock_client = _make_redis_mock(get=AsyncMock(side_effect=Exception("timeout")))
        with patch("apps.cache._get_client", return_value=mock_client):
            result = await get_cached("error_key")
        assert result is None


# ---------------------------------------------------------------------------
# set_cached
# ---------------------------------------------------------------------------


class TestSetCached:
    def setup_method(self):
        cache_module._pool = None

    def teardown_method(self):
        cache_module._pool = None

    @pytest.mark.asyncio
    async def test_returns_false_when_client_unavailable(self):
        with patch("apps.cache._get_client", return_value=None):
            result = await set_cached("key", {"data": 1})
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        mock_client = _make_redis_mock(setex=AsyncMock(return_value=True))
        with patch("apps.cache._get_client", return_value=mock_client):
            result = await set_cached("key", {"data": 1})
        assert result is True

    @pytest.mark.asyncio
    async def test_uses_default_ttl(self):
        mock_client = _make_redis_mock(setex=AsyncMock(return_value=True))
        with patch("apps.cache._get_client", return_value=mock_client):
            await set_cached("key", "value")
        call_args = mock_client.setex.call_args
        assert call_args[0][1] == TTL_DEFAULT

    @pytest.mark.asyncio
    async def test_uses_custom_ttl(self):
        mock_client = _make_redis_mock(setex=AsyncMock(return_value=True))
        with patch("apps.cache._get_client", return_value=mock_client):
            await set_cached("key", "value", ttl=999)
        call_args = mock_client.setex.call_args
        assert call_args[0][1] == 999

    @pytest.mark.asyncio
    async def test_returns_false_on_redis_error(self):
        mock_client = _make_redis_mock(setex=AsyncMock(side_effect=Exception("OOM")))
        with patch("apps.cache._get_client", return_value=mock_client):
            result = await set_cached("key", {"data": 1})
        assert result is False


# ---------------------------------------------------------------------------
# invalidate_cache
# ---------------------------------------------------------------------------


class TestInvalidateCache:
    def setup_method(self):
        cache_module._pool = None

    def teardown_method(self):
        cache_module._pool = None

    @pytest.mark.asyncio
    async def test_returns_zero_for_empty_keys(self):
        result = await invalidate_cache()
        assert result == 0

    @pytest.mark.asyncio
    async def test_returns_zero_when_client_unavailable(self):
        with patch("apps.cache._get_client", return_value=None):
            result = await invalidate_cache("k1", "k2")
        assert result == 0

    @pytest.mark.asyncio
    async def test_returns_deleted_count(self):
        mock_client = _make_redis_mock(delete=AsyncMock(return_value=2))
        with patch("apps.cache._get_client", return_value=mock_client):
            result = await invalidate_cache("k1", "k2")
        assert result == 2

    @pytest.mark.asyncio
    async def test_returns_zero_on_error(self):
        mock_client = _make_redis_mock(delete=AsyncMock(side_effect=Exception("err")))
        with patch("apps.cache._get_client", return_value=mock_client):
            result = await invalidate_cache("k1")
        assert result == 0


# ---------------------------------------------------------------------------
# invalidate_pattern
# ---------------------------------------------------------------------------


class TestInvalidatePattern:
    def setup_method(self):
        cache_module._pool = None

    def teardown_method(self):
        cache_module._pool = None

    @pytest.mark.asyncio
    async def test_returns_zero_when_client_unavailable(self):
        with patch("apps.cache._get_client", return_value=None):
            result = await invalidate_pattern("dashboard:*")
        assert result == 0

    @pytest.mark.asyncio
    async def test_deletes_matched_keys(self):
        async def _scan_iter(**kwargs):
            for k in ["dashboard:readiness", "dashboard:rto"]:
                yield k

        mock_client = MagicMock()
        mock_client.scan_iter = _scan_iter
        mock_client.delete = AsyncMock(return_value=1)

        with patch("apps.cache._get_client", return_value=mock_client):
            result = await invalidate_pattern("dashboard:*")
        assert result == 2

    @pytest.mark.asyncio
    async def test_returns_zero_on_error(self):
        mock_client = MagicMock()
        mock_client.scan_iter = MagicMock(side_effect=Exception("scan err"))

        with patch("apps.cache._get_client", return_value=mock_client):
            result = await invalidate_pattern("bad:*")
        assert result == 0


# ---------------------------------------------------------------------------
# ping
# ---------------------------------------------------------------------------


class TestPing:
    def setup_method(self):
        cache_module._pool = None

    def teardown_method(self):
        cache_module._pool = None

    @pytest.mark.asyncio
    async def test_returns_false_when_client_unavailable(self):
        with patch("apps.cache._get_client", return_value=None):
            result = await ping()
        assert result is False

    @pytest.mark.asyncio
    async def test_returns_true_on_success(self):
        mock_client = _make_redis_mock(ping=AsyncMock(return_value=True))
        with patch("apps.cache._get_client", return_value=mock_client):
            result = await ping()
        assert result is True

    @pytest.mark.asyncio
    async def test_returns_false_on_error(self):
        mock_client = _make_redis_mock(ping=AsyncMock(side_effect=Exception("refused")))
        with patch("apps.cache._get_client", return_value=mock_client):
            result = await ping()
        assert result is False
