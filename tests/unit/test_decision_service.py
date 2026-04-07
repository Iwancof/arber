"""Tests for the v2 decision policy service."""

from decimal import Decimal

from backend.services.decision import (
    compute_directional_edge,
    compute_priority,
    compute_size_cap,
    determine_action,
    determine_confidence_band,
    determine_initial_status,
    determine_trade_horizon,
)


class FakeHorizon:
    """Minimal horizon-like object for testing."""

    def __init__(
        self, code: str, p_out: Decimal | None = None
    ):
        self.horizon_code = code
        self.p_outperform_benchmark = p_out


# ── Directional Edge ─────────────────────────


def test_edge_no_horizons():
    """No horizons → zero edge."""
    edge, _, _, reasons = compute_directional_edge([])
    assert edge == Decimal("0")
    assert any(r["code"] == "no_horizons" for r in reasons)


def test_edge_bullish():
    """High p_outperform → positive edge."""
    hs = [
        FakeHorizon("1d", Decimal("0.68")),
        FakeHorizon("5d", Decimal("0.63")),
    ]
    edge, e1d, e5d, _ = compute_directional_edge(hs)
    assert edge > Decimal("0")
    assert e1d == Decimal("0.36")
    assert e5d == Decimal("0.26")


def test_edge_bearish():
    """Low p_outperform → negative edge."""
    hs = [
        FakeHorizon("1d", Decimal("0.35")),
        FakeHorizon("5d", Decimal("0.38")),
    ]
    edge, _, _, _ = compute_directional_edge(hs)
    assert edge < Decimal("0")


def test_edge_neutral():
    """p_outperform ~0.5 → near-zero edge."""
    hs = [
        FakeHorizon("1d", Decimal("0.51")),
        FakeHorizon("5d", Decimal("0.50")),
    ]
    edge, _, _, _ = compute_directional_edge(hs)
    assert abs(edge) < Decimal("0.05")


# ── Confidence Band ──────────────────────────


def test_band_noise():
    assert determine_confidence_band(Decimal("0.51")) == "noise"


def test_band_weak():
    assert determine_confidence_band(Decimal("0.58")) == "weak"


def test_band_clear():
    assert determine_confidence_band(Decimal("0.67")) == "clear"


def test_band_strong():
    assert determine_confidence_band(Decimal("0.75")) == "strong"


def test_band_very_strong():
    assert determine_confidence_band(Decimal("0.85")) == "very_strong"


# ── Action Matrix ────────────────────────────


def test_action_noise_always_no_trade():
    action = determine_action(Decimal("0.51"), Decimal("0.5"))
    assert action == "no_trade"


def test_action_clear_high_edge_long():
    """Clear signal + strong edge → long."""
    action = determine_action(
        Decimal("0.67"), Decimal("0.35")
    )
    assert action == "long_candidate"


def test_action_clear_high_edge_short():
    """Clear signal + negative edge → short."""
    action = determine_action(
        Decimal("0.67"), Decimal("-0.35")
    )
    assert action == "short_candidate"


def test_action_clear_moderate_edge_manual():
    """Clear signal + moderate edge → manual."""
    action = determine_action(
        Decimal("0.67"), Decimal("0.25")
    )
    assert action == "wait_manual"


def test_action_clear_low_edge_no_trade():
    """Clear signal + low edge → no trade."""
    action = determine_action(
        Decimal("0.67"), Decimal("0.10")
    )
    assert action == "no_trade"


def test_action_strong_long():
    """Strong + edge>=0.25 → long."""
    action = determine_action(
        Decimal("0.75"), Decimal("0.30")
    )
    assert action == "long_candidate"


def test_action_very_strong_long():
    """Very strong + edge>=0.20 → long."""
    action = determine_action(
        Decimal("0.85"), Decimal("0.22")
    )
    assert action == "long_candidate"


def test_action_weak_high_edge_manual():
    """Weak + very high edge → manual."""
    action = determine_action(
        Decimal("0.58"), Decimal("0.40")
    )
    assert action == "wait_manual"


# ── Size Cap ─────────────────────────────────


def test_size_cap_tier1():
    cap = compute_size_cap(
        Decimal("0.67"), Decimal("0.35"), "long_candidate"
    )
    assert cap == Decimal("2000.00")


def test_size_cap_tier2():
    cap = compute_size_cap(
        Decimal("0.75"), Decimal("0.30"), "long_candidate"
    )
    assert cap == Decimal("3500.0")


def test_size_cap_tier3():
    cap = compute_size_cap(
        Decimal("0.85"), Decimal("0.25"), "long_candidate"
    )
    assert cap == Decimal("5000.00")


def test_size_cap_manual():
    cap = compute_size_cap(
        Decimal("0.60"), Decimal("0.20"), "wait_manual"
    )
    assert cap == Decimal("1500.0")


def test_size_cap_no_trade():
    cap = compute_size_cap(
        Decimal("0.51"), Decimal("0.05"), "no_trade"
    )
    assert cap is None


# ── Trade Horizon ────────────────────────────


def test_horizon_earnings_5d():
    h = determine_trade_horizon(
        "corp_earnings_beat",
        Decimal("0.3"), Decimal("0.2"),
    )
    assert h == "5d"


def test_horizon_analyst_1d():
    h = determine_trade_horizon(
        "market_analyst_upgrade_material",
        Decimal("0.3"), Decimal("0.2"),
    )
    assert h == "1d"


def test_horizon_edge_dominant_1d():
    """1d edge much larger → 1d."""
    h = determine_trade_horizon(
        "unknown",
        Decimal("0.4"), Decimal("0.2"),
    )
    assert h == "1d"


def test_horizon_default_5d():
    h = determine_trade_horizon(
        "unknown",
        Decimal("0.3"), Decimal("0.25"),
    )
    assert h == "5d"


# ── Priority ─────────────────────────────────


def test_priority():
    p = compute_priority(Decimal("0.70"), Decimal("0.30"))
    assert p == Decimal("0.30") * Decimal("0.20")


# ── Status ───────────────────────────────────


def test_status_replay_approved():
    assert determine_initial_status(
        "long_candidate", "replay"
    ) == "approved"


def test_status_paper_candidate():
    assert determine_initial_status(
        "long_candidate", "paper"
    ) == "candidate"


def test_status_manual():
    assert determine_initial_status(
        "wait_manual", "paper"
    ) == "waiting_manual"


def test_status_no_trade():
    assert determine_initial_status(
        "no_trade", "paper"
    ) == "suppressed"
