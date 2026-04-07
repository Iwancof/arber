"""Tests for the postmortem judge service."""

from decimal import Decimal

from backend.services.postmortem import judge_verdict


class FakeHorizon:
    """Minimal horizon-like for testing."""

    def __init__(self, p_outperform: Decimal | None = None):
        self.p_outperform_benchmark = p_outperform


def test_verdict_correct_bullish():
    """Predicted up, actually up -> correct."""
    verdict, codes = judge_verdict(
        forecast_horizon=FakeHorizon(Decimal("0.7")),
        realized_rel_return=Decimal("0.03"),
        confidence=Decimal("0.8"),
    )
    assert verdict == "correct"
    assert codes == []


def test_verdict_correct_bearish():
    """Predicted down, actually down -> correct."""
    verdict, codes = judge_verdict(
        forecast_horizon=FakeHorizon(Decimal("0.3")),
        realized_rel_return=Decimal("-0.02"),
        confidence=Decimal("0.7"),
    )
    assert verdict == "correct"
    assert codes == []


def test_verdict_wrong_direction():
    """Predicted up, actually down -> wrong."""
    verdict, codes = judge_verdict(
        forecast_horizon=FakeHorizon(Decimal("0.7")),
        realized_rel_return=Decimal("-0.03"),
        confidence=Decimal("0.8"),
    )
    assert verdict == "wrong"
    assert "direction_error" in codes


def test_verdict_wrong_large_magnitude():
    """Large error should flag magnitude."""
    verdict, codes = judge_verdict(
        forecast_horizon=FakeHorizon(Decimal("0.7")),
        realized_rel_return=Decimal("-0.08"),
        confidence=Decimal("0.8"),
    )
    assert verdict == "wrong"
    assert "direction_error" in codes
    assert "large_magnitude_error" in codes


def test_verdict_mixed_low_confidence():
    """Correct direction but low confidence -> mixed."""
    verdict, codes = judge_verdict(
        forecast_horizon=FakeHorizon(Decimal("0.6")),
        realized_rel_return=Decimal("0.01"),
        confidence=Decimal("0.4"),
    )
    assert verdict == "mixed"
    assert "low_confidence_correct" in codes


def test_verdict_insufficient_no_data():
    """Missing price data -> insufficient."""
    verdict, codes = judge_verdict(
        forecast_horizon=FakeHorizon(Decimal("0.7")),
        realized_rel_return=None,
        confidence=Decimal("0.8"),
    )
    assert verdict == "insufficient"
    assert "missing_price_data" in codes


def test_verdict_insufficient_no_horizon():
    """Missing horizon data -> insufficient."""
    verdict, codes = judge_verdict(
        forecast_horizon=None,
        realized_rel_return=Decimal("0.01"),
        confidence=Decimal("0.8"),
    )
    assert verdict == "insufficient"
    assert "no_horizon_data" in codes


def test_verdict_insufficient_no_p_outperform():
    """Horizon with no p_outperform -> insufficient."""
    verdict, codes = judge_verdict(
        forecast_horizon=FakeHorizon(None),
        realized_rel_return=Decimal("0.01"),
        confidence=Decimal("0.8"),
    )
    assert verdict == "insufficient"
    assert "no_outperform_probability" in codes
