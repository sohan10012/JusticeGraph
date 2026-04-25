"""
app/routers/external.py
==========================
Router for all external legal API integrations.

Organised into groups:
  /ik/*          — Indian Kanoon API
  /kd/*          — kanoon.dev
  /eci/*         — ECIAPI (free, always on)
  /ecw/*         — eCourtsIndia.com (₹200 free credits)
  /gov/*         — data.gov.in
  /cl/*          — CourtListener (US)
  /search/*      — Aggregated cross-API search
"""
from __future__ import annotations

from typing import Any
import httpx
import logging
from app.services.external_service import ExternalService

router = APIRouter()
_svc = ExternalService()


def fetch_case_from_kleopatra(cnr: str):
    """
    Helper function to fetch case details from Kleopatra API.
    CNR format validation: Uppercase, ~16 characters.
    """
    # 1. Validation
    if not isinstance(cnr, str) or not cnr.isupper() or not (15 <= len(cnr) <= 17):
        return {
            "status": "invalid",
            "message": "Invalid CNR format"
        }

    url = f"https://court-api.kleopatra.io/case/{cnr}"

    # 2. Fetch with 10s timeout
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(url)

            # 3. Handle Responses
            if resp.status_code == 200:
                return {
                    "status": "success",
                    "data": resp.json()
                }
            elif resp.status_code == 404:
                return {
                    "status": "not_found",
                    "message": "Case not found in provider",
                    "cnr": cnr
                }
            else:
                logging.error(f"Kleopatra API error: {resp.status_code} for CNR {cnr}")
                return {
                    "status": "error",
                    "message": "External API failed"
                }
    except Exception as exc:
        logging.error(f"Kleopatra API connection failed: {exc}")
        return {
            "status": "error",
            "message": "External API failed"
        }


# ══════════════════════════════════════════════════════════════════════════════
# Indian Kanoon (IK)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/ik/search", summary="Search Indian Kanoon")
async def ik_search(
    q:       str          = Query(...),
    page:    int          = Query(0, ge=0),
    doctype: str  | None  = Query("judgments", description="judgments | secondary | etc"),
):
    """Search for judgments, laws, or articles on api.indiankanoon.org."""
    return await _svc.ik_search(q, page=page, doctype=doctype or "judgments")


@router.get("/ik/doc/{doc_id}", summary="Get IK document text")
async def ik_doc(doc_id: int):
    """Fetch full text of a legal document by its ID."""
    return await _svc.ik_document(doc_id)


@router.get("/ik/fragment/{doc_id}", summary="Get IK document fragment")
async def ik_fragment(doc_id: int, q: str = Query(...)):
    """Fetch matching snippet within a document for a specific query."""
    return await _svc.ik_fragment(doc_id, q)


@router.get("/ik/metadata/{doc_id}", summary="Get IK document metadata")
async def ik_metadata(doc_id: int):
    """Fetch structured metadata (citation, bench, date) for a doc."""
    return await _svc.ik_metadata(doc_id)


# ══════════════════════════════════════════════════════════════════════════════
# kanoon.dev
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/kd/courts", summary="List available courts on kanoon.dev")
async def kd_courts():
    """Returns a list of all Indian courts supported by kanoon.dev."""
    return await _svc.kd_courts()


@router.get("/kd/court/{court_id}/cases", summary="Get cases for a court")
async def kd_court_cases(court_id: str, limit: int = Query(20, ge=1, le=100)):
    """Fetch latest cases filed in a specific court."""
    return await _svc.kd_court_cases(court_id, limit=limit)


@router.get("/kd/case/{case_id}/orders", summary="Get orders for a case")
async def kd_case_orders(case_id: str):
    """Fetch all orders/judgments associated with a specific case ID."""
    return await _svc.kd_case_orders(case_id)


@router.get("/kd/case/{case_id}/insights", summary="Get AI legal insights")
async def kd_insights(case_id: str):
    """
    Get kanoon.dev AI analysis of the case, including outcomes and 
    liberty claim classification.
    """
    return await _svc.kd_insights(case_id)


# ══════════════════════════════════════════════════════════════════════════════
@router.get("/eci/case/{cnr}", summary="Get eCourts case by CNR")
async def eci_case(cnr: str):
    """
    Full case status from India's eCourts system using the CNR number.
    Uses the Kleopatra API provider.
    """
    return fetch_case_from_kleopatra(cnr)


# ══════════════════════════════════════════════════════════════════════════════
# eCourtsIndia.com (webapi.ecourtsindia.com)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/ecw/case", summary="Get case details (paid API)")
async def ecw_case(cnr: str = Query(...)):
    """Fetch full case details using the paid eCourtsIndia credit system."""
    return await _svc.ecw_case(cnr)


