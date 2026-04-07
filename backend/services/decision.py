"""Decision and policy evaluation service.

Evaluates forecasts against policy rules to produce decisions.
Follows the design principle that LLMs propose/score but
deterministic policy and broker layers decide execution.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.core.kill_switch import check_decision_allowed
from backend.core.outbox import emit_event
from backend.models.forecasting import (
    DecisionLedger,
    DecisionReason,
    ForecastHorizon,
    ForecastLedger,
)

# --- Policy configuration (v1: hardcoded, future: policy_pack_registry) ---

DEFAULT_POLICY_VERSION = "v1_simple"

# Minimum confidence to consider a trade
MIN_CONFIDENCE_THRESHOLD = Decimal("0.45")

# Score thresholds for actions
SCORE_LONG_THRESHOLD = Decimal("0.60")
SCORE_SHORT_THRESHOLD = Decimal("-0.60")
SCORE_MANUAL_THRESHOLD = Decimal("0.40")

# Maximum position size cap (as fraction of portfolio)
DEFAULT_SIZE_CAP = Decimal("0.02")


def compute_decision_score(
    forecast: ForecastLedger,
    horizons: list[ForecastHorizon],
) -> tuple[Decimal, list[dict[str, Any]]]:
    """Compute a decision score from forecast data.

    Returns (score, reasons) where score is in [-1, 1] range.
    Positive = bullish signal, negative = bearish.
    """
    reasons: list[dict[str, Any]] = []

    if not horizons:
        return Decimal("0"), [
            {"source": "policy", "code": "no_horizons", "contribution": Decimal("0"),
             "message": "No forecast horizons available"}
        ]

    # Base score from confidence
    confidence = forecast.confidence or Decimal("0.5")
    base_score = (confidence - Decimal("0.5")) * 2  # Map [0,1] to [-1,1]

    reasons.append({
        "source": "agent",
        "code": "confidence_signal",
        "contribution": base_score,
        "message": f"Confidence {confidence} mapped to base score {base_score}",
    })

    # Horizon-weighted adjustment
    horizon_score = Decimal("0")
    horizon_weights = {"1d": Decimal("0.5"), "5d": Decimal("0.3"), "20d": Decimal("0.2"),
                       "1w": Decimal("0.3"), "1m": Decimal("0.2")}

    for h in horizons:
        weight = horizon_weights.get(h.horizon_code, Decimal("0.1"))
        p_out = h.p_outperform_benchmark or Decimal("0.5")
        # Signal: how far from 50/50
        signal = (p_out - Decimal("0.5")) * 2 * weight
        horizon_score += signal

        reasons.append({
            "source": "agent",
            "code": f"horizon_{h.horizon_code}",
            "contribution": signal,
            "message": f"{h.horizon_code}: p_outperform={p_out}, weighted signal={signal}",
        })

    combined = (base_score + horizon_score) / 2
    # Clamp to [-1, 1]
    combined = max(Decimal("-1"), min(Decimal("1"), combined))

    return combined, reasons


def determine_action(
    score: Decimal,
    confidence: Decimal | None,
    execution_mode: str,
) -> str:
    """Determine the action based on score and policy rules.

    Returns one of: long_candidate, short_candidate, no_trade, wait_manual
    """
    conf = confidence or Decimal("0.5")

    # Low confidence → no trade or manual review
    if conf < MIN_CONFIDENCE_THRESHOLD:
        if abs(score) > float(SCORE_MANUAL_THRESHOLD):
            return "wait_manual"
        return "no_trade"

    # Score-based action
    if score >= SCORE_LONG_THRESHOLD:
        return "long_candidate"
    elif score <= SCORE_SHORT_THRESHOLD:
        return "short_candidate"
    elif abs(score) >= SCORE_MANUAL_THRESHOLD:
        return "wait_manual"
    else:
        return "no_trade"


def determine_initial_status(action: str, execution_mode: str) -> str:
    """Determine the initial decision status."""
    if action == "wait_manual":
        return "waiting_manual"
    if action == "no_trade":
        return "suppressed"
    if execution_mode in ("replay", "shadow"):
        return "approved"  # Auto-approve in non-live modes
    return "candidate"


async def evaluate_forecast(
    db: AsyncSession,
    *,
    forecast_id: UUID,
    execution_mode: str = "replay",
) -> DecisionLedger:
    """Evaluate a forecast and create a decision.

    This is the deterministic policy evaluation step.
    LLMs propose (forecast), policy decides (decision).
    """
    # Load forecast + horizons
    forecast_result = await db.execute(
        select(ForecastLedger).where(ForecastLedger.forecast_id == forecast_id)
    )
    forecast = forecast_result.scalar_one()

    # Kill switch: force no_trade when decision engine is halted
    decisions_ok = await check_decision_allowed(db)
    if not decisions_ok:
        decision = DecisionLedger(
            forecast_id=forecast_id,
            market_profile_id=forecast.market_profile_id,
            execution_mode=execution_mode,
            score=Decimal("0"),
            action="no_trade",
            decision_status="suppressed",
            policy_version=DEFAULT_POLICY_VERSION,
            reason_codes_json=["kill_switch_active"],
        )
        db.add(decision)
        await db.flush()
        reason = DecisionReason(
            decision_id=decision.decision_id,
            source_of_reason="policy",
            reason_code="kill_switch_active",
            score_contribution=Decimal("0"),
            message="Decision halted by kill switch",
        )
        db.add(reason)
        await emit_event(
            db,
            event_type="created",
            aggregate_type="decision",
            aggregate_id=str(decision.decision_id),
            payload={"action": "no_trade", "reason": "kill_switch"},
        )
        await db.commit()
        await db.refresh(decision)
        return decision

    horizon_result = await db.execute(
        select(ForecastHorizon).where(ForecastHorizon.forecast_id == forecast_id)
    )
    horizons = list(horizon_result.scalars().all())

    # Compute score
    score, reasons = compute_decision_score(forecast, horizons)

    # Determine action
    action = determine_action(score, forecast.confidence, execution_mode)

    # Determine initial status
    status = determine_initial_status(action, execution_mode)

    # Size cap
    size_cap = DEFAULT_SIZE_CAP if action in ("long_candidate", "short_candidate") else None

    # Create decision
    decision = DecisionLedger(
        forecast_id=forecast_id,
        market_profile_id=forecast.market_profile_id,
        execution_mode=execution_mode,
        score=score,
        action=action,
        decision_status=status,
        policy_version=DEFAULT_POLICY_VERSION,
        size_cap=size_cap,
        reason_codes_json=[r["code"] for r in reasons],
    )
    db.add(decision)
    await db.flush()

    # Create decision reasons
    for r in reasons:
        reason = DecisionReason(
            decision_id=decision.decision_id,
            source_of_reason=r["source"],
            reason_code=r["code"],
            score_contribution=r["contribution"],
            message=r.get("message"),
        )
        db.add(reason)

    # Emit outbox event within the same transaction
    await emit_event(
        db,
        event_type="created",
        aggregate_type="decision",
        aggregate_id=str(decision.decision_id),
        payload={
            "action": action,
            "score": str(score),
            "forecast_id": str(forecast_id),
        },
    )

    await db.commit()
    await db.refresh(decision)
    return decision
