"""Inquiry Signal Evaluator.

Automatically generates inquiry cases and tasks when
certain conditions are detected in events/decisions.

Signal types (v1):
- high_materiality_low_confidence
- novel_event_type
- macro_single_name_conflict
- postmortem_needs_human_label
"""

import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.content import EventLedger
from backend.models.forecasting import (
    DecisionLedger,
    ForecastLedger,
)
from backend.models.inquiry import (
    InquiryCase,
    InquirySignal,
)
from backend.services.inquiry import (
    create_inquiry_case,
    spawn_inquiry_task,
)

logger = logging.getLogger("eos.inquiry_signal")

# Official v2 taxonomy prefixes
VALID_PREFIXES = (
    "corp_", "reg_", "macro_", "market_",
)


async def evaluate_decision_signals(
    db: AsyncSession,
    *,
    decision_id: UUID,
) -> list[InquirySignal]:
    """Evaluate a decision for inquiry signals.

    Called after each decision is created.
    Returns list of signals detected.
    """
    signals: list[InquirySignal] = []

    # Load decision + forecast + event
    d_result = await db.execute(
        select(DecisionLedger).where(
            DecisionLedger.decision_id == decision_id
        )
    )
    decision = d_result.scalar_one_or_none()
    if not decision:
        return signals

    f_result = await db.execute(
        select(ForecastLedger).where(
            ForecastLedger.forecast_id
            == decision.forecast_id
        )
    )
    forecast = f_result.scalar_one_or_none()
    if not forecast:
        return signals

    event = None
    if forecast.event_id:
        e_result = await db.execute(
            select(EventLedger).where(
                EventLedger.event_id == forecast.event_id
            )
        )
        event = e_result.scalar_one_or_none()

    fj = forecast.forecast_json or {}
    conf = fj.get("confidence_after")
    conf_dec = (
        Decimal(str(conf))
        if conf is not None
        else Decimal("0.5")
    )

    # Signal 1: high materiality + low confidence
    if event and event.materiality:
        mat = event.materiality
        if mat > Decimal("0.65") and conf_dec < Decimal("0.58"):
            sig = await _create_signal(
                db,
                signal_type="high_materiality_low_confidence",
                score=float(mat * (1 - conf_dec)),
                source_ref_type="decision",
                source_ref_id=decision_id,
                explanation={
                    "materiality": str(mat),
                    "confidence": str(conf_dec),
                },
            )
            signals.append(sig)

            # Auto-create inquiry case
            await _auto_create_inquiry(
                db,
                signal=sig,
                event=event,
                forecast=forecast,
                inquiry_kind="pretrade_decision",
                title=(
                    f"{event.event_type} for "
                    f"{fj.get('symbol', '?')}: "
                    f"high materiality, low confidence"
                ),
                question=(
                    f"Event {event.event_type} has "
                    f"materiality {mat} but confidence "
                    f"is only {conf_dec}. Should we "
                    f"act on this signal?"
                ),
            )

    # Signal 2: novel event type
    if event:
        et = event.event_type or ""
        is_novel = not any(
            et.startswith(p) for p in VALID_PREFIXES
        )
        if is_novel and et:
            sig = await _create_signal(
                db,
                signal_type="novel_event_type",
                score=0.7,
                source_ref_type="event",
                source_ref_id=event.event_id,
                explanation={
                    "event_type": et,
                    "reason": "Not in official taxonomy",
                },
            )
            signals.append(sig)

            await _auto_create_inquiry(
                db,
                signal=sig,
                event=event,
                forecast=forecast,
                inquiry_kind="novel_event_interpretation",
                title=f"Novel event type: {et}",
                question=(
                    f"Event type '{et}' is not in the "
                    f"official taxonomy. How should "
                    f"this be classified and interpreted?"
                ),
            )

    # Signal 3: wait_manual decision
    if decision.action == "wait_manual":
        sig = await _create_signal(
            db,
            signal_type="policy_blocked_need_context",
            score=float(abs(decision.score)),
            source_ref_type="decision",
            source_ref_id=decision_id,
            explanation={
                "action": decision.action,
                "score": str(decision.score),
            },
        )
        signals.append(sig)

        symbol = fj.get("symbol", "?")
        await _auto_create_inquiry(
            db,
            signal=sig,
            event=event,
            forecast=forecast,
            inquiry_kind="pretrade_decision",
            title=(
                f"{symbol}: manual review needed "
                f"(score={decision.score})"
            ),
            question=(
                f"Decision for {symbol} requires "
                f"manual review. Score is "
                f"{decision.score}, edge is moderate. "
                f"Should we proceed with a trade?"
            ),
        )

    return signals


async def _create_signal(
    db: AsyncSession,
    *,
    signal_type: str,
    score: float,
    source_ref_type: str | None = None,
    source_ref_id: UUID | None = None,
    explanation: dict[str, Any] | None = None,
) -> InquirySignal:
    """Create an inquiry signal record."""
    sig = InquirySignal(
        signal_type=signal_type,
        signal_score=Decimal(str(score)),
        source_ref_type=source_ref_type,
        source_ref_id=source_ref_id,
        explanation_json=explanation or {},
    )
    db.add(sig)
    await db.flush()
    return sig


async def _auto_create_inquiry(
    db: AsyncSession,
    *,
    signal: InquirySignal,
    event: EventLedger | None,
    forecast: ForecastLedger,
    inquiry_kind: str,
    title: str,
    question: str,
) -> None:
    """Auto-create inquiry case + task from signal."""
    # Check for existing active case (dedup)
    et = event.event_type if event else "unknown"
    dedupe_key = f"{et}:{forecast.instrument_id}"

    existing = await db.execute(
        select(func.count()).select_from(
            InquiryCase
        ).where(
            InquiryCase.dedupe_key == dedupe_key,
            InquiryCase.case_status == "open",
        )
    )
    if existing.scalar_one() > 0:
        return  # Already exists

    fj = forecast.forecast_json or {}
    symbol = fj.get("symbol", "?")

    case = await create_inquiry_case(
        db,
        market_profile_code="US_EQUITY",
        linked_entity_type="decision",
        linked_entity_id=None,
        inquiry_kind=inquiry_kind,
        dedupe_key=dedupe_key,
        title=title,
        primary_symbol=symbol,
        urgency_class="high"
        if signal.signal_score > Decimal("0.5")
        else "normal",
    )

    # Link signal to case
    signal.inquiry_case_id = case.inquiry_case_id

    # Create task
    deadline = datetime.now(UTC) + timedelta(hours=4)
    await spawn_inquiry_task(
        db,
        case_id=case.inquiry_case_id,
        question_title=title,
        question_text=question,
        deadline_at=deadline,
        sla_class="fast"
        if signal.signal_score > Decimal("0.5")
        else "normal",
    )

    logger.info(
        "Auto-inquiry: %s → %s",
        signal.signal_type,
        title[:50],
    )
