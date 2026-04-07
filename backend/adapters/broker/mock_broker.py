"""Mock broker adapter for paper/replay execution.

Simulates order execution with deterministic fills
for testing and paper trading.
"""

from datetime import UTC, datetime
from decimal import Decimal
from uuid import uuid4

from backend.adapters.broker.base import (
    BrokerAdapter,
    Fill,
    OrderIntent,
    OrderStatus,
    PositionInfo,
)


class MockBrokerAdapter(BrokerAdapter):
    """Mock broker for paper/replay modes.

    Immediately fills market orders at a simulated price.
    Tracks positions in memory.
    """

    def __init__(self) -> None:
        self._orders: dict[str, OrderStatus] = {}
        self._fills: dict[str, list[Fill]] = {}
        self._positions: dict[str, PositionInfo] = {}

    @property
    def adapter_code(self) -> str:
        return "mock_paper_v1"

    @property
    def supported_execution_modes(self) -> list[str]:
        return ["replay", "shadow", "paper"]

    async def health(self) -> bool:
        return True

    async def submit(self, intent: OrderIntent) -> OrderStatus:
        """Simulate immediate fill for market orders."""
        client_order_id = f"mock-{uuid4().hex[:12]}"
        broker_order_id = f"brk-{uuid4().hex[:8]}"

        if intent.order_type == "market":
            # Simulate immediate fill
            sim_price = (
                intent.limit_price or Decimal("100.00")
            )
            fill = Fill(
                fill_price=sim_price,
                fill_qty=intent.quantity,
                fill_time=datetime.now(UTC),
                fee_estimate=sim_price * intent.quantity
                * Decimal("0.001"),
            )

            status = OrderStatus(
                client_order_id=client_order_id,
                broker_order_id=broker_order_id,
                status="filled",
                filled_qty=intent.quantity,
                avg_fill_price=sim_price,
            )

            self._fills[client_order_id] = [fill]
            self._update_position(intent, fill)
        else:
            # Limit/stop orders stay as accepted
            status = OrderStatus(
                client_order_id=client_order_id,
                broker_order_id=broker_order_id,
                status="accepted",
            )

        self._orders[client_order_id] = status
        return status

    async def cancel(self, client_order_id: str) -> OrderStatus:
        """Cancel an open order."""
        if client_order_id not in self._orders:
            return OrderStatus(
                client_order_id=client_order_id,
                status="rejected",
                status_reason="Order not found",
            )
        order = self._orders[client_order_id]
        if order.status in (
            "filled", "canceled", "rejected",
        ):
            return order
        order.status = "canceled"
        order.updated_at = datetime.now(UTC)
        return order

    async def get_order_status(
        self, client_order_id: str
    ) -> OrderStatus:
        """Get order status."""
        if client_order_id not in self._orders:
            return OrderStatus(
                client_order_id=client_order_id,
                status="rejected",
                status_reason="Order not found",
            )
        return self._orders[client_order_id]

    async def get_positions(self) -> list[PositionInfo]:
        """Get all tracked positions."""
        return list(self._positions.values())

    def get_fills(self, client_order_id: str) -> list[Fill]:
        """Get fills for an order."""
        return self._fills.get(client_order_id, [])

    def _update_position(
        self, intent: OrderIntent, fill: Fill
    ) -> None:
        """Update in-memory position tracking."""
        key = str(intent.instrument_id)
        pos = self._positions.get(key)
        if pos is None:
            pos = PositionInfo(
                instrument_id=intent.instrument_id,
                symbol=intent.symbol,
            )
            self._positions[key] = pos

        if intent.side == "buy":
            pos.position_qty += fill.fill_qty
        else:
            pos.position_qty -= fill.fill_qty
        pos.average_cost = fill.fill_price
        pos.mark_price = fill.fill_price
