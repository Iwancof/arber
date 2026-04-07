"""Broker adapter base interface.

Abstracts broker-specific logic behind a unified contract.
Supports execution modes: replay, shadow, paper, micro_live, live.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import UTC, datetime
from decimal import Decimal
from typing import Any
from uuid import UUID


@dataclass
class OrderIntent:
    """Order intent submitted to a broker adapter."""
    instrument_id: UUID
    symbol: str
    side: str  # buy | sell
    quantity: Decimal
    order_type: str = "market"  # market | limit | stop | stop_limit
    limit_price: Decimal | None = None
    stop_price: Decimal | None = None
    time_in_force: str = "day"
    session_type: str = "regular"
    decision_id: UUID | None = None
    execution_mode: str = "paper"
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class OrderStatus:
    """Order status returned by a broker adapter."""
    client_order_id: str
    broker_order_id: str | None = None
    status: str = "new"  # new|accepted|partially_filled|filled|canceled|rejected|expired
    filled_qty: Decimal = Decimal("0")
    avg_fill_price: Decimal | None = None
    status_reason: str | None = None
    updated_at: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )


@dataclass
class Fill:
    """Execution fill from a broker."""
    fill_price: Decimal
    fill_qty: Decimal
    fill_time: datetime = field(
        default_factory=lambda: datetime.now(UTC)
    )
    fee_estimate: Decimal | None = None
    liquidity_flag: str | None = None


@dataclass
class PositionInfo:
    """Position information from a broker."""
    instrument_id: UUID
    symbol: str
    position_qty: Decimal = Decimal("0")
    average_cost: Decimal | None = None
    mark_price: Decimal | None = None
    unrealized_pnl: Decimal | None = None


class BrokerAdapter(ABC):
    """Abstract broker adapter interface."""

    @abstractmethod
    async def health(self) -> bool:
        """Check broker connectivity."""
        ...

    @abstractmethod
    async def submit(self, intent: OrderIntent) -> OrderStatus:
        """Submit an order intent."""
        ...

    @abstractmethod
    async def cancel(self, client_order_id: str) -> OrderStatus:
        """Cancel an open order."""
        ...

    @abstractmethod
    async def get_order_status(
        self, client_order_id: str
    ) -> OrderStatus:
        """Get current order status."""
        ...

    @abstractmethod
    async def get_positions(self) -> list[PositionInfo]:
        """Get all current positions."""
        ...

    @property
    @abstractmethod
    def adapter_code(self) -> str:
        """Unique identifier for this adapter."""
        ...

    @property
    @abstractmethod
    def supported_execution_modes(self) -> list[str]:
        """Execution modes this adapter supports."""
        ...
