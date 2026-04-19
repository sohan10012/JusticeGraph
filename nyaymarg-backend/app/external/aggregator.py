"""
app/external/aggregator.py
============================
LegalSearchAggregator — fan-out search across all enabled legal APIs.

Runs all enabled API clients in parallel via asyncio.gather.
Normalises every source's response to UnifiedSearchResult.
Deduplicates by title similarity.
Returns a single ranked list sorted by source-confidence + recency.
"""
from __future__ import annotations

import asyncio
from typing import Any

import structlog

from app.config import settings
from app.external.indian_kanoon.schemas import UnifiedSearchResult

logger = structlog.get_logger(__name__)


class LegalSearchAggregator:
    """
    Single entry point for cross-API legal search.
    Each private _search_* method handles one source, normalises the result,
    and returns List[UnifiedSearchResult].  Individual failures are swallowed
    with a warning so one bad API doesn't kill the whole search.
    """

    async def search_all(
        self,
        query:                  str,
        include_international:  bool = False,
        max_results:            int  = 20,
    ) -> list[dict]:
        """
        Fan out to all *enabled* APIs in parallel.
        Returns normalised, deduplicated, ranked results.
        """
        tasks: list[Any] = []

        if settings.IK_ENABLED:
            tasks.append(self._search_indian_kanoon(query))
        if settings.KANOON_DEV_ENABLED:
            tasks.append(self._search_kanoon_dev(query))
        if settings.ECIAPI_ENABLED:
            tasks.append(self._search_eciapi(query))
        if settings.COURTLISTENER_ENABLED and include_international:
            tasks.append(self._search_courtlistener(query))

        if not tasks:
            logger.warning("aggregator.no_sources_enabled")
            return []

        results_lists = await asyncio.gather(*tasks, return_exceptions=True)

        unified: list[UnifiedSearchResult] = []
        for i, res in enumerate(results_lists):
            if isinstance(res, Exception):
                logger.warning("aggregator.source_failed", index=i, error=str(res))
                continue
            unified.extend(res)  # type: ignore[arg-type]

        ranked = self._deduplicate_and_rank(unified)[:max_results]
        return [r.model_dump() for r in ranked]

    # ── Source adapters ───────────────────────────────────────────────────────

    async def _search_indian_kanoon(self, query: str) -> list[UnifiedSearchResult]:
        from app.external.indian_kanoon.client import IndianKanoonClient
        client = IndianKanoonClient()
        raw    = await client.search(query, page=0)
        return [
            UnifiedSearchResult(
                source  = "indian_kanoon",
                doc_id  = str(doc.get("tid", "")),
                title   = doc.get("title", "Untitled"),
                court   = doc.get("doctype"),
                date    = doc.get("publishdate"),
                summary = doc.get("headline"),
                relevance = 0.9,   # IK returns BM25-ranked results
            )
            for doc in raw.get("docs", [])
        ]

    async def _search_kanoon_dev(self, query: str) -> list[UnifiedSearchResult]:
        from app.external.kanoon_dev.client import KanoonDevClient
        client = KanoonDevClient()
        # kanoon.dev doesn't have a free-text search — list SC cases as demo
        raw = await client.get_court_cases("sc", limit=5)
        cases = raw.get("cases", raw) if isinstance(raw, dict) else raw
        return [
            UnifiedSearchResult(
                source    = "kanoon_dev",
                doc_id    = str(c.get("id", "")),
                title     = c.get("title", c.get("case_name", "Untitled")),
                court     = c.get("court", "Supreme Court"),
                date      = c.get("date"),
                relevance = 0.7,
            )
            for c in (cases if isinstance(cases, list) else [])
        ]


    async def _search_eciapi(self, query: str) -> list[UnifiedSearchResult]:
        from app.external.ecourts.eciapi_client import ECIAPIClient
        client  = ECIAPIClient()
        raw     = await client.search_by_party(query)
        results = raw if isinstance(raw, list) else []
        return [
            UnifiedSearchResult(
                source    = "eciapi",
                doc_id    = r.get("cnr", ""),
                title     = r.get("case_title", r.get("parties", "Case")),
                court     = r.get("court"),
                date      = r.get("filing_date"),
                outcome   = r.get("status"),
                relevance = 0.75,
            )
            for r in results
        ]

    async def _search_courtlistener(self, query: str) -> list[UnifiedSearchResult]:
        from app.external.courtlistener.client import CourtListenerClient
        client = CourtListenerClient()
        raw    = await client.search_opinions(query)
        return [
            UnifiedSearchResult(
                source    = "courtlistener",
                doc_id    = str(r.get("id", "")),
                title     = r.get("caseName", "Untitled"),
                court     = r.get("court"),
                date      = r.get("dateFiled"),
                summary   = r.get("snippet"),
                relevance = 0.65,   # US data — lower weight for Indian platform
            )
            for r in raw.get("results", [])
        ]

    # ── Utility ───────────────────────────────────────────────────────────────

    def _deduplicate_and_rank(
        self, results: list[UnifiedSearchResult]
    ) -> list[UnifiedSearchResult]:
        seen:    set[str] = set()
        deduped: list[UnifiedSearchResult] = []
        for r in results:
            key = r.title[:50].lower().strip()
            if key not in seen:
                seen.add(key)
                deduped.append(r)
        # Sort by relevance desc, then date desc (None dates go last)
        return sorted(
            deduped,
            key=lambda r: (r.relevance, r.date or ""),
            reverse=True,
        )
