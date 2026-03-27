"""Tests for JWT authentication and RBAC."""

import pytest
from fastapi.testclient import TestClient

from apps.auth import ROLE_PERMISSIONS, ROLES, auth_service


# ---------------------------------------------------------------------------
# Token generation / verification
# ---------------------------------------------------------------------------


class TestTokenCreation:
    """Token creation tests."""

    def test_create_token_returns_string(self):
        token = auth_service.create_access_token("user1", "admin")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_for_each_role(self):
        for role in ROLES:
            token = auth_service.create_access_token(f"user_{role}", role)
            assert isinstance(token, str)

    def test_create_token_invalid_role_raises(self):
        with pytest.raises(ValueError, match="Invalid role"):
            auth_service.create_access_token("user1", "superadmin")

    def test_verify_token_returns_user_info(self):
        token = auth_service.create_access_token("user1", "admin")
        info = auth_service.verify_token(token)
        assert info["user_id"] == "user1"
        assert info["role"] == "admin"
        assert "permissions" in info

    def test_verify_token_invalid_raises_401(self):
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    def test_token_contains_correct_permissions(self):
        token = auth_service.create_access_token("user1", "viewer")
        info = auth_service.verify_token(token)
        assert info["permissions"] == ROLE_PERMISSIONS["viewer"]

    def test_admin_has_all_permissions(self):
        token = auth_service.create_access_token("admin1", "admin")
        info = auth_service.verify_token(token)
        assert "create" in info["permissions"]
        assert "delete" in info["permissions"]
        assert "manage_users" in info["permissions"]

    def test_viewer_has_read_only(self):
        token = auth_service.create_access_token("viewer1", "viewer")
        info = auth_service.verify_token(token)
        assert info["permissions"] == ["read"]

    def test_auditor_permissions(self):
        token = auth_service.create_access_token("auditor1", "auditor")
        info = auth_service.verify_token(token)
        assert "read" in info["permissions"]
        assert "report" in info["permissions"]
        assert "audit_log" in info["permissions"]
        assert "create" not in info["permissions"]


# ---------------------------------------------------------------------------
# API endpoints
# ---------------------------------------------------------------------------


class TestLoginAPI:
    """Login endpoint tests."""

    def test_login_success(self, client: TestClient):
        resp = client.post(
            "/api/auth/login",
            json={"user_id": "admin1", "password": "test", "role": "admin"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_default_role(self, client: TestClient):
        resp = client.post(
            "/api/auth/login",
            json={"user_id": "user1", "password": ""},
        )
        assert resp.status_code == 200

    def test_login_invalid_role_rejected(self, client: TestClient):
        resp = client.post(
            "/api/auth/login",
            json={"user_id": "user1", "password": "", "role": "superadmin"},
        )
        assert resp.status_code == 422

    def test_me_without_token_401(self, client: TestClient):
        resp = client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_valid_token(self, client: TestClient):
        token = auth_service.create_access_token("user1", "operator")
        resp = client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user1"
        assert data["role"] == "operator"

    def test_refresh_with_valid_token(self, client: TestClient):
        token = auth_service.create_access_token("user1", "admin")
        resp = client.post(
            "/api/auth/refresh",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        # Verify the refreshed token is valid
        info = auth_service.verify_token(data["access_token"])
        assert info["user_id"] == "user1"
        assert info["role"] == "admin"

    def test_refresh_without_token_401(self, client: TestClient):
        resp = client.post("/api/auth/refresh")
        assert resp.status_code == 401
