"""Tests for execution Pydantic schemas."""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from backend.schemas.execution import (
    ExecutionFillRead,
    KillSwitchActivate,
    KillSwitchRead,
    OrderLedgerRead,
    PositionSnapshotRead,
)


def test_order_ledger_read():
    """OrderLedgerRead should parse correctly."""
    now = datetime.now(tz=UTC)
    o = OrderLedgerRead(
        order_id=uuid4(),
        decision_id=uuid4(),
        instrument_id=uuid4(),
        execution_mode="paper",
        broker_name="mock_paper_v1",
        client_order_id="mock-abc123",
        side="buy",
        order_type="market",
        time_in_force="day",
        session_type="regular",
        qty=Decimal("10"),
        status="filled",
        submitted_at=now,
        updated_at=now,
        metadata_json={},
    )
    assert o.side == "buy"
    assert o.status == "filled"


def test_kill_switch_activate():
    """KillSwitchActivate should have defaults."""
    ks = KillSwitchActivate(reason="Emergency stop")
    assert ks.scope_type == "global"
    assert ks.scope_key == "all"


def test_kill_switch_read():
    """KillSwitchRead should parse correctly."""
    ks = KillSwitchRead(
        kill_switch_id=uuid4(),
        scope_type="market",
        scope_key="US_EQUITY",
        active=True,
        reason="Volatility",
        activated_at=datetime.now(tz=UTC),
    )
    assert ks.active is True


def test_position_snapshot_read():
    """PositionSnapshotRead should handle decimals."""
    snap = PositionSnapshotRead(
        position_snapshot_id=uuid4(),
        as_of=datetime.now(tz=UTC),
        execution_mode="paper",
        instrument_id=uuid4(),
        position_qty=Decimal("100"),
        average_cost=Decimal("150.50"),
        mark_price=Decimal("152.00"),
        unrealized_pnl=Decimal("150.00"),
        snapshot_json={},
    )
    assert snap.position_qty == Decimal("100")


def test_execution_fill_read():
    """ExecutionFillRead should parse correctly."""
    f = ExecutionFillRead(
        fill_id=uuid4(),
        order_id=uuid4(),
        fill_time=datetime.now(tz=UTC),
        fill_price=Decimal("150.25"),
        fill_qty=Decimal("10"),
        fill_source="paper",
        metadata_json={},
    )
    assert f.fill_source == "paper"
