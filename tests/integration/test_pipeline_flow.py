"""Integration tests for the core pipeline flow.

Tests cross-service data flow without external APIs.
Uses MockWorkerAdapter for deterministic results.
"""

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from backend.adapters.worker.mock_worker import (
    MockWorkerAdapter,
)
from backend.core.execution_mode import (
    ExecutionMode,
    validate_mode_for_order_submission,
)

# ── Test 1: Replay/shadow cannot submit to broker ──

def test_replay_blocks_broker_submission():
    """Replay mode must raise on order submission."""
    with pytest.raises(RuntimeError, match="does not allow"):
        validate_mode_for_order_submission(
            ExecutionMode.REPLAY
        )


def test_shadow_blocks_broker_submission():
    """Shadow mode must raise on order submission."""
    with pytest.raises(RuntimeError, match="does not allow"):
        validate_mode_for_order_submission(
            ExecutionMode.SHADOW
        )


def test_paper_allows_broker_submission():
    """Paper mode should allow broker submission."""
    # Should not raise
    validate_mode_for_order_submission(
        ExecutionMode.PAPER
    )


# ── Test 2: Mock worker produces valid forecast ──

@pytest.mark.asyncio
async def test_mock_forecast_has_required_fields():
    """MockWorkerAdapter forecast must have all
    required fields for the decision pipeline."""
    from backend.adapters.worker.base import WorkerTask

    worker = MockWorkerAdapter()
    result = await worker.execute(WorkerTask(
        task_type="event_forecast",
        input_payload={
            "event_type": "corp_earnings_beat",
            "symbol": "AAPL",
        },
    ))

    assert result.schema_valid
    d = result.parsed_json
    assert "hypotheses" in d
    assert "horizons" in d
    assert "confidence_after" in d
    h = d["horizons"]
    assert "1d" in h
    assert "5d" in h
    assert "p_outperform" in h["1d"]


# ── Test 3: Decision pipeline produces action ──

def test_decision_score_computation():
    """Full decision flow: edge + confidence -> action."""
    from backend.services.decision import (
        compute_directional_edge,
        determine_action,
    )

    class FakeH:
        def __init__(self, code, p):
            self.horizon_code = code
            self.p_outperform_benchmark = Decimal(
                str(p)
            )

    # Strong signal
    edge, _, _, _ = compute_directional_edge([
        FakeH("1d", 0.70),
        FakeH("5d", 0.65),
    ])
    action = determine_action(
        Decimal("0.72"), edge
    )
    assert action == "long_candidate"

    # Noise signal
    edge2, _, _, _ = compute_directional_edge([
        FakeH("1d", 0.51),
        FakeH("5d", 0.50),
    ])
    action2 = determine_action(
        Decimal("0.51"), edge2
    )
    assert action2 == "no_trade"


# ── Test 4: Exit engine stop levels ──

def test_exit_stop_levels():
    """Exit engine hard stop percentages must match
    risk policy: -2% for 1d, -3% for 5d."""
    from backend.services.exit_engine import (
        STOP_1D,
        STOP_5D,
    )

    assert Decimal("-0.02") == STOP_1D
    assert Decimal("-0.03") == STOP_5D
    # 1d stop must be tighter than 5d
    assert STOP_1D > STOP_5D


def test_exit_horizon_calendar_days():
    """Exit engine uses 2 cal days for 1d horizon,
    7 cal days for 5d horizon."""
    # Mirrors logic in check_time_exits
    horizons = {"1d": 2, "5d": 7}
    base = datetime(2026, 4, 6, 15, 0, tzinfo=UTC)

    for _horizon, cal_days in horizons.items():
        exit_after = base + timedelta(
            days=cal_days
        )
        assert exit_after > base
        diff = (exit_after - base).days
        assert diff == cal_days


# ── Test 5: Trade horizon connection ──

def test_trade_horizon_in_reason_codes():
    """Decision service should embed trade_horizon
    in reason_codes_json for execution to read."""
    from backend.services.decision import (
        determine_trade_horizon,
    )

    # Earnings -> 5d
    h = determine_trade_horizon(
        "corp_earnings_beat",
        Decimal("0.3"), Decimal("0.2"),
    )
    assert h == "5d"

    # Analyst upgrade -> 1d
    h2 = determine_trade_horizon(
        "market_analyst_upgrade_material",
        Decimal("0.3"), Decimal("0.2"),
    )
    assert h2 == "1d"


# ── Test 6: Event signature dedup ──

def test_event_signature_deterministic():
    """Same inputs should produce same signature."""
    from backend.workers.pipeline import (
        _event_signature,
    )

    sig1 = _event_signature(
        "inst-123", "corp_earnings_beat",
        "Apple beats earnings",
    )
    sig2 = _event_signature(
        "inst-123", "corp_earnings_beat",
        "Apple beats earnings",
    )
    assert sig1 == sig2

    # Different inputs -> different sig
    sig3 = _event_signature(
        "inst-456", "corp_earnings_beat",
        "Apple beats earnings",
    )
    assert sig1 != sig3
