"""Forecast pipeline service.

Orchestrates: retrieval → worker execution → reasoning trace → forecast ledger.
"""

from decimal import Decimal
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.adapters.worker.base import WorkerAdapter, WorkerTask
from backend.core.outbox import emit_event
from backend.models.content import EventLedger
from backend.models.core import Instrument
from backend.models.forecasting import (
    ForecastHorizon,
    ForecastLedger,
    ReasoningTrace,
    RetrievalItem,
    RetrievalSet,
)


async def build_retrieval_set(
    db: AsyncSession,
    *,
    event_id: UUID | None,
    mode: str = "episodic",
) -> RetrievalSet:
    """Build a retrieval set for an event.

    In v1, this creates a simple retrieval set referencing the source event.
    Future: semantic search, episodic retrieval, etc.
    """
    retrieval_set = RetrievalSet(
        event_id=event_id,
        retrieval_version="v1_simple",
        retrieval_mode=mode,
        metadata_json={},
    )
    db.add(retrieval_set)
    await db.flush()

    if event_id:
        item = RetrievalItem(
            retrieval_set_id=retrieval_set.retrieval_set_id,
            item_type="event",
            item_ref_id=event_id,
            rank=1,
            selected_by="rule",
            metadata_json={},
        )
        db.add(item)
        await db.flush()

    return retrieval_set


async def run_forecast_pipeline(
    db: AsyncSession,
    worker: WorkerAdapter,
    *,
    event_id: UUID,
    instrument_id: UUID,
    market_profile_id: UUID,
    execution_mode: str = "replay",
    prompt_template_id: str = "default_forecast_v1",
    prompt_version: str = "1.0.0",
    benchmark_instrument_id: UUID | None = None,
) -> ForecastLedger:
    """Run the full forecast pipeline for an event + instrument.

    Steps:
    1. Build retrieval set
    2. Execute worker task
    3. Store reasoning trace
    4. Create forecast ledger entry with horizons
    """
    # 1. Retrieval
    retrieval_set = await build_retrieval_set(db, event_id=event_id)

    # 2. Worker execution
    event_result = await db.execute(
        select(EventLedger).where(EventLedger.event_id == event_id)
    )
    event = event_result.scalar_one()

    instrument_result = await db.execute(
        select(Instrument).where(Instrument.instrument_id == instrument_id)
    )
    instrument = instrument_result.scalar_one()

    task = WorkerTask(
        task_type="single_name_forecast",
        schema_name="forecast",
        schema_version="1.0.0",
        prompt_template_id=prompt_template_id,
        prompt_version=prompt_version,
        input_payload={
            "event_type": event.event_type,
            "event_json": event.event_json,
            "instrument_symbol": instrument.symbol,
            "market_profile_id": str(market_profile_id),
            "direction_hint": event.direction_hint,
            "materiality": str(event.materiality) if event.materiality else None,
        },
        evidence_refs=[str(event.raw_document_id)],
        mode=execution_mode,
    )

    result = await worker.execute(task)

    # Reject invalid responses
    if not result.schema_valid or not result.parsed_json:
        raise ValueError(
            f"Worker returned invalid forecast: "
            f"{result.parse_errors}"
        )

    # 3. Reasoning trace
    trace = ReasoningTrace(
        event_id=event_id,
        retrieval_set_id=retrieval_set.retrieval_set_id,
        trace_version="1.0.0",
        trace_json=result.reasoning_trace_summary,
    )
    db.add(trace)
    await db.flush()

    # 4. Forecast ledger
    confidence_raw = result.parsed_json.get("confidence_after")
    confidence = Decimal(str(confidence_raw)) if confidence_raw is not None else None

    forecast = ForecastLedger(
        event_id=event_id,
        instrument_id=instrument_id,
        benchmark_instrument_id=benchmark_instrument_id,
        market_profile_id=market_profile_id,
        reasoning_trace_id=trace.reasoning_trace_id,
        model_family=result.model_name,
        model_version=result.model_version,
        worker_id=worker.adapter_code,
        prompt_template_id=prompt_template_id,
        prompt_version=prompt_version,
        forecast_mode=execution_mode,
        confidence=confidence,
        no_trade_reason_codes_json=[],
        forecast_json=result.parsed_json,
    )
    db.add(forecast)
    await db.flush()

    # 5. Forecast horizons
    horizons_data: dict[str, Any] = result.parsed_json.get("horizons", {})
    for horizon_code, h_data in horizons_data.items():
        horizon = ForecastHorizon(
            forecast_id=forecast.forecast_id,
            horizon_code=horizon_code,
            p_outperform_benchmark=_to_decimal(h_data.get("p_outperform")),
            p_underperform_benchmark=_to_decimal(h_data.get("p_underperform")),
            ret_q10=_to_decimal(h_data.get("ret_q10")),
            ret_q50=_to_decimal(h_data.get("ret_q50")),
            ret_q90=_to_decimal(h_data.get("ret_q90")),
        )
        db.add(horizon)

    # Emit outbox event within the same transaction
    await emit_event(
        db,
        event_type="created",
        aggregate_type="forecast",
        aggregate_id=str(forecast.forecast_id),
        payload={
            "instrument_id": str(instrument_id),
            "event_id": str(event_id),
            "confidence": str(confidence),
        },
    )

    await db.commit()
    await db.refresh(forecast)
    return forecast


def _to_decimal(value: Any) -> Decimal | None:
    """Safely convert a value to Decimal."""
    if value is None:
        return None
    return Decimal(str(value))
