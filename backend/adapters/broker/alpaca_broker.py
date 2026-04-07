"""Alpaca Paper Trading broker adapter.

Connects to Alpaca Paper API for order submission,
cancellation, position tracking, and fills.
"""

from decimal import Decimal
from typing import Any
from uuid import uuid4

import httpx

from backend.adapters.broker.base import (
    BrokerAdapter,
    OrderIntent,
    OrderStatus,
    PositionInfo,
)
from backend.config.settings import settings


class AlpacaPaperBrokerAdapter(BrokerAdapter):
    """Alpaca Paper Trading broker."""

    def __init__(self) -> None:
        self._base = settings.alpaca_base_url
        self._headers = {
            "APCA-API-KEY-ID": settings.alpaca_api_key,
            "APCA-API-SECRET-KEY": (
                settings.alpaca_secret_key
            ),
        }

    @property
    def adapter_code(self) -> str:
        return "alpaca_paper_v1"

    @property
    def supported_execution_modes(self) -> list[str]:
        return ["paper"]

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(
                    f"{self._base}/v2/account",
                    headers=self._headers,
                    timeout=10,
                )
                return r.status_code == 200
        except Exception:
            return False

    async def submit(
        self, intent: OrderIntent
    ) -> OrderStatus:
        """Submit order to Alpaca Paper API."""
        body: dict[str, Any] = {
            "symbol": intent.symbol,
            "qty": str(intent.quantity),
            "side": intent.side,
            "type": intent.order_type,
            "time_in_force": intent.time_in_force,
        }
        if intent.limit_price and intent.order_type in (
            "limit", "stop_limit"
        ):
            body["limit_price"] = str(
                intent.limit_price
            )
        if intent.stop_price and intent.order_type in (
            "stop", "stop_limit"
        ):
            body["stop_price"] = str(
                intent.stop_price
            )

        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{self._base}/v2/orders",
                headers=self._headers,
                json=body,
                timeout=30,
            )

        if r.status_code not in (200, 201):
            return OrderStatus(
                client_order_id=(
                    f"err-{uuid4().hex[:8]}"
                ),
                status="rejected",
                status_reason=r.text[:200],
            )

        data = r.json()
        return OrderStatus(
            client_order_id=data.get(
                "client_order_id",
                data.get("id", ""),
            ),
            broker_order_id=data.get("id"),
            status=self._map_status(
                data.get("status", "new")
            ),
            filled_qty=Decimal(
                data.get("filled_qty", "0")
            ),
            avg_fill_price=(
                Decimal(data["filled_avg_price"])
                if data.get("filled_avg_price")
                else None
            ),
        )

    async def cancel(
        self, client_order_id: str
    ) -> OrderStatus:
        """Cancel order via Alpaca API."""
        async with httpx.AsyncClient() as c:
            r = await c.delete(
                f"{self._base}/v2/orders/"
                f"{client_order_id}",
                headers=self._headers,
                timeout=15,
            )
        if r.status_code in (200, 204):
            return OrderStatus(
                client_order_id=client_order_id,
                status="canceled",
            )
        return OrderStatus(
            client_order_id=client_order_id,
            status="rejected",
            status_reason=r.text[:200],
        )

    async def get_order_status(
        self, client_order_id: str
    ) -> OrderStatus:
        """Get order status from Alpaca."""
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{self._base}/v2/orders/"
                f"{client_order_id}",
                headers=self._headers,
                timeout=10,
            )
        if r.status_code != 200:
            return OrderStatus(
                client_order_id=client_order_id,
                status="rejected",
                status_reason="Order not found",
            )
        data = r.json()
        return OrderStatus(
            client_order_id=data.get(
                "client_order_id",
                data.get("id", ""),
            ),
            broker_order_id=data.get("id"),
            status=self._map_status(
                data.get("status", "new")
            ),
            filled_qty=Decimal(
                data.get("filled_qty", "0")
            ),
            avg_fill_price=(
                Decimal(data["filled_avg_price"])
                if data.get("filled_avg_price")
                else None
            ),
        )

    async def get_positions(
        self,
    ) -> list[PositionInfo]:
        """Get all positions from Alpaca."""
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{self._base}/v2/positions",
                headers=self._headers,
                timeout=10,
            )
        if r.status_code != 200:
            return []
        positions = []
        for p in r.json():
            positions.append(PositionInfo(
                instrument_id=None,  # type: ignore
                symbol=p.get("symbol", ""),
                position_qty=Decimal(
                    p.get("qty", "0")
                ),
                average_cost=Decimal(
                    p.get("avg_entry_price", "0")
                ),
                mark_price=Decimal(
                    p.get("current_price", "0")
                ),
                unrealized_pnl=Decimal(
                    p.get("unrealized_pl", "0")
                ),
            ))
        return positions

    async def get_account(
        self,
    ) -> dict[str, Any]:
        """Get account info."""
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{self._base}/v2/account",
                headers=self._headers,
                timeout=10,
            )
        if r.status_code == 200:
            return r.json()
        return {}

    def _map_status(
        self, alpaca_status: str
    ) -> str:
        """Map Alpaca status to our status."""
        mapping = {
            "new": "new",
            "accepted": "accepted",
            "partially_filled": "partially_filled",
            "filled": "filled",
            "done_for_day": "filled",
            "canceled": "canceled",
            "expired": "expired",
            "replaced": "filled",
            "pending_new": "new",
            "pending_cancel": "canceled",
            "rejected": "rejected",
        }
        return mapping.get(alpaca_status, "new")
