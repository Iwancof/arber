"""Overlay API for Grafana panel plugin.

Provides forecast bands, event annotations, and decision intervals
for chart visualization.
"""

from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.content import EventLedger
from backend.models.forecasting import (
    DecisionLedger,
    ForecastHorizon,
    ForecastLedger,
)
from backend.schemas.forecasting import (
    DecisionInterval,
    ForecastBand,
    OverlayAnnotation,
    OverlayPayload,
)

router = APIRouter(tags=["overlays"])


@router.get("/overlays/{instrument_id}", response_model=OverlayPayload)
async def get_overlay(
    instrument_id: UUID,
    from_time: datetime = Query(alias="from"),
    to_time: datetime = Query(alias="to"),
    horizon: str = Query(default="1d"),
    db: AsyncSession = Depends(get_db),
) -> OverlayPayload:
    """Get overlay data for the Grafana forecast band panel."""
    # Forecast bands
    forecast_result = await db.execute(
        select(ForecastLedger)
        .where(
            ForecastLedger.instrument_id == instrument_id,
            ForecastLedger.forecasted_at >= from_time,
            ForecastLedger.forecasted_at <= to_time,
        )
        .order_by(ForecastLedger.forecasted_at)
    )
    forecasts = forecast_result.scalars().all()

    bands: list[ForecastBand] = []
    for f in forecasts:
        h_result = await db.execute(
            select(ForecastHorizon).where(
                ForecastHorizon.forecast_id == f.forecast_id,
                ForecastHorizon.horizon_code == horizon,
            )
        )
        h = h_result.scalar_one_or_none()
        if h:
            bands.append(
                ForecastBand(
                    time=f.forecasted_at,
                    horizon_code=horizon,
                    ret_q10=h.ret_q10,
                    ret_q50=h.ret_q50,
                    ret_q90=h.ret_q90,
                    confidence=f.confidence,
                )
            )

    # Event annotations
    event_result = await db.execute(
        select(EventLedger)
        .where(
            EventLedger.issuer_instrument_id == instrument_id,
            EventLedger.created_at >= from_time,
            EventLedger.created_at <= to_time,
        )
        .order_by(EventLedger.created_at)
    )
    annotations: list[OverlayAnnotation] = []
    for e in event_result.scalars().all():
        annotations.append(
            OverlayAnnotation(
                time=e.event_time or e.created_at,
                title=e.event_type,
                text=f"materiality={e.materiality} direction={e.direction_hint}",
                tags=[e.event_type, e.verification_status],
            )
        )

    # Decision intervals
    decision_result = await db.execute(
        select(DecisionLedger)
        .join(ForecastLedger, ForecastLedger.forecast_id == DecisionLedger.forecast_id)
        .where(
            ForecastLedger.instrument_id == instrument_id,
            DecisionLedger.decided_at >= from_time,
            DecisionLedger.decided_at <= to_time,
        )
        .order_by(DecisionLedger.decided_at)
    )
    intervals: list[DecisionInterval] = []
    for d in decision_result.scalars().all():
        intervals.append(
            DecisionInterval(
                start=d.decided_at,
                end=None,
                action=d.action,
                score=d.score,
                decision_id=d.decision_id,
            )
        )

    return OverlayPayload(
        instrument_id=instrument_id,
        from_time=from_time,
        to_time=to_time,
        forecast_bands=bands,
        annotations=annotations,
        decision_intervals=intervals,
    )
