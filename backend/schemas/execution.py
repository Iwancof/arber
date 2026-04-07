"""Execution and order schemas."""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID

from backend.schemas.common import OrmBase, PaginatedResponse


class OrderLedgerRead(OrmBase):
    """Order ledger response schema."""

    order_id: UUID
    decision_id: UUID
    instrument_id: UUID
    execution_mode: str
    broker_name: str
    client_order_id: str
    broker_order_id: str | None = None
    side: str
    order_type: str
    time_in_force: str
    session_type: str
    qty: Decimal
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    status: str
    status_reason: str | None = None
    submitted_at: datetime
    updated_at: datetime | None = None
    metadata_json: dict[str, Any] = {}


class OrderList(PaginatedResponse):
    """Paginated list of orders."""

    items: list[OrderLedgerRead]


class ExecutionFillRead(OrmBase):
    """Execution fill response schema."""

    fill_id: UUID
    order_id: UUID
    fill_time: datetime
    fill_price: Decimal
    fill_qty: Decimal
    fee_estimate: Decimal | None = None
    liquidity_flag: str | None = None
    fill_source: str
    metadata_json: dict[str, Any] = {}


class PositionSnapshotRead(OrmBase):
    """Position snapshot response schema."""

    position_snapshot_id: UUID
    as_of: datetime
    execution_mode: str
    instrument_id: UUID
    position_qty: Decimal
    average_cost: Decimal | None = None
    mark_price: Decimal | None = None
    unrealized_pnl: Decimal | None = None
    realized_pnl: Decimal | None = None
    snapshot_json: dict[str, Any] = {}


class KillSwitchRead(OrmBase):
    """Kill switch response schema."""

    kill_switch_id: UUID
    scope_type: str
    scope_key: str
    active: bool
    reason: str
    activated_by: UUID | None = None
    activated_at: datetime
    cleared_at: datetime | None = None


class KillSwitchActivate(OrmBase):
    """Kill switch activation request."""

    scope_type: str = "global"
    scope_key: str = "all"
    reason: str
    activated_by: UUID | None = None
