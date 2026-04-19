"""
app/external/kanoon_dev/client.py
===================================
kanoon.dev — structured, developer-friendly Indian legal API.

Provides typed objects for courts, cases, orders, and AI insights
(habeas corpus nature analysis etc.).
Free tier available. Sign up: https://kanoon.dev
"""
from __future__ import annotations

from app.config import settings
from app.external.base_client import BaseAPIClient


class KanoonDevClient(BaseAPIClient):
    name     = "kanoon_dev"
    base_url = settings.KANOON_DEV_BASE

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {settings.KANOON_DEV_API_KEY}"}

    # ── ENDPOINT 1: List courts ───────────────────────────────────────────────
    async def list_courts(self) -> list[dict]:
        """
        GET /courts
        All Indian courts with their unique IDs for use in subsequent calls.
        Returns: [{"id": "sc", "name": "Supreme Court of India"}, ...]
        """
        return await self.get("/courts", headers=self._headers())  # type: ignore[return-value]

    # ── ENDPOINT 2: Cases for a court ────────────────────────────────────────
    async def get_court_cases(self, court_id: str, limit: int = 20) -> dict:
        """
        GET /courts/{court_id}/cases?limit=N
        Paginated case list for a specific court.
        court_id examples: "sc", "delhi_hc", "bombay_hc"
        """
        return await self.get(
            f"/courts/{court_id}/cases",
            headers=self._headers(),
            params={"limit": limit},
        )

    # ── ENDPOINT 3: Orders for a case ────────────────────────────────────────
    async def get_case_orders(self, case_id: str) -> list[dict]:
        """
        GET /cases/{case_id}/orders
        All orders (interim + final) for a case.
        Each order: id, date, judges, pdf_url, text.
        """
        return await self.get(f"/cases/{case_id}/orders", headers=self._headers())  # type: ignore[return-value]

    # ── ENDPOINT 4: AI insights for a case ────────────────────────────────────
    async def get_insights(self, case_id: str) -> list[dict]:
        """
        GET /cases/{case_id}/insights
        AI-generated structural insights.
        Types: habeas_nature, detention analysis, liberty claims.
        Returns: [{id, type, data: {liberty_claim_type, restraint_type, ...}}]
        """
        return await self.get(f"/cases/{case_id}/insights", headers=self._headers())  # type: ignore[return-value]
