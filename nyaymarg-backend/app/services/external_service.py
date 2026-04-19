"""
app/services/external_service.py
==================================
Business logic for all external legal API operations.

Responsibilities:
  - Proxy calls to the appropriate API client
  - Enforce ENABLED flag before calling (fallback to empty list)
  - Integrate real IK results into the similarity index
  - Enrich synthetic cases with real judgment text
"""
from __future__ import annotations

import asyncio
from typing import Any

import structlog

from app.config import settings
from app.external.aggregator import LegalSearchAggregator

logger = structlog.get_logger(__name__)
aggregator = LegalSearchAggregator()


def _disabled(api: str) -> dict:
    return {"error": f"{api} integration is disabled. Set {api.upper()}_ENABLED=True in .env."}


class ExternalService:

    # ══ Indian Kanoon ═════════════════════════════════════════════════════════

    async def ik_search(self, query: str, page: int = 0, doctype: str = "judgments") -> dict:
        if not settings.IK_ENABLED:
            return _disabled("IK")
        from app.external.indian_kanoon.client import IndianKanoonClient
        return await IndianKanoonClient().search(query, page=page, doctype=doctype)

    async def ik_document(self, doc_id: int) -> dict:
        if not settings.IK_ENABLED:
            return _disabled("IK")
        from app.external.indian_kanoon.client import IndianKanoonClient
        return await IndianKanoonClient().get_document(doc_id)

    async def ik_fragment(self, doc_id: int, query: str) -> dict:
        if not settings.IK_ENABLED:
            return _disabled("IK")
        from app.external.indian_kanoon.client import IndianKanoonClient
        return await IndianKanoonClient().get_fragment(doc_id, query)

    async def ik_metadata(self, doc_id: int) -> dict:
        if not settings.IK_ENABLED:
            return _disabled("IK")
        from app.external.indian_kanoon.client import IndianKanoonClient
        return await IndianKanoonClient().get_metadata(doc_id)

    # ══ kanoon.dev ════════════════════════════════════════════════════════════

    async def kd_courts(self) -> Any:
        if not settings.KANOON_DEV_ENABLED:
            return _disabled("KANOON_DEV")
        from app.external.kanoon_dev.client import KanoonDevClient
        return await KanoonDevClient().list_courts()

    async def kd_court_cases(self, court_id: str, limit: int = 20) -> Any:
        if not settings.KANOON_DEV_ENABLED:
            return _disabled("KANOON_DEV")
        from app.external.kanoon_dev.client import KanoonDevClient
        return await KanoonDevClient().get_court_cases(court_id, limit=limit)

    async def kd_case_orders(self, case_id: str) -> Any:
        if not settings.KANOON_DEV_ENABLED:
            return _disabled("KANOON_DEV")
        from app.external.kanoon_dev.client import KanoonDevClient
        return await KanoonDevClient().get_case_orders(case_id)

    async def kd_insights(self, case_id: str) -> Any:
        if not settings.KANOON_DEV_ENABLED:
            return _disabled("KANOON_DEV")
        from app.external.kanoon_dev.client import KanoonDevClient
        return await KanoonDevClient().get_insights(case_id)

    # ══ ECIAPI (always enabled by default) ═══════════════════════════════════

    async def eci_case(self, cnr: str) -> Any:
        if not settings.ECIAPI_ENABLED:
            return _disabled("ECIAPI")
        from app.external.ecourts.eciapi_client import ECIAPIClient
        return await ECIAPIClient().get_case_by_cnr(cnr)

    async def eci_search(self, party: str, court: str | None = None) -> Any:
        if not settings.ECIAPI_ENABLED:
            return _disabled("ECIAPI")
        from app.external.ecourts.eciapi_client import ECIAPIClient
        return await ECIAPIClient().search_by_party(party, court=court)

    async def eci_causelist(self, court_code: str, date: str) -> Any:
        if not settings.ECIAPI_ENABLED:
            return _disabled("ECIAPI")
        from app.external.ecourts.eciapi_client import ECIAPIClient
        return await ECIAPIClient().get_causelist(court_code, date)

    async def eci_courts(self) -> Any:
        if not settings.ECIAPI_ENABLED:
            return _disabled("ECIAPI")
        from app.external.ecourts.eciapi_client import ECIAPIClient
        return await ECIAPIClient().list_courts()

    # ══ eCourtsIndia.com ═════════════════════════════════════════════════════

    async def ecw_case(self, cnr: str) -> Any:
        if not settings.ECOURTSINDIA_ENABLED:
            return _disabled("ECOURTSINDIA")
        from app.external.ecourts.ecourtsindia_client import ECourtsIndiaClient
        return await ECourtsIndiaClient().get_case(cnr)

    async def ecw_causelist(self, court: str, date: str, bench: str | None = None) -> Any:
        if not settings.ECOURTSINDIA_ENABLED:
            return _disabled("ECOURTSINDIA")
        from app.external.ecourts.ecourtsindia_client import ECourtsIndiaClient
        return await ECourtsIndiaClient().get_causelist(court, date, bench=bench)

    async def ecw_order(self, cnr: str, order_id: str) -> Any:
        if not settings.ECOURTSINDIA_ENABLED:
            return _disabled("ECOURTSINDIA")
        from app.external.ecourts.ecourtsindia_client import ECourtsIndiaClient
        return await ECourtsIndiaClient().get_order(cnr, order_id)

    async def ecw_bulk_refresh(self, cnr_list: list[str]) -> Any:
        if not settings.ECOURTSINDIA_ENABLED:
            return _disabled("ECOURTSINDIA")
        from app.external.ecourts.ecourtsindia_client import ECourtsIndiaClient
        return await ECourtsIndiaClient().bulk_refresh(cnr_list)

    async def ecw_force_refresh(self, cnr: str) -> Any:
        if not settings.ECOURTSINDIA_ENABLED:
            return _disabled("ECOURTSINDIA")
        from app.external.ecourts.ecourtsindia_client import ECourtsIndiaClient
        return await ECourtsIndiaClient().force_refresh(cnr)

    async def ecw_enums(self) -> Any:
        if not settings.ECOURTSINDIA_ENABLED:
            return _disabled("ECOURTSINDIA")
        from app.external.ecourts.ecourtsindia_client import ECourtsIndiaClient
        return await ECourtsIndiaClient().get_enums()

    # ══ data.gov.in ══════════════════════════════════════════════════════════

    async def gov_infrastructure(self, state: str | None = None) -> Any:
        if not settings.DATA_GOV_ENABLED:
            return _disabled("DATA_GOV")
        from app.external.data_gov.client import DataGovClient
        return await DataGovClient().get_court_infrastructure()

    async def gov_pendency(self, state: str | None = None) -> Any:
        if not settings.DATA_GOV_ENABLED:
            return _disabled("DATA_GOV")
        from app.external.data_gov.client import DataGovClient
        return await DataGovClient().get_pendency_stats(state=state)

    async def gov_disposal(self, year: int | None = None) -> Any:
        if not settings.DATA_GOV_ENABLED:
            return _disabled("DATA_GOV")
        from app.external.data_gov.client import DataGovClient
        return await DataGovClient().get_disposal_rates(year=year)

    # ══ CourtListener ════════════════════════════════════════════════════════

    async def cl_search(self, query: str, court: str | None = None) -> Any:
        if not settings.COURTLISTENER_ENABLED:
            return _disabled("COURTLISTENER")
        from app.external.courtlistener.client import CourtListenerClient
        return await CourtListenerClient().search_opinions(query, court=court)

    async def cl_opinion(self, opinion_id: int) -> Any:
        if not settings.COURTLISTENER_ENABLED:
            return _disabled("COURTLISTENER")
        from app.external.courtlistener.client import CourtListenerClient
        return await CourtListenerClient().get_opinion(opinion_id)

    async def cl_docket(self, docket_id: int) -> Any:
        if not settings.COURTLISTENER_ENABLED:
            return _disabled("COURTLISTENER")
        from app.external.courtlistener.client import CourtListenerClient
        return await CourtListenerClient().get_docket(docket_id)

    async def cl_judge(self, judge_id: int) -> Any:
        if not settings.COURTLISTENER_ENABLED:
            return _disabled("COURTLISTENER")
        from app.external.courtlistener.client import CourtListenerClient
        return await CourtListenerClient().get_judge(judge_id)

    async def cl_citations(self, opinion_id: int) -> Any:
        if not settings.COURTLISTENER_ENABLED:
            return _disabled("COURTLISTENER")
        from app.external.courtlistener.client import CourtListenerClient
        return await CourtListenerClient().get_citations(opinion_id)

    # ══ Aggregated operations ═════════════════════════════════════════════════

    async def fan_out_search(
        self,
        query:                 str,
        include_international: bool = False,
        max_results:           int  = 20,
    ) -> list[dict]:
        """Fan-out to all enabled APIs and return unified ranked results."""
        return await aggregator.search_all(
            query,
            include_international=include_international,
            max_results=max_results,
        )

    async def enrich_case(self, case_id: str) -> dict:
        """
        Find real counterpart of a NyayMarg synthetic case on Indian Kanoon.
        Fetches AI tags + structure for enrichment.
        Returns enriched metadata or {"enriched": False} if not found.
        """
        from app.data.seed import get_registry
        from app.external.indian_kanoon.client import IndianKanoonClient

        if not settings.IK_ENABLED:
            return {"enriched": False, "reason": "IK disabled"}

        registry = get_registry()
        df       = registry.df_cases
        row      = df[df["case_id"] == case_id]
        if row.empty:
            return {"enriched": False, "reason": "case not found"}

        query  = row.iloc[0].get("clean_text", "")[:100]
        client = IndianKanoonClient()

        try:
            results = await client.search(query, page=0)
            docs    = results.get("docs", [])
            if not docs:
                return {"enriched": False, "reason": "no IK match"}
            top = docs[0]
            meta = await client.get_metadata(top["tid"])
            return {"enriched": True, "ik_doc_id": top["tid"], **meta}
        except Exception as exc:
            logger.warning("enrich.failed", case_id=case_id, error=str(exc))
            return {"enriched": False, "reason": str(exc)}

    async def import_ik_cases(self, query: str, max_cases: int = 50) -> dict:
        """
        Import real IK cases into the similarity index.
        Background-friendly: returns immediately with count of queued cases.
        The actual import runs in a Celery task.
        """
        from app.tasks.training_tasks import import_ik_cases_task  # type: ignore[import]
        task = import_ik_cases_task.delay(query, max_cases)
        return {"job_id": task.id, "status": "queued", "query": query, "max_cases": max_cases}
