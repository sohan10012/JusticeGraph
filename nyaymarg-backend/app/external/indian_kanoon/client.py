"""
app/external/indian_kanoon/client.py
=====================================
Indian Kanoon API v1 — the authoritative source for Indian legal documents.

• 3 crore+ documents: SC, 24 HCs, 17 Tribunals, District Courts, Central Acts
• Free for non-commercial use (₹10,000/month credits)
• Auth: API Token  Sign up: https://api.indiankanoon.org
• NyayMarg sends User-Agent: NyayMarg/2.0 (non-commercial) to qualify
"""
from __future__ import annotations

from app.config import settings
from app.external.base_client import BaseAPIClient


class IndianKanoonClient(BaseAPIClient):
    name     = "indian_kanoon"
    base_url = settings.IK_API_BASE

    def _ik_headers(self) -> dict:
        return {"Authorization": f"Token {settings.IK_API_TOKEN}"}

    # ── ENDPOINT 1: Full-text search ─────────────────────────────────────────
    async def search(
        self,
        query:   str,
        page:    int  = 0,
        doctype: str  = "judgments",
        fromdate: str | None = None,
        todate:   str | None = None,
    ) -> dict:
        """
        POST /search/
        Search across all Indian court documents.
        doctype: judgments | laws | supremecourt | delhi | bombay | ...
        Returns: {"docs": [...], "found": int, "pagenum": int}
        """
        form: dict = {
            "formInput": query,
            "pagenum":   str(page),
            "doctypes":  doctype,
        }
        if fromdate: form["fromdate"] = fromdate
        if todate:   form["todate"]   = todate

        return await self._request(
            "POST",
            f"{self.base_url}/search/",
            headers=self._ik_headers(),
            data=form,
            use_cache=True,
        )

    # ── ENDPOINT 2: Full document text ───────────────────────────────────────
    async def get_document(self, doc_id: int) -> dict:
        """
        POST /doc/{doc_id}/
        Full text (HTML) of a judgment or act by IK doc ID (tid from search).
        """
        return await self._request(
            "POST",
            f"{self.base_url}/doc/{doc_id}/",
            headers=self._ik_headers(),
            use_cache=True,
        )

    # ── ENDPOINT 3: Highlighted fragment ─────────────────────────────────────
    async def get_fragment(self, doc_id: int, query: str) -> dict:
        """
        POST /docfragment/{doc_id}/
        Returns the portions of the document that match 'query'.
        Response: {"fragment": "<highlighted HTML>"}
        """
        return await self._request(
            "POST",
            f"{self.base_url}/docfragment/{doc_id}/",
            headers=self._ik_headers(),
            data={"formInput": query},
            use_cache=True,
        )

    # ── ENDPOINT 4: Structured metadata + AI tags ─────────────────────────────
    async def get_metadata(self, doc_id: int) -> dict:
        """
        POST /docmeta/{doc_id}/
        Structured metadata without full text:
          - title, court, date, citations
          - ai_tags: AI-generated topic labels
          - structure: {facts, issues, analysis, conclusion}  [premium]
          - precedents: [{doc_id, classification: Positive|Negative|Neutral}]
        """
        return await self._request(
            "POST",
            f"{self.base_url}/docmeta/{doc_id}/",
            headers=self._ik_headers(),
            use_cache=True,
        )
