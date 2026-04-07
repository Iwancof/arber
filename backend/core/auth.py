"""Authentication and authorization.

JWT verification and role-based access control.
Backend verifies tokens directly - does not depend on
Grafana auth proxy as sole trust boundary.
"""

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any

import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import (
    HTTPAuthorizationCredentials,
    HTTPBearer,
)

from backend.config.settings import settings


class Role(StrEnum):
    """User roles with increasing privilege."""

    VIEWER = "viewer"
    OPERATOR = "operator"
    TRADER = "trader"
    ADMIN = "admin"

    def __ge__(self, other: "Role") -> bool:
        order = list(Role)
        return order.index(self) >= order.index(other)

    def __gt__(self, other: "Role") -> bool:
        order = list(Role)
        return order.index(self) > order.index(other)

    def __le__(self, other: "Role") -> bool:
        order = list(Role)
        return order.index(self) <= order.index(other)

    def __lt__(self, other: "Role") -> bool:
        order = list(Role)
        return order.index(self) < order.index(other)


class Capability(StrEnum):
    """Fine-grained capabilities beyond role."""

    CAN_LIVE_TRADE = "can_live_trade"
    CAN_ARM_LIVE = "can_arm_live"
    CAN_KILL_SWITCH = "can_kill_switch"
    CAN_MANAGE_SOURCES = "can_manage_sources"


@dataclass
class CurrentUser:
    """Authenticated user context."""

    user_id: str
    role: Role
    capabilities: list[Capability] = field(
        default_factory=list
    )
    email: str | None = None

    def has_role(self, minimum: Role) -> bool:
        return self.role >= minimum

    def has_capability(self, cap: Capability) -> bool:
        return cap in self.capabilities


# --- JWT verification ---

_bearer_scheme = HTTPBearer(auto_error=False)


def _decode_jwt(token: str) -> dict[str, Any]:
    """Decode and verify a JWT token."""
    try:
        payload = jwt.decode(
            token,
            settings.jwt_secret,
            algorithms=[settings.jwt_algorithm],
            options={"verify_exp": True},
        )
        return payload
    except jwt.ExpiredSignatureError as e:
        raise HTTPException(
            status_code=401, detail="Token expired"
        ) from e
    except jwt.InvalidTokenError as e:
        raise HTTPException(
            status_code=401, detail="Invalid token"
        ) from e


async def get_current_user(
    request: Request,
    credentials: (
        HTTPAuthorizationCredentials | None
    ) = Depends(_bearer_scheme),
) -> CurrentUser:
    """Extract authenticated user from JWT.

    In development mode (settings.auth_disabled), returns
    a default admin user.
    """
    if settings.auth_disabled:
        return CurrentUser(
            user_id="dev-user",
            role=Role.ADMIN,
            capabilities=list(Capability),
            email="dev@localhost",
        )

    if credentials is None:
        raise HTTPException(
            status_code=401,
            detail="Authentication required",
        )

    payload = _decode_jwt(credentials.credentials)

    role_str = payload.get("role", "viewer")
    try:
        role = Role(role_str)
    except ValueError:
        role = Role.VIEWER

    caps = [
        Capability(c)
        for c in payload.get("capabilities", [])
        if c in Capability.__members__.values()
    ]

    return CurrentUser(
        user_id=payload.get("sub", "unknown"),
        role=role,
        capabilities=caps,
        email=payload.get("email"),
    )


# --- Role requirement dependencies ---


def require_role(minimum: Role):
    """FastAPI dependency requiring a minimum role."""

    async def _check(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not user.has_role(minimum):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Role '{minimum.value}' or higher "
                    f"required. "
                    f"Current: '{user.role.value}'"
                ),
            )
        return user

    return _check


def require_capability(cap: Capability):
    """FastAPI dependency requiring a capability."""

    async def _check(
        user: CurrentUser = Depends(get_current_user),
    ) -> CurrentUser:
        if not user.has_capability(cap):
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Capability '{cap.value}' required"
                ),
            )
        return user

    return _check
