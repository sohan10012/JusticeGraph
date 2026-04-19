"""
app/external/courtlistener/client.py
=======================================
CourtListener REST API v4 — US federal + state court data.

Free with token. Register at https://courtlistener.com
Millions of opinions, dockets, judge profiles, oral argument audio.
Useful for NyayMarg's comparative legal research and international precedent features.

Rate limits vary by tier. Docs: https://www.courtlistener.com/help/api/rest/
"""
from __future__ import annotations

from app.config import settings
from app.external.base_client import BaseAPIClient


class CourtListenerClient(BaseAPIClient):
    name     = "courtlistener"
    base_url = settings.COURTLISTENER_BASE

    def _headers(self) -> dict:
        return {"Authorization": f"Token {settings.COURTLISTENER_TOKEN}"}

    # ── ENDPOINT 1: Search opinions ───────────────────────────────────────────
    async def search_opinions(self, query: str, court: str | None = None) -> dict:
        """
        GET /search/?type=o&q=...
        Full-text search across millions of US legal opinions.
        Returns: {count, results: [{caseName, dateFiled, court, citation, snippet}]}
        """
        params: dict = {"type": "o", "q": query, "format": "json"}
        if court:
            params["court"] = court
        return await self.get("/search/", headers=self._headers(), params=params)

    # ── ENDPOINT 2: Get single opinion ────────────────────────────────────────
    async def get_opinion(self, opinion_id: int) -> dict:
        """
        GET /opinions/{opinion_id}/
        Full opinion: text, citations, judges, case name, date.
        """
        return await self.get(f"/opinions/{opinion_id}/", headers=self._headers())

    # ── ENDPOINT 3: Get docket ────────────────────────────────────────────────
    async def get_docket(self, docket_id: int) -> dict:
        """
        GET /dockets/{docket_id}/
        Full case docket: all filings, parties, attorneys, history.
        """
        return await self.get(f"/dockets/{docket_id}/", headers=self._headers())

    # ── ENDPOINT 4: Get judge profile ─────────────────────────────────────────
    async def get_judge(self, judge_id: int) -> dict:
        """
        GET /people/{judge_id}/
        Judge profile: education, positions, career, financial disclosures.
        """
        return await self.get(f"/people/{judge_id}/", headers=self._headers())

    # ── ENDPOINT 5: List courts ───────────────────────────────────────────────
    async def list_courts(self) -> dict:
        """GET /courts/ — All US courts indexed by CourtListener."""
        return await self.get("/courts/", headers=self._headers())

    # ── ENDPOINT 6: Citation network ──────────────────────────────────────────
    async def get_citations(self, opinion_id: int) -> dict:
        """
        GET /citations/?document={opinion_id}
        Forward citations (who cites this opinion) +
        backward citations (what this opinion cites).
        Useful for citation network analysis and precedent strength scoring.
        """
        return await self.get(
            "/citations/",
            headers=self._headers(),
            params={"document": opinion_id},
        )

    # ── ENDPOINT 7: Create case alert (webhook) ────────────────────────────────
    async def create_alert(self, query: str, name: str) -> dict:
        """
        POST /alerts/
        Subscribe to daily email/webhook alerts when new cases match a query.
        """
        return await self.post(
            "/alerts/",
            headers=self._headers(),
            json={"query": query, "name": name, "rate": "dly"},
            use_cache=False,
        )
