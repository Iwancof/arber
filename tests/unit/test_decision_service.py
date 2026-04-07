"""Tests for the decision policy service."""

from decimal import Decimal

from backend.services.decision import (
    compute_decision_score,
    determine_action,
    determine_initial_status,
)


class FakeForecast:
    """Minimal forecast-like object for testing."""

    def __init__(self, confidence: Decimal | None = None):
        self.confidence = confidence


class FakeHorizon:
    """Minimal horizon-like object for testing."""

    def __init__(self, horizon_code: str, p_outperform: Decimal | None = None):
        self.horizon_code = horizon_code
        self.p_outperform_benchmark = p_outperform


def test_compute_score_no_horizons():
    """Score should be 0 with no horizons."""
    forecast = FakeForecast(confidence=Decimal("0.7"))
    score, reasons = compute_decision_score(forecast, [])
    assert score == Decimal("0")
    assert any(r["code"] == "no_horizons" for r in reasons)


def test_compute_score_bullish():
    """High confidence + high p_outperform should give positive score."""
    forecast = FakeForecast(confidence=Decimal("0.8"))
    horizons = [
        FakeHorizon("1d", Decimal("0.75")),
        FakeHorizon("5d", Decimal("0.70")),
    ]
    score, reasons = compute_decision_score(forecast, horizons)
    assert score > Decimal("0")
    assert len(reasons) >= 2


def test_compute_score_bearish():
    """Low confidence + low p_outperform should give negative score."""
    forecast = FakeForecast(confidence=Decimal("0.2"))
    horizons = [
        FakeHorizon("1d", Decimal("0.25")),
    ]
    score, reasons = compute_decision_score(forecast, horizons)
    assert score < Decimal("0")


def test_compute_score_neutral():
    """50/50 should give near-zero score."""
    forecast = FakeForecast(confidence=Decimal("0.5"))
    horizons = [
        FakeHorizon("1d", Decimal("0.5")),
    ]
    score, reasons = compute_decision_score(forecast, horizons)
    assert abs(score) < Decimal("0.1")


def test_score_clamped_to_range():
    """Score should be clamped to [-1, 1]."""
    forecast = FakeForecast(confidence=Decimal("1.0"))
    horizons = [
        FakeHorizon("1d", Decimal("1.0")),
        FakeHorizon("5d", Decimal("1.0")),
        FakeHorizon("20d", Decimal("1.0")),
    ]
    score, _ = compute_decision_score(forecast, horizons)
    assert Decimal("-1") <= score <= Decimal("1")


def test_determine_action_long():
    """High score + high confidence should be long_candidate."""
    action = determine_action(Decimal("0.7"), Decimal("0.8"), "replay")
    assert action == "long_candidate"


def test_determine_action_no_trade():
    """Low score + low confidence should be no_trade."""
    action = determine_action(Decimal("0.1"), Decimal("0.3"), "replay")
    assert action == "no_trade"


def test_determine_action_wait_manual():
    """Moderate score + low confidence should be wait_manual."""
    action = determine_action(Decimal("0.5"), Decimal("0.35"), "replay")
    assert action == "wait_manual"


def test_determine_action_short():
    """Very negative score + high confidence should be short_candidate."""
    action = determine_action(Decimal("-0.7"), Decimal("0.8"), "replay")
    assert action == "short_candidate"


def test_initial_status_replay_auto_approved():
    """Replay mode should auto-approve trade actions."""
    status = determine_initial_status("long_candidate", "replay")
    assert status == "approved"


def test_initial_status_shadow_auto_approved():
    """Shadow mode should auto-approve trade actions."""
    status = determine_initial_status("short_candidate", "shadow")
    assert status == "approved"


def test_initial_status_live_candidate():
    """Live mode should leave as candidate."""
    status = determine_initial_status("long_candidate", "live")
    assert status == "candidate"


def test_initial_status_wait_manual():
    """Wait manual action should set waiting_manual status."""
    status = determine_initial_status("wait_manual", "replay")
    assert status == "waiting_manual"


def test_initial_status_no_trade():
    """No trade action should set suppressed status."""
    status = determine_initial_status("no_trade", "live")
    assert status == "suppressed"
