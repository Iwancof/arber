"""Forecasting, decision, and reasoning trace schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.schemas.common import OrmBase, PaginatedResponse

# --- Reasoning Trace ---

class HypothesisRead(OrmBase):
    """A single hypothesis within a reasoning trace."""
    code: str
    weight: Decimal | None = None
    description: str | None = None


class CounterargumentRead(OrmBase):
    """A counterargument within a reasoning trace."""
    code: str
    severity: str | None = None
    description: str | None = None


class ReasoningTraceRead(OrmBase):
    """Structured reasoning trace response."""
    reasoning_trace_id: UUID
    event_id: UUID | None = None
    retrieval_set_id: UUID | None = None
    trace_version: str
    trace_json: dict[str, Any]
    created_at: datetime


# --- Retrieval ---

class RetrievalItemRead(OrmBase):
    """Single item in a retrieval set."""
    retrieval_item_id: UUID
    retrieval_set_id: UUID
    item_type: str
    item_ref_id: UUID | None = None
    item_ref_text: str | None = None
    rank: int
    similarity_score: Decimal | None = None
    selected_by: str


class RetrievalSetRead(OrmBase):
    """Retrieval set response."""
    retrieval_set_id: UUID
    event_id: UUID | None = None
    retrieval_version: str
    retrieval_mode: str
    created_at: datetime
    items: list[RetrievalItemRead] = []


# --- Forecast ---

class ForecastHorizonRead(OrmBase):
    """Forecast horizon detail."""
    forecast_horizon_id: UUID
    forecast_id: UUID
    horizon_code: str
    p_outperform_benchmark: Decimal | None = None
    p_underperform_benchmark: Decimal | None = None
    p_downside_barrier: Decimal | None = None
    ret_q10: Decimal | None = None
    ret_q50: Decimal | None = None
    ret_q90: Decimal | None = None
    vol_forecast: Decimal | None = None


class ForecastLedgerRead(OrmBase):
    """Forecast ledger response."""
    forecast_id: UUID
    event_id: UUID | None = None
    instrument_id: UUID
    benchmark_instrument_id: UUID | None = None
    market_profile_id: UUID
    reasoning_trace_id: UUID | None = None
    model_family: str
    model_version: str
    worker_id: str
    prompt_template_id: str
    prompt_version: str
    forecast_mode: str
    forecasted_at: datetime
    confidence: Decimal | None = None
    no_trade_reason_codes_json: list[Any]
    forecast_json: dict[str, Any]
    horizons: list[ForecastHorizonRead] = []


class ForecastList(PaginatedResponse):
    """Paginated list of forecasts."""
    items: list[ForecastLedgerRead]


# --- Decision ---

class DecisionReasonRead(OrmBase):
    """Decision reason detail."""
    decision_reason_id: UUID
    decision_id: UUID
    source_of_reason: str
    reason_code: str
    score_contribution: Decimal | None = None
    message: str | None = None


class DecisionLedgerRead(OrmBase):
    """Decision ledger response."""
    decision_id: UUID
    forecast_id: UUID
    market_profile_id: UUID
    execution_mode: str
    score: Decimal
    action: str
    decision_status: str
    policy_version: str
    size_cap: Decimal | None = None
    reason_codes_json: list[Any]
    decided_at: datetime
    reasons: list[DecisionReasonRead] = []


class DecisionList(PaginatedResponse):
    """Paginated list of decisions."""
    items: list[DecisionLedgerRead]


# --- Dossier (aggregate view) ---

class DossierRead(OrmBase):
    """Decision dossier aggregate - the central UI view."""
    decision: DecisionLedgerRead
    forecast: ForecastLedgerRead | None = None
    event: dict[str, Any] | None = None
    reasoning_trace: ReasoningTraceRead | None = None
    prompt_tasks: list[dict[str, Any]] = []
    orders: list[dict[str, Any]] = []
    outcomes: list[dict[str, Any]] = []


# --- Overlay (Grafana panel data) ---

class OverlayAnnotation(OrmBase):
    """Single annotation on the overlay chart."""
    time: datetime
    title: str
    text: str | None = None
    tags: list[str] = []


class ForecastBand(OrmBase):
    """Forecast band for overlay."""
    time: datetime
    horizon_code: str
    ret_q10: Decimal | None = None
    ret_q50: Decimal | None = None
    ret_q90: Decimal | None = None
    confidence: Decimal | None = None


class DecisionInterval(OrmBase):
    """Decision interval for overlay."""
    start: datetime
    end: datetime | None = None
    action: str
    score: Decimal
    decision_id: UUID


class OverlayPayload(OrmBase):
    """Overlay data for Grafana panel plugin."""
    instrument_id: UUID
    from_time: datetime
    to_time: datetime
    forecast_bands: list[ForecastBand] = []
    annotations: list[OverlayAnnotation] = []
    decision_intervals: list[DecisionInterval] = []
