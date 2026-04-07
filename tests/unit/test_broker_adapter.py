"""Tests for broker adapter and mock implementation."""

from decimal import Decimal
from uuid import uuid4

from backend.adapters.broker.base import (
    OrderIntent,
    OrderStatus,
)
from backend.adapters.broker.mock_broker import MockBrokerAdapter


def test_order_intent_defaults():
    """OrderIntent should have sensible defaults."""
    intent = OrderIntent(
        instrument_id=uuid4(),
        symbol="AAPL",
        side="buy",
        quantity=Decimal("10"),
    )
    assert intent.order_type == "market"
    assert intent.time_in_force == "day"
    assert intent.session_type == "regular"
    assert intent.execution_mode == "paper"


def test_order_status_defaults():
    """OrderStatus should default to new."""
    status = OrderStatus(client_order_id="test-001")
    assert status.status == "new"
    assert status.filled_qty == Decimal("0")


def test_mock_broker_adapter_code():
    """Mock broker should identify itself."""
    broker = MockBrokerAdapter()
    assert broker.adapter_code == "mock_paper_v1"


def test_mock_broker_supported_modes():
    """Mock broker should support paper modes."""
    broker = MockBrokerAdapter()
    assert "paper" in broker.supported_execution_modes
    assert "replay" in broker.supported_execution_modes


async def test_mock_broker_health():
    """Mock broker should be healthy."""
    broker = MockBrokerAdapter()
    assert await broker.health() is True


async def test_mock_broker_submit_market_order():
    """Market order should fill immediately."""
    broker = MockBrokerAdapter()
    intent = OrderIntent(
        instrument_id=uuid4(),
        symbol="AAPL",
        side="buy",
        quantity=Decimal("10"),
        order_type="market",
        limit_price=Decimal("150.00"),
    )
    status = await broker.submit(intent)
    assert status.status == "filled"
    assert status.filled_qty == Decimal("10")
    assert status.avg_fill_price == Decimal("150.00")
    assert status.client_order_id.startswith("mock-")


async def test_mock_broker_submit_limit_order():
    """Limit order should stay as accepted."""
    broker = MockBrokerAdapter()
    intent = OrderIntent(
        instrument_id=uuid4(),
        symbol="AAPL",
        side="buy",
        quantity=Decimal("10"),
        order_type="limit",
        limit_price=Decimal("145.00"),
    )
    status = await broker.submit(intent)
    assert status.status == "accepted"


async def test_mock_broker_cancel():
    """Should cancel an accepted order."""
    broker = MockBrokerAdapter()
    intent = OrderIntent(
        instrument_id=uuid4(),
        symbol="AAPL",
        side="buy",
        quantity=Decimal("10"),
        order_type="limit",
        limit_price=Decimal("145.00"),
    )
    status = await broker.submit(intent)
    canceled = await broker.cancel(status.client_order_id)
    assert canceled.status == "canceled"


async def test_mock_broker_cancel_filled_noop():
    """Canceling a filled order should not change status."""
    broker = MockBrokerAdapter()
    intent = OrderIntent(
        instrument_id=uuid4(),
        symbol="AAPL",
        side="buy",
        quantity=Decimal("10"),
        limit_price=Decimal("150.00"),
    )
    status = await broker.submit(intent)
    assert status.status == "filled"
    result = await broker.cancel(status.client_order_id)
    assert result.status == "filled"


async def test_mock_broker_positions_after_fill():
    """Positions should update after a fill."""
    broker = MockBrokerAdapter()
    iid = uuid4()
    intent = OrderIntent(
        instrument_id=iid,
        symbol="AAPL",
        side="buy",
        quantity=Decimal("10"),
        limit_price=Decimal("150.00"),
    )
    await broker.submit(intent)
    positions = await broker.get_positions()
    assert len(positions) == 1
    assert positions[0].position_qty == Decimal("10")
    assert positions[0].symbol == "AAPL"


async def test_mock_broker_sell_reduces_position():
    """Selling should reduce position."""
    broker = MockBrokerAdapter()
    iid = uuid4()
    buy = OrderIntent(
        instrument_id=iid, symbol="AAPL",
        side="buy", quantity=Decimal("10"),
        limit_price=Decimal("150"),
    )
    sell = OrderIntent(
        instrument_id=iid, symbol="AAPL",
        side="sell", quantity=Decimal("3"),
        limit_price=Decimal("155"),
    )
    await broker.submit(buy)
    await broker.submit(sell)
    positions = await broker.get_positions()
    assert positions[0].position_qty == Decimal("7")


async def test_mock_broker_get_fills():
    """Should return fills for a filled order."""
    broker = MockBrokerAdapter()
    intent = OrderIntent(
        instrument_id=uuid4(),
        symbol="AAPL",
        side="buy",
        quantity=Decimal("10"),
        limit_price=Decimal("150.00"),
    )
    status = await broker.submit(intent)
    fills = broker.get_fills(status.client_order_id)
    assert len(fills) == 1
    assert fills[0].fill_qty == Decimal("10")
    assert fills[0].fill_price == Decimal("150.00")
