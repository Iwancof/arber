"""Feedback and postmortem schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.schemas.common import OrmBase, PaginatedResponse


class OutcomeRead(OrmBase):
    """Outcome ledger response schema."""
    outcome_id: UUID
    forecast_id: UUID
    horizon_code: str
    computed_at: datetime
    horizon_end_at: datetime | None = None
    realized_abs_return: Decimal | None = None
    realized_rel_return: Decimal | None = None
    benchmark_return: Decimal | None = None
    barrier_hit: bool | None = None
    mae: Decimal | None = None
    mfe: Decimal | None = None
    outcome_json: dict[str, Any]


class PostmortemRead(OrmBase):
    """Postmortem ledger response schema."""
    postmortem_id: UUID
    forecast_id: UUID
    outcome_id: UUID | None = None
    verdict: str
    failure_codes_json: list[Any]
    requires_source_review: bool
    requires_prompt_review: bool
    judge_version: str
    postmortem_json: dict[str, Any]
    created_at: datetime


class PostmortemList(PaginatedResponse):
    """Paginated list of postmortems."""
    items: list[PostmortemRead]
