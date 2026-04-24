"""
app/external/base_client.py
============================
Shared async HTTP foundation for all external legal API clients.

Features:
  - Exponential-backoff retry (tenacity)
  - Per-client TTL response cache (cachetools)
  - Consistent timeout + error logging
  - NyayMarg User-Agent header (qualifies for IK non-commercial free tier)
"""
from __future__ import annotations

import hashlib
import json
import time
from typing import Any

import httpx
import structlog
from cachetools import TTLCache
from tenacity import (
    AsyncRetrying,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.config import settings

logger = structlog.get_logger(__name__)

# ── Global shared cache ───────────────────────────────────────────────────────
_RESPONSE_CACHE: TTLCache = TTLCache(
    maxsize=500,
    ttl=settings.EXTERNAL_API_CACHE_TTL_SECONDS,
)

_RETRYABLE = (httpx.TimeoutException, httpx.ConnectError, httpx.RemoteProtocolError)

BASE_HEADERS = {
    "User-Agent": "NyayMarg/2.0 (non-commercial; legal-analytics)",
    "Accept":     "application/json",
}


class BaseAPIClient:
    """
    Async HTTP client base class.
    All external API clients inherit from this.
    """

    name:     str = "base"
    base_url: str = ""
    timeout:  int = settings.EXTERNAL_API_TIMEOUT_SECONDS

    def _cache_key(self, method: str, url: str, **kwargs) -> str:
        raw = json.dumps({"m": method, "u": url, **kwargs}, sort_keys=True)
        return hashlib.md5(raw.encode()).hexdigest()  # noqa: S324

    async def _request(
        self,
        method:   str,
        url:      str,
        *,
        use_cache: bool = True,
        **kwargs: Any,
    ) -> dict | list:
        """
        Make an HTTP request with retry, caching, and structured logging.
        Returns parsed JSON or raises HTTPStatusError.
        """
        cache_key = self._cache_key(method, url, **kwargs)

        if use_cache and cache_key in _RESPONSE_CACHE:
            logger.debug("external.cache_hit", source=self.name, url=url)
            return _RESPONSE_CACHE[cache_key]  # type: ignore[return-value]

        start = time.monotonic()
        try:
            async for attempt in AsyncRetrying(
                stop=stop_after_attempt(settings.EXTERNAL_API_MAX_RETRIES),
                wait=wait_exponential(multiplier=1, min=1, max=10),
                retry=retry_if_exception_type(_RETRYABLE),
                reraise=True,
            ):
                with attempt:
                    # Don't pop from kwargs inside the retry loop as it mutates it for subsequent attempts
                    headers = {**BASE_HEADERS, **kwargs.get("headers", {})}
                    req_kwargs = {k: v for k, v in kwargs.items() if k != "headers"}

                    async with httpx.AsyncClient(
                        timeout=self.timeout,
                        follow_redirects=True,
                    ) as client:
                        resp = await client.request(
                            method, url,
                            headers=headers,
                            **req_kwargs,
                        )
                        resp.raise_for_status()
                        data = resp.json()

                        elapsed = round(time.monotonic() - start, 3)
                        logger.info(
                            "external.request_ok",
                            source=self.name,
                            url=url,
                            status=resp.status_code,
                            elapsed_s=elapsed,
                        )

                        if use_cache:
                            _RESPONSE_CACHE[cache_key] = data
                        return data  # type: ignore[return-value]

        except httpx.HTTPStatusError as exc:
            msg = exc.response.text[:200]
            logger.warning(
                "external.http_error",
                source=self.name,
                url=url,
                status=exc.response.status_code,
                detail=msg,
            )
            return {
                "error": f"External API {self.name} returned {exc.response.status_code}",
                "detail": msg,
                "url": url
            }
        except json.JSONDecodeError as exc:
            logger.error("external.json_error", source=self.name, url=url, error=str(exc))
            return {
                "error": f"External API {self.name} returned non-JSON response",
                "detail": str(exc),
                "url": url
            }
        except Exception as exc:
            logger.error("external.request_failed", source=self.name, url=url, error=str(exc))
            return {
                "error": f"External API {self.name} request failed",
                "detail": str(exc),
                "url": url
            }

    async def get(self, path: str, *, params: dict | None = None, **kw) -> Any:
        return await self._request("GET", f"{self.base_url}{path}", params=params, **kw)

    async def post(self, path: str, *, data: dict | None = None, json: dict | None = None, **kw) -> Any:
        return await self._request("POST", f"{self.base_url}{path}", data=data, json=json, **kw)
