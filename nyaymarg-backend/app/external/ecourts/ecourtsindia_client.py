"""
app/external/ecourts/ecourtsindia_client.py
============================================
eCourtsIndia.com API — commercial-grade real-time eCourts scraper.

₹200 free credits on signup (~100 case lookups).
Covers 600+ district courts, 25 High Courts, Supreme Court.
Supports: certified-copy PDF, bulk refresh, live cause lists, force re-scrape.
Sign up: https://ecourtsindia.com/api
"""
from __future__ import annotations

from app.config import settings
from app.external.base_client import BaseAPIClient


class ECourtsIndiaClient(BaseAPIClient):
    name     = "ecourtsindia"
    base_url = settings.ECOURTSINDIA_BASE

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.ECOURTSINDIA_TOKEN}"}

    # ── ENDPOINT 1: Get case by CNR ───────────────────────────────────────────
    async def get_case(self, cnr: str) -> dict:
        """
        GET /partner/case/{cnr}
        Real-time data from eCourts.gov.in — timeline, hearings, orders,
        parties, advocates, PDF links.
        """
        return await self.get(f"/partner/case/{cnr}", headers=self._headers())

    # ── ENDPOINT 2: Cause list ────────────────────────────────────────────────
    async def get_causelist(
        self, court: str, date: str, bench: str | None = None
    ) -> dict:
        """
        GET /partner/causelist?court=...&date=...&bench=...
        Full daily cause list. Also supports CNR-specific lookup.
        """
        params: dict = {"court": court, "date": date}
        if bench:
            params["bench"] = bench
        return await self.get(
            "/partner/causelist",
            headers=self._headers(),
            params=params,
            use_cache=False,
        )

    # ── ENDPOINT 3: Order PDF + markdown ─────────────────────────────────────
    async def get_order(self, cnr: str, order_id: str) -> dict:
        """
        GET /partner/order/{cnr}/{order_id}
        Returns watermarked certified-copy PDF URL + extracted markdown.
        Response: {"pdf_url": "...", "markdown_text": "..."}
        """
        return await self.get(
            f"/partner/order/{cnr}/{order_id}",
            headers=self._headers(),
        )

    # ── ENDPOINT 4: Bulk refresh (up to 50 CNRs) ─────────────────────────────
    async def bulk_refresh(self, cnr_list: list[str]) -> dict:
        """
        POST /partner/bulk-refresh
        Queue up to 50 CNR numbers for batch refresh (~30s async).
        Response: {"job_id": "...", "queued": int, "ready_in_seconds": 30}
        """
        return await self.post(
            "/partner/bulk-refresh",
            headers=self._headers(),
            json={"cnrs": cnr_list},
            use_cache=False,
        )

    # ── ENDPOINT 5: Force re-scrape ───────────────────────────────────────────
    async def force_refresh(self, cnr: str) -> dict:
        """
        POST /partner/refresh/{cnr}
        Immediate re-scrape from official eCourts servers (5–10s).
        """
        return await self.post(
            f"/partner/refresh/{cnr}",
            headers=self._headers(),
            use_cache=False,
        )

    # ── ENDPOINT 6: Live enumeration codes (free, no auth) ────────────────────
    async def get_enums(self) -> dict:
        """
        GET /partner/enums
        Live case types, statuses, court codes from the API.
        """
        return await self.get("/partner/enums")
