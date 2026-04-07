"""Tests for execution mode safety guards."""

from datetime import UTC, datetime, timedelta

import pytest
from backend.core.execution_mode import (
    ExecutionMode,
    LiveArmingState,
    arm_live,
    disarm_live,
    validate_mode_for_order_submission,
)


def test_replay_disallows_broker():
    """Replay mode must not allow broker submission."""
    assert ExecutionMode.REPLAY.allows_broker_submission is False


def test_shadow_disallows_broker():
    """Shadow mode must not allow broker submission."""
    assert ExecutionMode.SHADOW.allows_broker_submission is False


def test_paper_allows_broker():
    """Paper mode allows broker submission."""
    assert ExecutionMode.PAPER.allows_broker_submission is True


def test_live_allows_broker():
    """Live mode allows broker submission."""
    assert ExecutionMode.LIVE.allows_broker_submission is True


def test_micro_live_allows_broker():
    """Micro-live mode allows broker submission."""
    assert ExecutionMode.MICRO_LIVE.allows_broker_submission is True


def test_live_requires_arming():
    """Live modes require arming."""
    assert ExecutionMode.LIVE.requires_arming is True
    assert ExecutionMode.MICRO_LIVE.requires_arming is True


def test_paper_does_not_require_arming():
    """Paper mode does not require arming."""
    assert ExecutionMode.PAPER.requires_arming is False


def test_replay_does_not_require_arming():
    """Replay mode does not require arming."""
    assert ExecutionMode.REPLAY.requires_arming is False


def test_shadow_does_not_require_arming():
    """Shadow mode does not require arming."""
    assert ExecutionMode.SHADOW.requires_arming is False


def test_live_is_live():
    """Live and micro_live report is_live True."""
    assert ExecutionMode.LIVE.is_live is True
    assert ExecutionMode.MICRO_LIVE.is_live is True


def test_paper_is_not_live():
    """Paper mode is not live."""
    assert ExecutionMode.PAPER.is_live is False


def test_validate_replay_raises():
    """Replay submission must be rejected."""
    with pytest.raises(RuntimeError, match="does not allow"):
        validate_mode_for_order_submission(
            ExecutionMode.REPLAY
        )


def test_validate_shadow_raises():
    """Shadow submission must be rejected."""
    with pytest.raises(RuntimeError, match="does not allow"):
        validate_mode_for_order_submission(
            ExecutionMode.SHADOW
        )


def test_validate_paper_passes():
    """Paper submission should pass."""
    validate_mode_for_order_submission(ExecutionMode.PAPER)


def test_validate_live_unarmed_raises():
    """Live submission without arming must be rejected."""
    disarm_live()
    with pytest.raises(RuntimeError, match="not armed"):
        validate_mode_for_order_submission(
            ExecutionMode.LIVE
        )


def test_validate_micro_live_unarmed_raises():
    """Micro-live unarmed must be rejected."""
    disarm_live()
    with pytest.raises(RuntimeError, match="not armed"):
        validate_mode_for_order_submission(
            ExecutionMode.MICRO_LIVE
        )


def test_validate_live_armed_passes():
    """Live submission with arming should pass."""
    arm_live(
        armed_by="test",
        reason="test",
        armed_until=datetime.now(UTC) + timedelta(hours=1),
    )
    try:
        validate_mode_for_order_submission(
            ExecutionMode.LIVE
        )
    finally:
        disarm_live()


def test_arming_ttl_expired():
    """Expired arming should not be considered armed."""
    state = LiveArmingState(
        armed=True,
        armed_until=datetime.now(UTC) - timedelta(hours=1),
    )
    assert state.is_armed is False


def test_arming_ttl_valid():
    """Valid arming should be considered armed."""
    state = LiveArmingState(
        armed=True,
        armed_until=datetime.now(UTC) + timedelta(hours=1),
    )
    assert state.is_armed is True


def test_arming_not_armed():
    """Unarmed state should not be considered armed."""
    state = LiveArmingState(armed=False)
    assert state.is_armed is False


def test_arming_no_ttl():
    """Armed with no TTL should be considered armed."""
    state = LiveArmingState(armed=True, armed_until=None)
    assert state.is_armed is True


def test_arm_live_returns_state():
    """arm_live should return the new arming state."""
    try:
        state = arm_live(
            armed_by="operator",
            reason="scheduled test",
            armed_until=(
                datetime.now(UTC) + timedelta(hours=1)
            ),
        )
        assert state.armed is True
        assert state.armed_by == "operator"
        assert state.reason == "scheduled test"
    finally:
        disarm_live()


def test_disarm_live_resets():
    """disarm_live should reset to unarmed state."""
    arm_live(
        armed_by="test",
        reason="test",
        armed_until=datetime.now(UTC) + timedelta(hours=1),
    )
    state = disarm_live()
    assert state.armed is False
    assert state.is_armed is False


def test_enum_from_string():
    """ExecutionMode should construct from string."""
    mode = ExecutionMode("replay")
    assert mode == ExecutionMode.REPLAY


def test_enum_all_values():
    """All five execution modes should be defined."""
    modes = list(ExecutionMode)
    assert len(modes) == 5
    values = {m.value for m in modes}
    assert values == {
        "replay",
        "shadow",
        "paper",
        "micro_live",
        "live",
    }
