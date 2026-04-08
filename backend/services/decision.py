"""Decision and policy evaluation service.

v2 policy: confidence is a quality gate, score is directional edge.
These are NOT mixed. confidence determines whether to trade,
directional_edge determines direction and magnitude.
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

DEFAULT_POLICY_VERSION = "v2_edge_gate"

# Paper account NAV for sizing
PAPER_NAV = Decimal("100000")

# Max simultaneous positions
MAX_POSITIONS = 5
MAX_GROSS_EXPOSURE_PCT = Decimal("0.20")


# ── Directional Edge ────────────────────────────


def compute_directional_edge(
    horizons: list[ForecastHorizon],
) -> tuple[Decimal, Decimal, Decimal, list[dict[str, Any]]]:
    """Compute directional edge from horizon data.

    Returns (directional_edge, edge_1d, edge_5d, reasons).
    directional_edge > 0 = long, < 0 = short.
    """
    reasons: list[dict[str, Any]] = []

    if not horizons:
        return Decimal("0"), Decimal("0"), Decimal("0"), [
            {
                "source": "policy",
                "code": "no_horizons",
                "contribution": Decimal("0"),
                "message": "No horizon data",
            }
        ]

    edge_1d = Decimal("0")
    edge_5d = Decimal("0")

    for h in horizons:
        p = h.p_outperform_benchmark or Decimal("0.5")
        edge = 2 * (p - Decimal("0.5"))

        if h.horizon_code == "1d":
            edge_1d = edge
            reasons.append({
                "source": "agent",
                "code": "edge_1d",
                "contribution": edge,
                "message": f"1d: p_out={p} edge={edge}",
            })
        elif h.horizon_code == "5d":
            edge_5d = edge
            reasons.append({
                "source": "agent",
                "code": "edge_5d",
                "contribution": edge,
                "message": f"5d: p_out={p} edge={edge}",
            })

    directional = (
        Decimal("0.55") * edge_1d
        + Decimal("0.45") * edge_5d
    )

    reasons.append({
        "source": "policy",
        "code": "directional_edge",
        "contribution": directional,
        "message": (
            f"0.55*{edge_1d} + 0.45*{edge_5d} "
            f"= {directional}"
        ),
    })

    return directional, edge_1d, edge_5d, reasons


# ── Confidence Gate + Action Matrix ──────────────


def determine_confidence_band(
    confidence: Decimal,
) -> str:
    """Map confidence to a named band."""
    if confidence < Decimal("0.55"):
        return "noise"
    if confidence < Decimal("0.62"):
        return "weak"
    if confidence < Decimal("0.72"):
        return "clear"
    if confidence < Decimal("0.80"):
        return "strong"
    return "very_strong"


def determine_action(
    confidence: Decimal,
    directional_edge: Decimal,
) -> str:
    """Determine action using confidence gate + edge matrix.

    confidence is a quality gate (not mixed into score).
    directional_edge determines direction and strength.
    """
    abs_edge = abs(directional_edge)
    band = determine_confidence_band(confidence)

    if band == "noise":
        return "no_trade"

    if band == "weak":
        if abs_edge >= Decimal("0.35"):
            return "wait_manual"
        return "no_trade"

    if band == "clear":
        if abs_edge >= Decimal("0.30"):
            return (
                "long_candidate"
                if directional_edge > 0
                else "short_candidate"
            )
        if abs_edge >= Decimal("0.20"):
            return "wait_manual"
        return "no_trade"

    if band == "strong":
        if abs_edge >= Decimal("0.25"):
            return (
                "long_candidate"
                if directional_edge > 0
                else "short_candidate"
            )
        if abs_edge >= Decimal("0.15"):
            return "wait_manual"
        return "no_trade"

    # very_strong
    if abs_edge >= Decimal("0.20"):
        return (
            "long_candidate"
            if directional_edge > 0
            else "short_candidate"
        )
    if abs_edge >= Decimal("0.12"):
        return "wait_manual"
    return "no_trade"


# ── Position Sizing ──────────────────────────────


def compute_size_cap(
    confidence: Decimal,
    abs_edge: Decimal,
    action: str,
) -> Decimal | None:
    """Compute position size cap in USD (notional).

    Tier 1: conf 0.62-0.72, edge>=0.30 → 2% NAV
    Tier 2: conf 0.72-0.80, edge>=0.25 → 3.5% NAV
    Tier 3: conf >= 0.80, edge>=0.20 → 5% NAV
    Manual-approved: 1.5% NAV
    """
    if action == "wait_manual":
        return PAPER_NAV * Decimal("0.015")

    if action not in ("long_candidate", "short_candidate"):
        return None

    band = determine_confidence_band(confidence)

    if band == "very_strong":
        return PAPER_NAV * Decimal("0.05")
    if band == "strong":
        return PAPER_NAV * Decimal("0.035")
    if band == "clear":
        return PAPER_NAV * Decimal("0.02")

    return PAPER_NAV * Decimal("0.015")


# ── Trade Horizon ────────────────────────────────


def determine_trade_horizon(
    event_type: str,
    edge_1d: Decimal,
    edge_5d: Decimal,
) -> str:
    """Determine trade horizon based on event type."""
    event_1d = {
        "market_analyst_upgrade_material",
        "market_analyst_downgrade_material",
        "market_index_inclusion",
        "market_index_exclusion",
        "market_short_report",
        "market_activist_stake",
    }
    event_5d = {
        "corp_earnings_beat", "corp_earnings_miss",
        "corp_guidance_raise", "corp_guidance_cut",
        "corp_mna_target", "corp_mna_acquirer",
        "reg_fda_approval", "reg_fda_delay_or_rejection",
        "corp_contract_win_major",
        "corp_contract_loss_major",
        "corp_product_launch_major",
    }

    if event_type in event_1d:
        return "1d"
    if event_type in event_5d:
        return "5d"

    # Fallback: use edge difference
    if abs(edge_1d) >= abs(edge_5d) + Decimal("0.10"):
        return "1d"
    return "5d"


# ── Priority Score ───────────────────────────────


def compute_priority(
    confidence: Decimal,
    abs_edge: Decimal,
) -> Decimal:
    """Priority for position selection when at capacity."""
    return abs_edge * max(
        confidence - Decimal("0.50"), Decimal("0")
    )


# ── Status ───────────────────────────────────────


def determine_initial_status(
    action: str, execution_mode: str
) -> str:
    """Determine the initial decision status."""
    if action == "wait_manual":
        return "waiting_manual"
    if action == "no_trade":
        return "suppressed"
    if execution_mode in ("replay", "shadow"):
        return "approved"
    return "candidate"


# ── Main Evaluation ──────────────────────────────


async def evaluate_forecast(
    db: AsyncSession,
    *,
    forecast_id: UUID,
    execution_mode: str = "replay",
) -> DecisionLedger:
    """Evaluate a forecast and create a decision.

    v2: confidence is a gate, score is directional edge.
    """
    forecast_result = await db.execute(
        select(ForecastLedger).where(
            ForecastLedger.forecast_id == forecast_id
        )
    )
    forecast = forecast_result.scalar_one()

    # Kill switch check
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
        db.add(DecisionReason(
            decision_id=decision.decision_id,
            source_of_reason="policy",
            reason_code="kill_switch_active",
            score_contribution=Decimal("0"),
            message="Decision halted by kill switch",
        ))
        await emit_event(
            db,
            event_type="created",
            aggregate_type="decision",
            aggregate_id=str(decision.decision_id),
            payload={"action": "no_trade"},
        )
        await db.commit()
        await db.refresh(decision)
        return decision

    # Load horizons
    horizon_result = await db.execute(
        select(ForecastHorizon).where(
            ForecastHorizon.forecast_id == forecast_id
        )
    )
    horizons = list(horizon_result.scalars().all())

    # Get confidence from forecast_json
    fj = forecast.forecast_json or {}
    conf_raw = fj.get("confidence_after")
    confidence = (
        Decimal(str(conf_raw))
        if conf_raw is not None
        else Decimal("0.50")
    )

    # Compute directional edge (NOT mixed with confidence)
    d_edge, edge_1d, edge_5d, reasons = (
        compute_directional_edge(horizons)
    )
    abs_edge = abs(d_edge)

    # Confidence gate + action matrix
    action = determine_action(confidence, d_edge)

    band = determine_confidence_band(confidence)
    reasons.append({
        "source": "policy",
        "code": f"confidence_band_{band}",
        "contribution": Decimal("0"),
        "message": f"confidence={confidence} band={band}",
    })

    # Size cap (notional USD)
    size_cap = compute_size_cap(confidence, abs_edge, action)

    # Trade horizon
    event_type = ""
    if forecast.event_id:
        from backend.models.content import EventLedger
        ev_result = await db.execute(
            select(EventLedger.event_type).where(
                EventLedger.event_id == forecast.event_id
            )
        )
        event_type = ev_result.scalar_one_or_none() or ""

    trade_horizon = determine_trade_horizon(
        event_type, edge_1d, edge_5d
    )

    # Priority
    priority = compute_priority(confidence, abs_edge)

    # Status
    status = determine_initial_status(
        action, execution_mode
    )

    # Create decision
    # score = directional_edge (NOT mixed with confidence)
    decision = DecisionLedger(
        forecast_id=forecast_id,
        market_profile_id=forecast.market_profile_id,
        execution_mode=execution_mode,
        score=d_edge,
        action=action,
        decision_status=status,
        policy_version=DEFAULT_POLICY_VERSION,
        size_cap=size_cap,
        reason_codes_json=(
            [r["code"] for r in reasons]
            + [f"trade_horizon_{trade_horizon}"]
        ),
    )
    db.add(decision)
    await db.flush()

    # Decision reasons
    for r in reasons:
        db.add(DecisionReason(
            decision_id=decision.decision_id,
            source_of_reason=r["source"],
            reason_code=r["code"],
            score_contribution=r["contribution"],
            message=r.get("message"),
        ))

    await emit_event(
        db,
        event_type="created",
        aggregate_type="decision",
        aggregate_id=str(decision.decision_id),
        payload={
            "action": action,
            "score": str(d_edge),
            "confidence_band": band,
            "directional_edge": str(d_edge),
            "trade_horizon": trade_horizon,
            "size_cap": str(size_cap) if size_cap else None,
            "priority": str(priority),
        },
    )

    await db.commit()
    await db.refresh(decision)
    return decision
