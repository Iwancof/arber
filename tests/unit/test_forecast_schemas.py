"""Tests for forecast and decision Pydantic schemas."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from backend.schemas.forecasting import (
    DecisionInterval,
    DecisionLedgerRead,
    DossierRead,
    ForecastBand,
    ForecastHorizonRead,
    ForecastLedgerRead,
    OverlayAnnotation,
    OverlayPayload,
    ReasoningTraceRead,
)


def test_forecast_ledger_read():
    """ForecastLedgerRead should parse correctly."""
    now = datetime.now(tz=UTC)
    f = ForecastLedgerRead(
        forecast_id=uuid4(),
        instrument_id=uuid4(),
        market_profile_id=uuid4(),
        model_family="mock",
        model_version="1.0",
        worker_id="mock_v1",
        prompt_template_id="default",
        prompt_version="1.0",
        forecast_mode="replay",
        forecasted_at=now,
        no_trade_reason_codes_json=[],
        forecast_json={"test": True},
    )
    assert f.forecast_mode == "replay"
    assert f.horizons == []


def test_forecast_horizon_read():
    """ForecastHorizonRead should handle decimal values."""
    h = ForecastHorizonRead(
        forecast_horizon_id=uuid4(),
        forecast_id=uuid4(),
        horizon_code="1d",
        p_outperform_benchmark=Decimal("0.65"),
        ret_q50=Decimal("0.012"),
    )
    assert h.horizon_code == "1d"
    assert h.p_outperform_benchmark == Decimal("0.65")


def test_decision_ledger_read():
    """DecisionLedgerRead should include reasons."""
    d = DecisionLedgerRead(
        decision_id=uuid4(),
        forecast_id=uuid4(),
        market_profile_id=uuid4(),
        execution_mode="replay",
        score=Decimal("0.72"),
        action="long_candidate",
        decision_status="approved",
        policy_version="v1",
        reason_codes_json=["confidence_signal"],
        decided_at=datetime.now(tz=UTC),
    )
    assert d.reasons == []
    assert d.action == "long_candidate"


def test_dossier_read_minimal():
    """DossierRead should work with minimal data."""
    d = DossierRead(
        decision=DecisionLedgerRead(
            decision_id=uuid4(),
            forecast_id=uuid4(),
            market_profile_id=uuid4(),
            execution_mode="replay",
            score=Decimal("0.5"),
            action="no_trade",
            decision_status="suppressed",
            policy_version="v1",
            reason_codes_json=[],
            decided_at=datetime.now(tz=UTC),
        ),
    )
    assert d.forecast is None
    assert d.event is None
    assert d.orders == []


def test_overlay_payload():
    """OverlayPayload should assemble all components."""
    now = datetime.now(tz=UTC)
    payload = OverlayPayload(
        instrument_id=uuid4(),
        from_time=now,
        to_time=now,
        forecast_bands=[
            ForecastBand(
                time=now, horizon_code="1d",
                ret_q10=Decimal("-0.02"), ret_q50=Decimal("0.01"), ret_q90=Decimal("0.04"),
            ),
        ],
        annotations=[
            OverlayAnnotation(time=now, title="earnings_beat", tags=["corporate"]),
        ],
        decision_intervals=[
            DecisionInterval(
                start=now, action="long_candidate",
                score=Decimal("0.7"), decision_id=uuid4(),
            ),
        ],
    )
    assert len(payload.forecast_bands) == 1
    assert len(payload.annotations) == 1
    assert len(payload.decision_intervals) == 1


def test_reasoning_trace_read():
    """ReasoningTraceRead should handle trace JSON."""
    t = ReasoningTraceRead(
        reasoning_trace_id=uuid4(),
        trace_version="1.0",
        trace_json={
            "hypotheses": [{"code": "h1", "weight": 0.7}],
            "selected_hypothesis": "h1",
        },
        created_at=datetime.now(tz=UTC),
    )
    assert t.trace_json["selected_hypothesis"] == "h1"
