"""Authentication API router."""

from typing import Any

from fastapi import APIRouter, Depends

from apps.auth import AuthService, ROLE_PERMISSIONS, auth_service
from apps.audit_service import audit_service
from apps.schemas import LoginRequest, TokenResponse, UserInfo

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest) -> TokenResponse:
    """Simplified login: issues a JWT based on user_id and role.

    In production, password verification would be performed here.
    """
    # Mock password check — accept anything for now
    token = auth_service.create_access_token(user_id=body.user_id, role=body.role)
    audit_service.log(
        action="login",
        resource_type="auth",
        user_id=body.user_id,
        role=body.role,
        details={"method": "password"},
    )
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserInfo)
async def get_me(
    user: dict[str, Any] = Depends(AuthService.get_current_user),
) -> UserInfo:
    """Return the current authenticated user's info."""
    return UserInfo(
        user_id=user["user_id"],
        role=user["role"],
        permissions=user.get("permissions", ROLE_PERMISSIONS.get(user["role"], [])),
    )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    user: dict[str, Any] = Depends(AuthService.get_current_user),
) -> TokenResponse:
    """Issue a fresh token for an already-authenticated user."""
    token = auth_service.create_access_token(user_id=user["user_id"], role=user["role"])
    return TokenResponse(access_token=token)
