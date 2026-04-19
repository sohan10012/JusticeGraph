"""
app/external/data_gov/client.py
==================================
data.gov.in — Open Government Data Platform India.

100% free. Register at https://data.gov.in for an API key.
Provides official Ministry of Law & Justice judiciary statistics:
  - Court infrastructure by state
  - NJDG pendency figures
  - District-wise disposal rates
  - Judge strength data
"""
from __future__ import annotations

from app.config import settings
from app.external.base_client import BaseAPIClient

# Official resource IDs on data.gov.in (verified public datasets)
_RES_COURT_INFRA    = "b031d51c-e7db-4ef6-a47a-08ee97fd9f62"
_RES_PENDENCY       = "2c9b3831-9f07-4c73-b2b2-5e1d6dcf3f22"
_RES_DISPOSAL_RATES = "b031d51c-disposal-rates-placeholder"   # update with real ID


class DataGovClient(BaseAPIClient):
    name     = "data_gov"
    base_url = settings.DATA_GOV_BASE

    def _base_params(self, offset: int = 0, limit: int = 100) -> dict:
        return {
            "api-key": settings.DATA_GOV_API_KEY,
            "format":  "json",
            "offset":  offset,
            "limit":   limit,
        }

    # ── ENDPOINT 1: Court infrastructure by state ─────────────────────────────
    async def get_court_infrastructure(
        self, offset: int = 0, limit: int = 100
    ) -> dict:
        """
        GET /resource/{resource_id}?api-key=...
        Returns: court count, judge strength, pending cases by state.
        Source: Ministry of Law and Justice
        """
        return await self.get(
            f"/{_RES_COURT_INFRA}",
            params=self._base_params(offset, limit),
        )

    # ── ENDPOINT 2: Pendency statistics ──────────────────────────────────────
    async def get_pendency_stats(self, state: str | None = None) -> dict:
        """
        GET /resource/{resource_id}
        State-wise and court-type-wise pending case counts.
        Updated periodically from NJDG (National Judicial Data Grid) exports.
        """
        params = self._base_params()
        if state:
            params["filters[state]"] = state
        return await self.get(f"/{_RES_PENDENCY}", params=params)

    # ── ENDPOINT 3: Disposal rates by district ────────────────────────────────
    async def get_disposal_rates(self, year: int | None = None) -> dict:
        """
        GET /resource/{resource_id}
        District-wise annual disposal rates and institution rates.
        """
        params = self._base_params(limit=200)
        if year:
            params["filters[year]"] = str(year)
        return await self.get(f"/{_RES_DISPOSAL_RATES}", params=params)
