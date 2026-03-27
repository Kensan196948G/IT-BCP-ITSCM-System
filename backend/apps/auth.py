"""JWT authentication and RBAC for IT-BCP-ITSCM-System."""

from datetime import datetime, timedelta, timezone
from typing import Any

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from config import settings

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ALGORITHM = "HS256"

ROLES = ("admin", "operator", "viewer", "auditor")

ROLE_PERMISSIONS: dict[str, list[str]] = {
    "admin": [
        "create",
        "read",
        "update",
        "delete",
        "execute_exercise",
        "incident_response",
        "report",
        "audit_log",
        "manage_users",
    ],
    "operator": [
        "create",
        "read",
        "update",
        "delete",
        "execute_exercise",
        "incident_response",
    ],
    "viewer": [
        "read",
    ],
    "auditor": [
        "read",
        "report",
        "audit_log",
    ],
}

# ---------------------------------------------------------------------------
# Bearer scheme (auto_error=False so unauthenticated requests pass through
# when authentication is optional)
# ---------------------------------------------------------------------------

bearer_scheme = HTTPBearer(auto_error=False)


# ---------------------------------------------------------------------------
# AuthService
# ---------------------------------------------------------------------------


class AuthService:
    """JWT token management and role-based access control."""

    @staticmethod
    def create_access_token(
        user_id: str,
        role: str,
        expires_delta: timedelta | None = None,
    ) -> str:
        """Create a signed JWT access token."""
        if role not in ROLES:
            raise ValueError(f"Invalid role: {role}. Must be one of {ROLES}")
        expire = datetime.now(timezone.utc) + (
            expires_delta if expires_delta is not None else timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        )
        payload: dict[str, Any] = {
            "sub": user_id,
            "role": role,
            "permissions": ROLE_PERMISSIONS.get(role, []),
            "exp": expire,
            "iat": datetime.now(timezone.utc),
        }
        return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)

    @staticmethod
    def verify_token(token: str) -> dict[str, Any]:
        """Verify and decode a JWT token.

        Returns a dict with ``user_id`` and ``role`` on success.
        Raises ``HTTPException(401)`` on failure.
        """
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
            user_id: str | None = payload.get("sub")
            role: str | None = payload.get("role")
            if user_id is None or role is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid token payload",
                )
            return {
                "user_id": user_id,
                "role": role,
                "permissions": payload.get("permissions", ROLE_PERMISSIONS.get(role, [])),
            }
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
            )

    @staticmethod
    async def get_current_user(
        credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    ) -> dict[str, Any]:
        """FastAPI dependency that extracts the current user from a Bearer token."""
        if credentials is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Not authenticated",
            )
        return AuthService.verify_token(credentials.credentials)

    @staticmethod
    def require_role(*roles: str):
        """Return a FastAPI dependency that checks the user has one of *roles*."""

        async def _check(
            user: dict[str, Any] = Depends(AuthService.get_current_user),
        ) -> dict[str, Any]:
            if user["role"] not in roles:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail=f"Role '{user['role']}' not permitted. Required: {roles}",
                )
            return user

        return _check


auth_service = AuthService()