@router.get("/ecw/causelist", summary="Get causelist (paid API)")
async def ecw_causelist(
    court: str  = Query(...),
    date:  str  = Query(...),
    bench: str | None = None
):
    """Fetch schedule of cases via paid API credits."""
    return await _svc.ecw_causelist(court, date, bench=bench)


@router.get("/ecw/order", summary="Get case order (paid API)")
async def ecw_order(cnr: str = Query(...), order_id: str = Query(...)):
    """Download or fetch a specific order PDF/text."""
    return await _svc.ecw_order(cnr, order_id)


@router.post("/ecw/refresh/bulk", summary="Bulk refresh CNR status")
async def ecw_bulk_refresh(cnr_list: list[str]):
    """Force a refresh from eCourts for multiple cases."""
    return await _svc.ecw_bulk_refresh(cnr_list)


@router.get("/ecw/refresh/{cnr}", summary="Force refresh single case")
async def ecw_force_refresh(cnr: str):
    """Force a live update for a single case."""
    return await _svc.ecw_force_refresh(cnr)


@router.get("/ecw/enums", summary="Get court/state metadata")
async def ecw_enums():
    """Returns mapping for state/district/court codes used in paid API."""
    return await _svc.ecw_enums()


# ══════════════════════════════════════════════════════════════════════════════
# data.gov.in (OGD Platform)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/gov/infrastructure", summary="Get judicial infrastructure stats")
async def gov_infrastructure(state: str | None = None):
    """Fetch OGD data on court buildings, computerisation, and staffing."""
    return await _svc.gov_infrastructure(state=state)


@router.get("/gov/pendency", summary="Get case pendency stats")
async def gov_pendency(state: str | None = None):
    """Fetch official government data on case backlogs across states."""
    return await _svc.gov_pendency(state=state)


@router.get("/gov/disposal", summary="Get case disposal rates")
async def gov_disposal(year: int | None = Query(None, ge=2000)):
    """Fetch yearly rates of case resolution."""
    return await _svc.gov_disposal(year=year)


# ══════════════════════════════════════════════════════════════════════════════
# CourtListener (International / Reference)
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/cl/search", summary="Search CourtListener opinions")
async def cl_search(q: str = Query(...), court: str | None = None):
    """Search US legal opinions for international precedent comparison."""
    return await _svc.cl_search(q, court=court)


@router.get("/cl/opinion/{opinion_id}", summary="Get CL legal opinion")
async def cl_opinion(opinion_id: int):
    """Fetch full text of a CourtListener opinion."""
    return await _svc.cl_opinion(opinion_id)


@router.get("/cl/docket/{docket_id}", summary="Get CL docket entries")
async def cl_docket(docket_id: int):
    """Fetch history of filings for a US case."""
    return await _svc.cl_docket(docket_id)


@router.get("/cl/judge/{judge_id}", summary="Get CL judge bio")
async def cl_judge(judge_id: int):
    """Fetch biographic and career metadata for a judge."""
    return await _svc.cl_judge(judge_id)


@router.get("/cl/citations/{opinion_id}", summary="Get CL citations")
async def cl_citations(opinion_id: int):
    """Fetch list of cases cited by or citing this opinion."""
    return await _svc.cl_citations(opinion_id)


# ══════════════════════════════════════════════════════════════════════════════
# Aggregated & Utility Operations
# ══════════════════════════════════════════════════════════════════════════════

@router.get("/search/all", summary="Search across all legal APIs")
async def search_all(
    q:    str  = Query(...),
    intl: bool = Query(False, description="Include international results (CourtListener)"),
    max:  int  = Query(20, ge=1, le=100),
):
    """
    Fan-out search to all enabled Indian & Global APIs.
    Normalises and deduplicates results into a unified ranked list.
    """
    return await _svc.fan_out_search(q, include_international=intl, max_results=max)


@router.post("/case/{case_id}/enrich", summary="Enrich synthetic case with real data")
async def enrich_case(case_id: str):
    """
    Search for a real-world counterpart of a NyayMarg synthetic case on Indian Kanoon.
    If found, enriches the synthetic record with real judgment text and AI tags.
    """
    return await _svc.enrich_case(case_id)


@router.post("/ik/import", summary="Import real cases into analytics")
async def import_ik_cases(query: str = Query(...), count: int = Query(50, ge=1, le=200)):
    """
    Queues a background task to import real judgments from IK into the platform 
    similarity index. Triggers an async Celery worker.
    """
    return await _svc.import_ik_cases(query, max_cases=count)
