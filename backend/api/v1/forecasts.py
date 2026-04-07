"""Forecasts and decisions API endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.session import get_db
from backend.models.forecasting import (
    DecisionLedger,
    DecisionReason,
    ForecastHorizon,
    ForecastLedger,
)
from backend.schemas.forecasting import (
    DecisionLedgerRead,
    DecisionList,
    DecisionReasonRead,
    ForecastHorizonRead,
    ForecastLedgerRead,
    ForecastList,
)

router = APIRouter(tags=["forecasts"])


async def _build_forecast_read(
    db: AsyncSession, f: ForecastLedger
) -> ForecastLedgerRead:
    """Build ForecastLedgerRead avoiding lazy load."""
    h_result = await db.execute(
        select(ForecastHorizon).where(
            ForecastHorizon.forecast_id == f.forecast_id
        )
    )
    horizons = [
        ForecastHorizonRead.model_validate(h)
        for h in h_result.scalars().all()
    ]
    # Build without touching ORM relationships
    fr = ForecastLedgerRead(
        forecast_id=f.forecast_id,
        event_id=f.event_id,
        instrument_id=f.instrument_id,
        benchmark_instrument_id=f.benchmark_instrument_id,
        market_profile_id=f.market_profile_id,
        reasoning_trace_id=f.reasoning_trace_id,
        model_family=f.model_family,
        model_version=f.model_version,
        worker_id=f.worker_id,
        prompt_template_id=f.prompt_template_id,
        prompt_version=f.prompt_version,
        forecast_mode=f.forecast_mode,
        forecasted_at=f.forecasted_at,
        confidence=f.confidence,
        no_trade_reason_codes_json=f.no_trade_reason_codes_json,
        forecast_json=f.forecast_json,
        horizons=horizons,
    )
    return fr


async def _build_decision_read(
    db: AsyncSession, d: DecisionLedger
) -> DecisionLedgerRead:
    """Build DecisionLedgerRead avoiding lazy load."""
    r_result = await db.execute(
        select(DecisionReason).where(
            DecisionReason.decision_id == d.decision_id
        )
    )
    reasons = [
        DecisionReasonRead.model_validate(r)
        for r in r_result.scalars().all()
    ]
    return DecisionLedgerRead(
        decision_id=d.decision_id,
        forecast_id=d.forecast_id,
        market_profile_id=d.market_profile_id,
        execution_mode=d.execution_mode,
        score=d.score,
        action=d.action,
        decision_status=d.decision_status,
        policy_version=d.policy_version,
        size_cap=d.size_cap,
        reason_codes_json=d.reason_codes_json,
        decided_at=d.decided_at,
        reasons=reasons,
    )


@router.get("/forecasts", response_model=ForecastList)
async def list_forecasts(
    instrument_id: UUID | None = Query(default=None),
    market_profile_id: UUID | None = Query(default=None),
    forecast_mode: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> ForecastList:
    stmt = select(ForecastLedger)
    count_stmt = select(func.count()).select_from(ForecastLedger)
    if instrument_id:
        stmt = stmt.where(ForecastLedger.instrument_id == instrument_id)
        count_stmt = count_stmt.where(ForecastLedger.instrument_id == instrument_id)
    if market_profile_id:
        stmt = stmt.where(ForecastLedger.market_profile_id == market_profile_id)
        count_stmt = count_stmt.where(
            ForecastLedger.market_profile_id == market_profile_id
        )
    if forecast_mode:
        stmt = stmt.where(ForecastLedger.forecast_mode == forecast_mode)
        count_stmt = count_stmt.where(ForecastLedger.forecast_mode == forecast_mode)

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset).limit(limit).order_by(ForecastLedger.forecasted_at.desc())
    )
    forecasts = result.scalars().all()

    items = []
    for f in forecasts:
        items.append(await _build_forecast_read(db, f))

    return ForecastList(
        items=items, total=total, limit=limit, offset=offset
    )


@router.get(
    "/forecasts/{forecast_id}",
    response_model=ForecastLedgerRead,
)
async def get_forecast(
    forecast_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> ForecastLedgerRead:
    result = await db.execute(
        select(ForecastLedger).where(
            ForecastLedger.forecast_id == forecast_id
        )
    )
    forecast = result.scalar_one_or_none()
    if forecast is None:
        raise HTTPException(
            status_code=404, detail="Forecast not found"
        )
    return await _build_forecast_read(db, forecast)


@router.get("/decisions", response_model=DecisionList)
async def list_decisions(
    market_profile_id: UUID | None = Query(default=None),
    execution_mode: str | None = Query(default=None),
    action: str | None = Query(default=None),
    decision_status: str | None = Query(default=None),
    limit: int = Query(default=50, le=200),
    offset: int = Query(default=0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> DecisionList:
    stmt = select(DecisionLedger)
    count_stmt = select(func.count()).select_from(DecisionLedger)
    if market_profile_id:
        stmt = stmt.where(DecisionLedger.market_profile_id == market_profile_id)
        count_stmt = count_stmt.where(
            DecisionLedger.market_profile_id == market_profile_id
        )
    if execution_mode:
        stmt = stmt.where(DecisionLedger.execution_mode == execution_mode)
        count_stmt = count_stmt.where(
            DecisionLedger.execution_mode == execution_mode
        )
    if action:
        stmt = stmt.where(DecisionLedger.action == action)
        count_stmt = count_stmt.where(DecisionLedger.action == action)
    if decision_status:
        stmt = stmt.where(DecisionLedger.decision_status == decision_status)
        count_stmt = count_stmt.where(
            DecisionLedger.decision_status == decision_status
        )

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.offset(offset).limit(limit).order_by(DecisionLedger.decided_at.desc())
    )
    decisions = result.scalars().all()

    items = []
    for d in decisions:
        items.append(await _build_decision_read(db, d))

    return DecisionList(items=items, total=total, limit=limit, offset=offset)
