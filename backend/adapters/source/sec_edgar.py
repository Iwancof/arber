"""SEC EDGAR source adapter.

Fetches company filings from SEC EDGAR RSS feeds.
Free, no authentication required.
"""

from datetime import UTC, datetime
from typing import Any

import feedparser
import httpx


class SECEdgarAdapter:
    """Fetch SEC filings via EDGAR RSS and API."""

    COMPANY_RSS = (
        "https://www.sec.gov/cgi-bin/browse-edgar"
        "?action=getcompany&CIK={cik}"
        "&type={filing_type}&dateb=&owner=include"
        "&count=10&search_text=&action=getcompany"
        "&output=atom"
    )
    FULL_TEXT_RSS = (
        "https://efts.sec.gov/LATEST/search-index"
        "?q=%22{query}%22&dateRange=custom"
        "&startdt={start}&enddt={end}"
        "&forms={forms}"
    )
    SUBMISSIONS_URL = (
        "https://data.sec.gov/submissions/"
        "CIK{cik}.json"
    )

    def __init__(self) -> None:
        self._headers = {
            "User-Agent": (
                "EventIntelligenceOS/1.0 "
                "(contact@example.com)"
            ),
            "Accept": "application/json",
        }

    async def health(self) -> bool:
        """Check EDGAR API connectivity."""
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    "https://data.sec.gov/submissions/"
                    "CIK0000320193.json",
                    headers=self._headers,
                    timeout=10,
                )
                return resp.status_code == 200
        except Exception:
            return False

    async def fetch_filings(
        self,
        *,
        cik: str,
        filing_type: str = "10-Q",
        limit: int = 10,
    ) -> list[dict[str, Any]]:
        """Fetch recent filings for a company."""
        cik_padded = cik.zfill(10)
        url = self.SUBMISSIONS_URL.format(
            cik=cik_padded
        )

        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                headers=self._headers,
                timeout=30,
            )
            resp.raise_for_status()
            data = resp.json()

        filings = data.get("filings", {}).get(
            "recent", {}
        )
        results: list[dict[str, Any]] = []

        forms = filings.get("form", [])
        dates = filings.get("filingDate", [])
        accessions = filings.get(
            "accessionNumber", []
        )
        descriptions = filings.get(
            "primaryDocDescription", []
        )

        company_name = data.get("name", "")

        for i in range(min(len(forms), limit)):
            if filing_type and forms[i] != filing_type:
                continue
            acc_clean = accessions[i].replace("-", "")
            desc = (
                descriptions[i]
                if i < len(descriptions)
                else ""
            )
            results.append(
                self._normalize(
                    cik=cik_padded,
                    company=company_name,
                    form=forms[i],
                    date=dates[i],
                    accession=accessions[i],
                    acc_clean=acc_clean,
                    description=desc,
                )
            )
            if len(results) >= limit:
                break

        return results

    async def fetch_rss(
        self,
        *,
        cik: str,
        filing_type: str = "",
    ) -> list[dict[str, Any]]:
        """Fetch filings via EDGAR RSS feed."""
        url = self.COMPANY_RSS.format(
            cik=cik, filing_type=filing_type
        )
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                url,
                headers={
                    "User-Agent": (
                        self._headers["User-Agent"]
                    )
                },
                timeout=30,
            )
            resp.raise_for_status()

        feed = feedparser.parse(resp.text)
        return [
            {
                "headline": entry.get("title", ""),
                "url": entry.get("link", ""),
                "raw_text": entry.get(
                    "summary", ""
                ),
                "native_doc_id": entry.get("id", ""),
                "published_at": entry.get(
                    "updated",
                    datetime.now(UTC).isoformat(),
                ),
                "language_code": "en",
                "source_tier": "official",
                "raw_payload_json": dict(entry),
            }
            for entry in feed.entries
        ]

    def _normalize(
        self,
        *,
        cik: str,
        company: str,
        form: str,
        date: str,
        accession: str,
        acc_clean: str,
        description: str,
    ) -> dict[str, Any]:
        """Normalize a filing to ingest format."""
        url = (
            "https://www.sec.gov/Archives/"
            f"edgar/data/{cik}/{acc_clean}/"
            f"{accession}-index.htm"
        )
        return {
            "headline": (
                f"{company} {form} filing"
            ),
            "url": url,
            "raw_text": description,
            "native_doc_id": accession,
            "published_at": f"{date}T00:00:00Z",
            "language_code": "en",
            "source_tier": "official",
            "symbols": [],
            "raw_payload_json": {
                "cik": cik,
                "company": company,
                "form": form,
                "filing_date": date,
                "accession": accession,
            },
        }
