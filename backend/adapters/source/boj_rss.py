"""Bank of Japan RSS adapter.

Fetches BOJ press releases, policy decisions,
and statistical publications via RSS.
"""

from datetime import UTC, datetime
from typing import Any

import feedparser
import httpx

BOJ_FEEDS = {
    "whatsnew": (
        "https://www.boj.or.jp/rss/whatsnew.xml"
    ),
    "announcements": (
        "https://www.boj.or.jp/rss/announce.xml"
    ),
}


class BOJRSSAdapter:
    """Fetch BOJ publications via RSS."""

    async def health(self) -> bool:
        try:
            async with httpx.AsyncClient() as c:
                r = await c.get(
                    BOJ_FEEDS["whatsnew"],
                    timeout=10,
                )
                return r.status_code == 200
        except Exception:
            return False

    async def fetch(
        self,
        *,
        feed_key: str = "whatsnew",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch BOJ RSS entries."""
        url = BOJ_FEEDS.get(
            feed_key, BOJ_FEEDS["whatsnew"]
        )
        async with httpx.AsyncClient() as c:
            r = await c.get(url, timeout=30)
            r.raise_for_status()

        feed = feedparser.parse(r.text)
        results: list[dict[str, Any]] = []

        for entry in feed.entries[:limit]:
            published = entry.get(
                "published",
                datetime.now(UTC).isoformat(),
            )
            results.append({
                "headline": entry.get(
                    "title", ""
                ),
                "url": entry.get("link", ""),
                "raw_text": entry.get(
                    "summary", ""
                ),
                "native_doc_id": entry.get(
                    "id", ""
                ),
                "published_at": published,
                "language_code": "ja",
                "source_tier": "official",
                "symbols": [],
                "raw_payload_json": dict(entry),
            })

        return results
