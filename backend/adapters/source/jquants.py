"""J-Quants API adapter.

JPX official API for historical stock prices,
financial info, and listed companies.
"""

from decimal import Decimal
from typing import Any

import httpx

from backend.config.settings import settings

JQUANTS_BASE = "https://api.jquants.com/v1"


class JQuantsAdapter:
    """J-Quants API for JP stock data."""

    def __init__(self) -> None:
        self._token: str | None = None

    async def _get_token(self) -> str:
        """Get or refresh auth token."""
        if self._token:
            return self._token

        async with httpx.AsyncClient() as c:
            r = await c.post(
                f"{JQUANTS_BASE}"
                "/token/auth_user",
                json={
                    "mailaddress": (
                        settings.jquants_email
                    ),
                    "password": (
                        settings.jquants_password
                    ),
                },
                timeout=10,
            )
            r.raise_for_status()
            refresh = r.json().get(
                "refreshToken", ""
            )

            r2 = await c.post(
                f"{JQUANTS_BASE}"
                "/token/auth_refresh",
                params={
                    "refreshtoken": refresh,
                },
                timeout=10,
            )
            r2.raise_for_status()
            self._token = r2.json().get(
                "idToken", ""
            )

        return self._token or ""

    async def health(self) -> bool:
        try:
            token = await self._get_token()
            return bool(token)
        except Exception:
            return False

    async def get_daily_quotes(
        self,
        code: str,
        *,
        date_from: str | None = None,
        date_to: str | None = None,
    ) -> list[dict[str, Any]]:
        """Get daily stock quotes."""
        token = await self._get_token()
        params: dict[str, str] = {"code": code}
        if date_from:
            params["from"] = date_from
        if date_to:
            params["to"] = date_to

        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{JQUANTS_BASE}"
                "/prices/daily_quotes",
                params=params,
                headers={
                    "Authorization": (
                        f"Bearer {token}"
                    ),
                },
                timeout=30,
            )
            r.raise_for_status()

        return r.json().get(
            "daily_quotes", []
        )

    async def get_latest_price(
        self, code: str
    ) -> Decimal | None:
        """Get the latest close price."""
        quotes = await self.get_daily_quotes(
            code,
            date_from=None,
            date_to=None,
        )
        if not quotes:
            return None
        last = quotes[-1]
        close = last.get(
            "Close"
        ) or last.get("AdjustmentClose")
        if close:
            return Decimal(str(close))
        return None

    async def get_listed_companies(
        self,
    ) -> list[dict[str, Any]]:
        """Get list of all listed companies."""
        token = await self._get_token()
        async with httpx.AsyncClient() as c:
            r = await c.get(
                f"{JQUANTS_BASE}/listed/info",
                headers={
                    "Authorization": (
                        f"Bearer {token}"
                    ),
                },
                timeout=30,
            )
            r.raise_for_status()
        return r.json().get("info", [])
