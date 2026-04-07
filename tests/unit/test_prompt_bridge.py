"""Tests for the manual expert bridge service."""

from backend.services.prompt_bridge import should_escalate_to_manual


def test_escalate_novel_event_type():
    """Novel event types should always escalate."""
    should, reason = should_escalate_to_manual(
        materiality=0.3,
        confidence=0.8,
        event_type="unknown_event",
        is_novel_event_type=True,
    )
    assert should is True
    assert reason == "novel_event_type"


def test_escalate_high_materiality_low_confidence():
    """High materiality + low confidence should escalate."""
    should, reason = should_escalate_to_manual(
        materiality=0.9,
        confidence=0.3,
        event_type="earnings_beat",
    )
    assert should is True
    assert reason == "high_materiality_low_confidence"


def test_no_escalate_normal():
    """Normal conditions should not escalate."""
    should, reason = should_escalate_to_manual(
        materiality=0.5,
        confidence=0.7,
        event_type="earnings_beat",
    )
    assert should is False
    assert reason == ""


def test_escalate_large_position():
    """Large position size should escalate."""
    should, reason = should_escalate_to_manual(
        materiality=0.3,
        confidence=0.8,
        event_type="earnings_beat",
        position_size_pct=0.06,
    )
    assert should is True
    assert reason == "large_position"


def test_no_escalate_when_materiality_none():
    """None materiality should not trigger materiality check."""
    should, reason = should_escalate_to_manual(
        materiality=None,
        confidence=0.3,
        event_type="earnings_beat",
    )
    assert should is False


def test_no_escalate_high_materiality_high_confidence():
    """High materiality with high confidence should not escalate."""
    should, reason = should_escalate_to_manual(
        materiality=0.9,
        confidence=0.8,
        event_type="earnings_beat",
    )
    assert should is False
