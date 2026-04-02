"""E2E test fixtures for Playwright-based API tests.

These tests run against a live server (local or staging).
They are intentionally separated from unit/integration tests to allow
independent execution in CI: fast unit tests run first, E2E only on deploy gates.

Usage:
    # Against local dev server (must be running on port 8000)
    pytest tests/e2e/ --base-url http://localhost:8000

    # Against staging
    pytest tests/e2e/ --base-url https://staging.itbcp.example.com
"""

import pytest

# Default base URL for local development. Override via --base-url CLI option
# or the PYTEST_BASE_URL environment variable (handled by pytest-base-url plugin).
DEFAULT_BASE_URL = "http://localhost:8000"


@pytest.fixture(scope="session")
def base_url(request) -> str:
    """Resolve the API base URL for E2E tests.

    Priority: --base-url CLI option > PYTEST_BASE_URL env var > DEFAULT_BASE_URL
    """
    url = getattr(request.config, "option", None)
    if url and hasattr(url, "base_url") and url.base_url:
        return url.base_url.rstrip("/")
    return DEFAULT_BASE_URL


@pytest.fixture(scope="session")
def admin_token(base_url: str) -> str:
    """Obtain a valid admin JWT token from the live /api/auth/login endpoint."""
    import httpx

    resp = httpx.post(
        f"{base_url}/api/auth/login",
        json={"user_id": "e2e-admin", "password": "e2e", "role": "admin"},
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def auth_headers(admin_token: str) -> dict[str, str]:
    """Return Authorization headers for authenticated E2E requests."""
    return {"Authorization": f"Bearer {admin_token}"}
