"""Tests for scoped kill switch types."""

from backend.core.kill_switch import KillSwitchType


def test_all_switch_types_defined():
    """All 5 scoped kill switch types should exist."""
    types = list(KillSwitchType)
    assert len(types) == 5
    assert KillSwitchType.TRADE_HALT_GLOBAL in types
    assert KillSwitchType.REDUCE_ONLY_GLOBAL in types
    assert KillSwitchType.DECISION_HALT in types
    assert KillSwitchType.SOURCE_INGEST_PAUSE in types
    assert KillSwitchType.FULL_FREEZE in types


def test_switch_type_values():
    """Kill switch type values should be strings."""
    assert (
        KillSwitchType.TRADE_HALT_GLOBAL
        == "trade_halt_global"
    )
    assert (
        KillSwitchType.REDUCE_ONLY_GLOBAL
        == "reduce_only_global"
    )
    assert (
        KillSwitchType.DECISION_HALT
        == "decision_halt"
    )
    assert (
        KillSwitchType.SOURCE_INGEST_PAUSE
        == "source_ingest_pause"
    )
    assert (
        KillSwitchType.FULL_FREEZE
        == "full_freeze"
    )


def test_switch_type_from_string():
    """KillSwitchType should construct from string."""
    assert (
        KillSwitchType("trade_halt_global")
        == KillSwitchType.TRADE_HALT_GLOBAL
    )
    assert (
        KillSwitchType("full_freeze")
        == KillSwitchType.FULL_FREEZE
    )


def test_switch_type_is_str():
    """KillSwitchType values should be usable as str."""
    for kt in KillSwitchType:
        assert isinstance(kt, str)
        assert isinstance(kt.value, str)
