"""Tests for JWT authentication and RBAC."""

import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from jose import jwt

from apps.auth import ALGORITHM, ROLE_PERMISSIONS, ROLES, AuthService, auth_service
from config import settings

# ---------------------------------------------------------------------------
# Token generation / verification
# ---------------------------------------------------------------------------


class TestTokenCreation:
    """Token creation tests."""

    def test_create_token_returns_string(self) -> None:
        token = auth_service.create_access_token("user1", "admin")
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_for_each_role(self) -> None:
        for role in ROLES:
            token = auth_service.create_access_token(f"user_{role}", role)
            assert isinstance(token, str)

    def test_create_token_invalid_role_raises(self) -> None:
        with pytest.raises(ValueError, match="Invalid role"):
            auth_service.create_access_token("user1", "superadmin")

    def test_verify_token_returns_user_info(self) -> None:
        token = auth_service.create_access_token("user1", "admin")
        info = auth_service.verify_token(token)
        assert info["user_id"] == "user1"
        assert info["role"] == "admin"
        assert "permissions" in info

    def test_verify_token_invalid_raises_401(self) -> None:
        from fastapi import HTTPException

        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token("invalid.token.here")
        assert exc_info.value.status_code == 401

    def test_token_contains_correct_permissions(self) -> None:
        token = auth_service.create_access_token("user1", "viewer")
        info = auth_service.verify_token(token)
        assert info["permissions"] == ROLE_PERMISSIONS["viewer"]

    def test_admin_has_all_permissions(self) -> None:
        token = auth_service.create_access_token("admin1", "admin")
        info = auth_service.verify_token(token)
        assert "create" in info["permissions"]
        assert "delete" in info["permissions"]
        assert "manage_users" in info["permissions"]

    def test_viewer_has_read_only(self) -> None:
        token = auth_service.create_access_token("viewer1", "viewer")
        info = auth_service.verify_token(token)
        assert info["permissions"] == ["read"]

    def test_auditor_permissions(self) -> None:
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

    def test_login_success(self, client: TestClient) -> None:
        resp = client.post(
            "/api/auth/login",
            json={"user_id": "admin1", "password": "test", "role": "admin"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_default_role(self, client: TestClient) -> None:
        resp = client.post(
            "/api/auth/login",
            json={"user_id": "user1", "password": ""},
        )
        assert resp.status_code == 200

    def test_login_invalid_role_rejected(self, client: TestClient) -> None:
        resp = client.post(
            "/api/auth/login",
            json={"user_id": "user1", "password": "", "role": "superadmin"},
        )
        assert resp.status_code == 422

    def test_me_without_token_401(self, unauthenticated_client: TestClient) -> None:
        resp = unauthenticated_client.get("/api/auth/me")
        assert resp.status_code == 401

    def test_me_with_valid_token(self, unauthenticated_client: TestClient) -> None:
        token = auth_service.create_access_token("user1", "operator")
        resp = unauthenticated_client.get(
            "/api/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["user_id"] == "user1"
        assert data["role"] == "operator"

    def test_refresh_with_valid_token(self, unauthenticated_client: TestClient) -> None:
        token = auth_service.create_access_token("user1", "admin")
        resp = unauthenticated_client.post(
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

    def test_refresh_without_token_401(self, unauthenticated_client: TestClient) -> None:
        resp = unauthenticated_client.post("/api/auth/refresh")
        assert resp.status_code == 401


# ---------------------------------------------------------------------------
# Edge-case coverage: invalid payload & require_role
# ---------------------------------------------------------------------------


class TestVerifyTokenEdgeCases:
    """Cover verify_token payload validation and require_role."""

    def test_verify_token_missing_sub_raises_401(self) -> None:
        """Token without 'sub' claim raises 401 with 'Invalid token payload'."""
        token_without_sub = jwt.encode(
            {"role": "admin"},
            settings.SECRET_KEY,
            algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token(token_without_sub)
        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail

    def test_verify_token_missing_role_raises_401(self) -> None:
        """Token without 'role' claim raises 401 with 'Invalid token payload'."""
        token_without_role = jwt.encode(
            {"sub": "user1"},
            settings.SECRET_KEY,
            algorithm=ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc_info:
            auth_service.verify_token(token_without_role)
        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_require_role_allows_matching_role(self) -> None:
        """require_role returns user when role matches."""
        check = AuthService.require_role("admin", "operator")
        user = {"user_id": "u1", "role": "admin", "permissions": ["read"]}
        result = await check(user=user)
        assert result["user_id"] == "u1"

    @pytest.mark.asyncio
    async def test_require_role_rejects_wrong_role(self) -> None:
        """require_role raises 403 when user role is not in allowed roles."""
        check = AuthService.require_role("admin")
        user = {"user_id": "u1", "role": "viewer", "permissions": ["read"]}
        with pytest.raises(HTTPException) as exc_info:
            await check(user=user)
        assert exc_info.value.status_code == 403
        assert "viewer" in exc_info.value.detail
