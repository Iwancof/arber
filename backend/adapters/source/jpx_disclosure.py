"""JPX Company Announcements adapter.

Fetches timely disclosures from JPX's public
Company Announcements Disclosure Service.
"""

import logging
from datetime import UTC, datetime
from typing import Any

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger("eos.jpx")

# JPX timely disclosure listing page
JPX_DISCLOSURE_URL = (
    "https://www.release.tdnet.info/inbs/"
    "I_list_001_00.html"
)


class JPXDisclosureAdapter:
    """Fetch timely disclosures from JPX."""

    def __init__(self) -> None:
        self._headers = {
            "User-Agent": (
                "EventIntelligenceOS/1.0"
            ),
        }

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(
                    JPX_DISCLOSURE_URL,
                    headers=self._headers,
                    timeout=10,
                )
                return r.status_code == 200
        except Exception:
            return False

    async def fetch(
        self,
        *,
        limit: int = 20,
    ) -> list[dict[str, Any]]:
        """Fetch recent disclosures from JPX."""
        async with httpx.AsyncClient() as c:
            r = await c.get(
                JPX_DISCLOSURE_URL,
                headers=self._headers,
                timeout=30,
            )
            r.raise_for_status()

        # Parse HTML table
        soup = BeautifulSoup(
            r.text, "html.parser"
        )
        results: list[dict[str, Any]] = []

        # TDnet lists disclosures in a table
        rows = soup.select("tr")
        for row in rows[:limit]:
            cells = row.select("td")
            if len(cells) < 4:
                continue

            time_text = cells[0].get_text(
                strip=True
            )
            code = cells[1].get_text(strip=True)
            company = cells[2].get_text(strip=True)
            title = cells[3].get_text(strip=True)
            link_tag = cells[3].select_one("a")
            url = ""
            if link_tag and link_tag.get("href"):
                url = link_tag["href"]
                if not url.startswith("http"):
                    base = (
                        "https://www.release"
                        ".tdnet.info"
                    )
                    url = base + url

            results.append({
                "headline": (
                    f"{company} {title}"
                ),
                "url": url,
                "raw_text": title,
                "native_doc_id": (
                    f"jpx-{code}-{time_text}"
                ),
                "published_at": datetime.now(
                    UTC
                ).isoformat(),
                "language_code": "ja",
                "source_tier": "official",
                "symbols": (
                    [code] if code else []
                ),
                "raw_payload_json": {
                    "issuer_code": code,
                    "company": company,
                    "title": title,
                    "time": time_text,
                },
            })

        return results
