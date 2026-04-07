"""Alpaca News source adapter.

Fetches financial news via Alpaca's news API (Benzinga).
Supports both historical fetch and real-time streaming.
"""

from datetime import UTC, datetime
from typing import Any

import httpx

from backend.config.settings import settings


class AlpacaNewsAdapter:
    """Fetch news from Alpaca's news API."""

    def __init__(self) -> None:
        self._base_url = (
            "https://data.alpaca.markets/v1beta1/news"
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
                    self._base_url,
                    headers=self._headers,
                    params={"limit": 1},
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def fetch(
        self,
        *,
        symbols: list[str] | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
        limit: int = 50,
    ) -> list[dict[str, Any]]:
        """Fetch news articles from Alpaca."""
        params: dict[str, Any] = {"limit": limit}
        if symbols:
            params["symbols"] = ",".join(symbols)
        if start:
            params["start"] = start.isoformat()
        if end:
            params["end"] = end.isoformat()

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self._base_url,
                headers=self._headers,
                params=params,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        return [
            self._normalize(article)
            for article in data.get("news", [])
        ]

    def _normalize(
        self, article: dict[str, Any]
    ) -> dict[str, Any]:
        """Normalize Alpaca news to ingest format."""
        return {
            "headline": article.get("headline", ""),
            "url": article.get("url", ""),
            "raw_text": article.get("summary", ""),
            "native_doc_id": str(
                article.get("id", "")
            ),
            "published_at": article.get(
                "created_at",
                datetime.now(UTC).isoformat(),
            ),
            "language_code": "en",
            "source_tier": "high_vendor",
            "symbols": article.get("symbols", []),
            "raw_payload_json": article,
        }
