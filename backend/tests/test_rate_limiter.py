"""Tests for the API rate limiter middleware."""

import time
from unittest.mock import patch

from apps.rate_limiter import RateLimiter


class TestRateLimiterUnit:
    """Unit tests for the RateLimiter class."""

    def test_allows_request_under_limit(self):
        """Requests under the limit should be allowed."""
        limiter = RateLimiter(requests_per_minute=10)
        assert limiter.is_allowed("192.168.1.1") is True

    def test_blocks_request_over_limit(self):
        """Requests exceeding the limit should be blocked."""
        limiter = RateLimiter(requests_per_minute=5)
        for _ in range(5):
            limiter.is_allowed("10.0.0.1")
        assert limiter.is_allowed("10.0.0.1") is False

    def test_different_ips_tracked_separately(self):
        """Each IP address should have its own counter."""
        limiter = RateLimiter(requests_per_minute=3)
        for _ in range(3):
            limiter.is_allowed("10.0.0.1")
        # IP 1 is exhausted
        assert limiter.is_allowed("10.0.0.1") is False
        # IP 2 should still be allowed
        assert limiter.is_allowed("10.0.0.2") is True

    def test_window_expires_after_60_seconds(self):
        """Old timestamps should be cleaned up after 60 seconds."""
        limiter = RateLimiter(requests_per_minute=2)
        # Use up the limit
        limiter.is_allowed("10.0.0.1")
        limiter.is_allowed("10.0.0.1")
        assert limiter.is_allowed("10.0.0.1") is False

        # Simulate 61 seconds passing
        with patch.object(time, "time", return_value=time.time() + 61):
            assert limiter.is_allowed("10.0.0.1") is True

    def test_whitelist_paths(self):
        """Whitelist paths should be defined correctly."""
        assert "/api/health" in RateLimiter.WHITELIST_PATHS
        assert "/api/health/ready" in RateLimiter.WHITELIST_PATHS
        assert "/api/health/live" in RateLimiter.WHITELIST_PATHS


class TestRateLimiterIntegration:
    """Integration tests using the FastAPI test client."""

    def test_normal_request_passes(self, client):
        """A normal request should pass through the rate limiter."""
        resp = client.get("/api/health")
        assert resp.status_code == 200

    def test_health_check_not_limited(self, client):
        """Health check endpoints should never be rate-limited."""
        for _ in range(150):
            resp = client.get("/api/health")
            assert resp.status_code == 200

    def test_rate_limit_returns_429(self, client):
        """Exceeding the rate limit should return 429."""
        from main import _rate_limiter

        original = _rate_limiter.requests_per_minute
        _rate_limiter.requests_per_minute = 3
        _rate_limiter._history.clear()
        try:
            for _ in range(3):
                client.get("/docs")
            resp = client.get("/docs")
            assert resp.status_code == 429
            body = resp.json()
            assert body["detail"] == "Too Many Requests"
        finally:
            _rate_limiter.requests_per_minute = original
            _rate_limiter._history.clear()

    def test_rate_limit_response_body(self, client):
        """The 429 response should contain a helpful message."""
        from main import _rate_limiter

        original = _rate_limiter.requests_per_minute
        _rate_limiter.requests_per_minute = 1
        _rate_limiter._history.clear()
        try:
            client.get("/docs")
            resp = client.get("/docs")
            assert resp.status_code == 429
            body = resp.json()
            assert "Rate limit exceeded" in body["message"]
        finally:
            _rate_limiter.requests_per_minute = original
            _rate_limiter._history.clear()

    def test_default_limit_from_config(self):
        """RateLimiter should use config value by default."""
        from config import settings

        limiter = RateLimiter()
        assert limiter.requests_per_minute == settings.RATE_LIMIT_PER_MINUTE
