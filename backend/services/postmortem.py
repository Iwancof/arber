"""Postmortem and outcome evaluation service.

Evaluates forecast accuracy after the horizon period ends.
Creates outcome records and postmortem verdicts.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.feedback import OutcomeLedger, PostmortemLedger
from backend.models.forecasting import ForecastHorizon, ForecastLedger

JUDGE_VERSION = "v1_simple"


async def record_outcome(
    db: AsyncSession,
    *,
    forecast_id: UUID,
    horizon_code: str,
    realized_abs_return: Decimal | None = None,
    realized_rel_return: Decimal | None = None,
    benchmark_return: Decimal | None = None,
    barrier_hit: bool | None = None,
    horizon_end_at: datetime | None = None,
    outcome_json: dict[str, Any] | None = None,
) -> OutcomeLedger:
    """Record a realized outcome for a forecast horizon."""
    outcome = OutcomeLedger(
        forecast_id=forecast_id,
        horizon_code=horizon_code,
        horizon_end_at=horizon_end_at,
        realized_abs_return=realized_abs_return,
        realized_rel_return=realized_rel_return,
        benchmark_return=benchmark_return,
        barrier_hit=barrier_hit,
        outcome_json=outcome_json or {},
    )
    db.add(outcome)
    await db.commit()
    await db.refresh(outcome)
    return outcome


def judge_verdict(
    *,
    forecast_horizon: ForecastHorizon | None,
    realized_rel_return: Decimal | None,
    confidence: Decimal | None,
) -> tuple[str, list[str]]:
    """Judge a forecast's accuracy.

    Returns (verdict, failure_codes).
    verdict: correct, wrong, mixed, insufficient
    """
    if realized_rel_return is None:
        return "insufficient", ["missing_price_data"]

    if forecast_horizon is None:
        return "insufficient", ["no_horizon_data"]

    failure_codes: list[str] = []
    p_out = forecast_horizon.p_outperform_benchmark

    if p_out is None:
        return "insufficient", ["no_outperform_probability"]

    # Predicted outperform (p > 0.5) and actually outperformed
    predicted_up = p_out > Decimal("0.5")
    actually_up = realized_rel_return > Decimal("0")

    if predicted_up == actually_up:
        # Direction correct
        if confidence and confidence < Decimal("0.5"):
            return "mixed", ["low_confidence_correct"]
        return "correct", []

    # Direction wrong
    failure_codes.append("direction_error")

    # Check magnitude of error
    if abs(realized_rel_return) > Decimal("0.05"):
        failure_codes.append("large_magnitude_error")

    return "wrong", failure_codes


async def create_postmortem(
    db: AsyncSession,
    *,
    forecast_id: UUID,
    outcome_id: UUID | None = None,
    horizon_code: str = "1d",
) -> PostmortemLedger:
    """Create a postmortem verdict for a forecast.

    Loads the forecast, outcome, and horizon data, then judges.
    """
    # Load forecast
    f_result = await db.execute(
        select(ForecastLedger).where(
            ForecastLedger.forecast_id == forecast_id
        )
    )
    forecast = f_result.scalar_one()

    # Load horizon
    h_result = await db.execute(
        select(ForecastHorizon).where(
            ForecastHorizon.forecast_id == forecast_id,
            ForecastHorizon.horizon_code == horizon_code,
        )
    )
    horizon = h_result.scalar_one_or_none()

    # Load outcome
    realized_rel: Decimal | None = None
    if outcome_id:
        o_result = await db.execute(
            select(OutcomeLedger).where(
                OutcomeLedger.outcome_id == outcome_id
            )
        )
        outcome = o_result.scalar_one()
        realized_rel = outcome.realized_rel_return

    # Judge
    verdict, failure_codes = judge_verdict(
        forecast_horizon=horizon,
        realized_rel_return=realized_rel,
        confidence=forecast.confidence,
    )

    # Determine review flags
    requires_source = "source_gap" in failure_codes
    requires_prompt = "direction_error" in failure_codes

    postmortem = PostmortemLedger(
        forecast_id=forecast_id,
        outcome_id=outcome_id,
        verdict=verdict,
        failure_codes_json=failure_codes,
        requires_source_review=requires_source,
        requires_prompt_review=requires_prompt,
        judge_version=JUDGE_VERSION,
        postmortem_json={
            "horizon_code": horizon_code,
            "p_outperform": str(horizon.p_outperform_benchmark)
            if horizon and horizon.p_outperform_benchmark
            else None,
            "realized_rel_return": str(realized_rel)
            if realized_rel
            else None,
            "confidence": str(forecast.confidence)
            if forecast.confidence
            else None,
        },
    )
    db.add(postmortem)
    await db.commit()
    await db.refresh(postmortem)
    return postmortem
