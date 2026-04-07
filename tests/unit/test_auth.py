"""Tests for authentication and RBAC."""

import time

import jwt
import pytest
from backend.config.settings import settings
from backend.core.auth import (
    Capability,
    CurrentUser,
    Role,
    _decode_jwt,
)
from fastapi import HTTPException


def test_role_ordering():
    """Roles should have proper ordering."""
    assert Role.ADMIN >= Role.TRADER
    assert Role.TRADER >= Role.OPERATOR
    assert Role.OPERATOR >= Role.VIEWER
    assert not (Role.VIEWER >= Role.ADMIN)


def test_role_ordering_strict():
    """Strict ordering: ADMIN > TRADER > OPERATOR > VIEWER."""
    assert Role.ADMIN > Role.TRADER
    assert Role.TRADER > Role.OPERATOR
    assert Role.OPERATOR > Role.VIEWER


def test_role_ordering_less_than():
    """Less-than ordering should work."""
    assert Role.VIEWER < Role.OPERATOR
    assert Role.OPERATOR < Role.TRADER
    assert Role.TRADER < Role.ADMIN


def test_role_ordering_le():
    """Less-than-or-equal ordering should work."""
    assert Role.VIEWER <= Role.VIEWER
    assert Role.VIEWER <= Role.OPERATOR
    assert not (Role.ADMIN <= Role.TRADER)


def test_role_equality_ge():
    """Role >= itself should be True."""
    for role in Role:
        assert role >= role


def test_current_user_has_role():
    """CurrentUser should check role level."""
    user = CurrentUser(
        user_id="test", role=Role.TRADER
    )
    assert user.has_role(Role.VIEWER) is True
    assert user.has_role(Role.TRADER) is True
    assert user.has_role(Role.ADMIN) is False


def test_current_user_has_capability():
    """CurrentUser should check capabilities."""
    user = CurrentUser(
        user_id="test",
        role=Role.TRADER,
        capabilities=[Capability.CAN_LIVE_TRADE],
    )
    assert user.has_capability(Capability.CAN_LIVE_TRADE)
    assert not user.has_capability(
        Capability.CAN_KILL_SWITCH
    )


def test_current_user_no_capabilities():
    """CurrentUser with no capabilities denies all."""
    user = CurrentUser(
        user_id="test", role=Role.VIEWER
    )
    for cap in Capability:
        assert not user.has_capability(cap)


def test_current_user_all_capabilities():
    """CurrentUser with all capabilities grants all."""
    user = CurrentUser(
        user_id="test",
        role=Role.ADMIN,
        capabilities=list(Capability),
    )
    for cap in Capability:
        assert user.has_capability(cap)


def test_decode_valid_jwt():
    """Valid JWT should decode correctly."""
    token = jwt.encode(
        {
            "sub": "user-123",
            "role": "trader",
            "capabilities": ["can_live_trade"],
            "exp": time.time() + 3600,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    payload = _decode_jwt(token)
    assert payload["sub"] == "user-123"
    assert payload["role"] == "trader"


def test_decode_expired_jwt():
    """Expired JWT should raise 401."""
    token = jwt.encode(
        {
            "sub": "user-123",
            "exp": time.time() - 3600,
        },
        settings.jwt_secret,
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(HTTPException) as exc_info:
        _decode_jwt(token)
    assert exc_info.value.status_code == 401


def test_decode_invalid_jwt():
    """Invalid JWT should raise 401."""
    with pytest.raises(HTTPException) as exc_info:
        _decode_jwt("invalid.token.here")
    assert exc_info.value.status_code == 401


def test_decode_wrong_secret():
    """JWT signed with wrong secret should raise 401."""
    token = jwt.encode(
        {
            "sub": "user-123",
            "exp": time.time() + 3600,
        },
        "wrong-secret",
        algorithm=settings.jwt_algorithm,
    )
    with pytest.raises(HTTPException) as exc_info:
        _decode_jwt(token)
    assert exc_info.value.status_code == 401


def test_all_capabilities_defined():
    """All expected capabilities should exist."""
    caps = list(Capability)
    assert len(caps) == 4
    assert Capability.CAN_LIVE_TRADE in caps
    assert Capability.CAN_ARM_LIVE in caps
    assert Capability.CAN_KILL_SWITCH in caps
    assert Capability.CAN_MANAGE_SOURCES in caps


def test_all_roles_defined():
    """All expected roles should exist."""
    roles = list(Role)
    assert len(roles) == 4
    values = {r.value for r in roles}
    assert values == {
        "viewer", "operator", "trader", "admin"
    }
