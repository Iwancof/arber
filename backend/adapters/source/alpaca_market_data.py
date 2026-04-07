"""Alpaca market data adapter.

Fetches historical and real-time stock price data
for outcome evaluation and position tracking.
"""

from datetime import datetime
from decimal import Decimal
from typing import Any

import httpx

from backend.config.settings import settings


class AlpacaMarketDataAdapter:
    """Fetch stock price data from Alpaca."""

    def __init__(self) -> None:
        self._base = (
            "https://data.alpaca.markets/v2"
        )
        self._headers = {
            "APCA-API-KEY-ID": settings.alpaca_api_key,
            "APCA-API-SECRET-KEY": (
                settings.alpaca_secret_key
            ),
        }

    async def health(self) -> bool:
        """Check API connectivity."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    f"{self._base}/stocks/AAPL/bars",
                    headers=self._headers,
                    params={
                        "timeframe": "1Day",
                        "limit": 1,
                    },
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def get_daily_bars(
        self,
        symbol: str,
        *,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 30,
    ) -> list[dict[str, Any]]:
        """Fetch daily OHLCV bars."""
        params: dict[str, Any] = {
            "timeframe": "1Day",
            "limit": limit,
        }
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()

        url = (
            f"{self._base}/stocks/{symbol}/bars"
        )
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                headers=self._headers,
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        return data.get("bars", [])

    async def get_latest_price(
        self, symbol: str
    ) -> Decimal | None:
        """Get the latest trade price."""
        url = (
            f"{self._base}/stocks"
            f"/{symbol}/trades/latest"
        )
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url,
                    headers=self._headers,
                    timeout=10,
                )
                resp.raise_for_status()
                data = resp.json()
            trade = data.get("trade", {})
            price = trade.get("p")
            if price is None:
                return None
            return Decimal(str(price))
        except Exception:
            return None

    async def get_snapshot(
        self, symbol: str
    ) -> dict[str, Any] | None:
        """Get market snapshot for a symbol."""
        url = (
            f"{self._base}/stocks"
            f"/{symbol}/snapshot"
        )
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url,
                    headers=self._headers,
                    timeout=10,
                )
                resp.raise_for_status()
                return resp.json()
        except Exception:
            return None
