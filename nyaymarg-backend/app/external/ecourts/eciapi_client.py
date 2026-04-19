"""
app/external/ecourts/eciapi_client.py
========================================
ECIAPI — e-Courts India API (eciapi.akshit.me)

100% FREE. No authentication required.
Enterprise-grade public API covering:
  - District Courts, High Courts, NCLT, Consumer Forum
  - Case status by CNR, party name search, daily cause lists

Docs: https://akshit-me.gitbook.io/e-courts-india-api
"""
from __future__ import annotations

from app.config import settings
from app.external.base_client import BaseAPIClient


class ECIAPIClient(BaseAPIClient):
    name     = "eciapi"
    base_url = settings.ECIAPI_BASE
    # No auth required

    # ── ENDPOINT 1: Get case by CNR ───────────────────────────────────────────
    async def get_case_by_cnr(self, cnr: str) -> dict:
        """
        GET /case/{cnr}
        Full case status from eCourts using the unique CNR number.
        CNR format: DLHC010001232024 (state code + court code + number + year)
        Returns: cnr, case_type, parties, advocates, status,
                 hearing_history, next_date, acts.
        """
        return await self.get(f"/case/{cnr}", use_cache=True)

    # ── ENDPOINT 2: Search by party name ─────────────────────────────────────
    async def search_by_party(self, party_name: str, court: str | None = None) -> list[dict]:
        """
        GET /search?party=...&court=...
        Find all cases where the petitioner or respondent matches.
        Returns list of matching cases with CNR numbers.
        """
        params: dict = {"party": party_name}
        if court:
            params["court"] = court
        return await self.get("/search", params=params)  # type: ignore[return-value]

    # ── ENDPOINT 3: Daily cause list ──────────────────────────────────────────
    async def get_causelist(self, court_code: str, date: str) -> list[dict]:
        """
        GET /causelist?court=...&date=...
        Today's scheduled hearings for a court.
        date format: YYYY-MM-DD
        Returns: [{cnr, case_no, parties, bench}]
        """
        return await self.get(
            "/causelist",
            params={"court": court_code, "date": date},
            use_cache=False,   # cause list changes daily
        )  # type: ignore[return-value]

    # ── ENDPOINT 4: List supported courts ─────────────────────────────────────
    async def list_courts(self) -> list[dict]:
        """
        GET /courts
        All courts supported by ECIAPI with their codes.
        Returns: [{code, name, type}]
        """
        return await self.get("/courts")  # type: ignore[return-value]
