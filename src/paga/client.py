"""Async client for the Paga Engine API."""

from __future__ import annotations

import asyncio
import json
import time
from typing import Any, Dict, Mapping, Optional, Union

import httpx

from .actions import ActionMixin
from .auth import (
    DEFAULT_HASH_ALGORITHM,
    PAYMENT_REQUEST_HASH_FIELDS,
    PagaAuth,
    generate_hash,
)
from .business import BusinessMixin
from .checkout import CheckoutMixin
from .customer import CustomerMixin
from .direct_debit import DirectDebitMixin
from .directory import DirectoryMixin
from .exceptions import PagaAPIError, PagaAuthenticationError, PagaRateLimitError
from .models import PagaResponse
from .persistent import PersistentPaymentAccountMixin

DEFAULT_COLLECT_TEST_BASE_URL = "https://beta-collect.paga.com"
DEFAULT_COLLECT_LIVE_BASE_URL = "https://collect.paga.com"
DEFAULT_CHECKOUT_TEST_BASE_URL = "https://beta-checkout.paga.com"
DEFAULT_CHECKOUT_LIVE_BASE_URL = "https://checkout.paga.com"
DEFAULT_BUSINESS_TEST_BASE_URL = "https://beta.mypaga.com/paga-webservices/business-rest/secured"
DEFAULT_BUSINESS_LIVE_BASE_URL = "https://www.mypaga.com/paga-webservices/business-rest/secured"

# A multipart part carrying a JSON document.
JsonPart = Dict[str, Any]
# A multipart part carrying a file: the bytes, and optionally a filename and
# a content type.
FilePart = Union[bytes, bytearray, "tuple[Optional[str], bytes, Optional[str]]"]


class PagaClient(
    CheckoutMixin,
    ActionMixin,
    BusinessMixin,
    DirectoryMixin,
    DirectDebitMixin,
    PersistentPaymentAccountMixin,
    CustomerMixin,
):
    """Async client for the Paga Engine API.

    Combines the checkout, action, business / subsidiary, directory, Direct
    Debit, persistent payment account and customer registration operation
    mixins and owns the shared async HTTP plumbing (auth, hashing, errors,
    base URLs).
    """

    def __init__(
        self,
        public_id: str,
        credentials: str,
        hash_key: str,
        *,
        environment: str = "test",
        base_url: Optional[str] = None,
        checkout_base_url: Optional[str] = None,
        business_base_url: Optional[str] = None,
        timeout: float = 30.0,
        max_retries: int = 0,
        retry_backoff: float = 0.5,
    ) -> None:
        if environment not in {"test", "live"}:
            raise ValueError("environment must be either 'test' or 'live'")

        self.public_id = public_id
        self.credentials = credentials
        self.hash_key = hash_key
        self.environment = environment
        self.base_url = base_url or (
            DEFAULT_COLLECT_TEST_BASE_URL if environment == "test" else DEFAULT_COLLECT_LIVE_BASE_URL
        )
        self.checkout_base_url = checkout_base_url or (
            DEFAULT_CHECKOUT_TEST_BASE_URL if environment == "test" else DEFAULT_CHECKOUT_LIVE_BASE_URL
        )
        self.business_base_url = business_base_url or (
            DEFAULT_BUSINESS_TEST_BASE_URL if environment == "test" else DEFAULT_BUSINESS_LIVE_BASE_URL
        )
        self.timeout = httpx.Timeout(timeout)
        self.max_retries = max(0, int(max_retries))
        self.retry_backoff = float(retry_backoff)
        self.auth = PagaAuth(public_id=public_id, credentials=credentials, hash_key=hash_key)
        self._http: Optional[httpx.AsyncClient] = None

    @property
    def baseUrl(self) -> str:
        """Base URL of the targeted Paga (collect) environment."""
        return self.base_url

    @property
    def checkoutBaseUrl(self) -> str:
        """Base URL of the targeted Paga (checkout) environment."""
        return self.checkout_base_url

    async def __aenter__(self) -> "PagaClient":
        self._http = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001, ANN002
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=self.timeout)
        return self._http

    async def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Mapping[str, Any]] = None,
        *,
        use_hash: bool = True,
        use_basic: bool = False,
        base_url: Optional[str] = None,
        hash_fields: Optional[tuple] = None,
        raise_on_error: bool = True,
        params: Optional[Mapping[str, Any]] = None,
        hash_payload: Optional[Mapping[str, Any]] = None,
    ) -> PagaResponse:
        """Execute a request against the Paga Engine API.

        Args:
            method: HTTP method (e.g. ``"POST"``, ``"GET"``).
            path: Endpoint path relative to the base URL
                (e.g. ``/paymentRequest``, ``/checkout/transaction/verify``).
            payload: Optional JSON request body.
            use_hash: Use Paga hash-based auth headers. Defaults to ``True``.
            use_basic: Use HTTP Basic auth (public key / secret key) instead of
                the header based auth. Defaults to ``False``.
            base_url: Override the target base URL. Defaults to the collect base URL.
            hash_fields: Ordered hash field paths used when computing the hash.
            raise_on_error: Raise on unsuccessful operation responses. Defaults to
                ``True``.
            hash_payload: The payload the hash is computed over, when it is
                not the request body. Used by operations that sign fields the
                body does not carry.

        Returns:
            The parsed :class:`PagaResponse`.

        Raises:
            PagaAuthenticationError: If Paga rejects the credentials.
            PagaAPIError: If the API responds with a failure.
        """
        target_base = (base_url or self.base_url).rstrip("/")
        url = f"{target_base}{path}"
        http = await self._ensure_client()

        signed = hash_payload if hash_payload is not None else payload

        auth = self.auth.basic_auth() if use_basic else None
        headers: Optional[Dict[str, str]] = None
        if use_basic:
            if use_hash and signed is not None:
                headers = {
                    "hash": generate_hash(
                        signed,
                        self.hash_key,
                        algorithm=DEFAULT_HASH_ALGORITHM,
                        fields=hash_fields or PAYMENT_REQUEST_HASH_FIELDS,
                    ),
                }
        elif use_hash and signed is not None:
            headers = self.auth.build_headers(signed, hash_fields=hash_fields)

        request_kwargs: Dict[str, Any] = {
            "method": method.upper(),
            "url": url,
            "auth": auth,
        }
        if headers is not None:
            request_kwargs["headers"] = headers
        if params is not None:
            request_kwargs["params"] = params
        # GET requests carry no body; hash-relevant values travel in query params.
        if payload is not None and method.upper() != "GET":
            request_kwargs["json"] = dict(payload)
        response = await self._send(http, request_kwargs)

        if response.status_code in (401, 403):
            raise PagaAuthenticationError(
                f"Paga authentication failed with status {response.status_code}"
            )
        if response.status_code >= 400:
            raise self._to_api_error(response)

        body: Any = response.json() if response.content else {}
        result = PagaResponse.model_validate(body)
        if raise_on_error and not result.is_success:
            raise PagaAPIError(
                message=result.message or "Paga request failed",
                response_code=result.responseCode,
                payload=result,
            )
        return result

    async def _multipart_request(
        self,
        method: str,
        path: str,
        parts: Mapping[str, Any],
        *,
        hash_payload: Optional[Mapping[str, Any]] = None,
        hash_fields: Optional[tuple] = None,
        base_url: Optional[str] = None,
        raise_on_error: bool = True,
    ) -> PagaResponse:
        """Execute a multipart/form-data request against the Paga Engine API.

        Paga's customer registration endpoints take a JSON part plus one or
        two image parts. The hash is computed over the JSON part, not over
        the multipart envelope.

        Args:
            method: HTTP method.
            path: Endpoint path relative to the base URL.
            parts: The multipart parts. A ``dict`` value becomes a JSON
                part; ``bytes`` or a ``(filename, bytes, content_type)``
                tuple becomes a file part.
            hash_payload: The payload the hash is computed over. Defaults to
                the JSON part, when there is exactly one.
            hash_fields: Ordered hash field paths used when computing the hash.
            base_url: Override the target base URL. Defaults to the business
                base URL.
            raise_on_error: Raise on unsuccessful operation responses.

        Returns:
            The parsed :class:`PagaResponse`.
        """
        target_base = (base_url or self.business_base_url).rstrip("/")
        url = f"{target_base}{path}"
        http = await self._ensure_client()

        files: Dict[str, Any] = {}
        json_parts: Dict[str, Any] = {}
        for name, value in parts.items():
            if isinstance(value, dict):
                files[name] = (None, json.dumps(value), "application/json")
                json_parts[name] = value
            elif isinstance(value, (bytes, bytearray)):
                files[name] = ("upload", bytes(value), "application/octet-stream")
            else:
                filename, content, content_type = value
                files[name] = (filename, content, content_type)

        if hash_payload is None and len(json_parts) == 1:
            hash_payload = next(iter(json_parts.values()))

        headers: Optional[Dict[str, str]] = None
        if hash_payload is not None:
            headers = self.auth.build_headers(hash_payload, hash_fields=hash_fields)

        request_kwargs: Dict[str, Any] = {
            "method": method.upper(),
            "url": url,
            "files": files,
        }
        if headers is not None:
            request_kwargs["headers"] = headers
        response = await self._send(http, request_kwargs)

        if response.status_code in (401, 403):
            raise PagaAuthenticationError(
                f"Paga authentication failed with status {response.status_code}"
            )
        if response.status_code >= 400:
            raise self._to_api_error(response)

        body: Any = response.json() if response.content else {}
        result = PagaResponse.model_validate(body)
        if raise_on_error and not result.is_success:
            raise PagaAPIError(
                message=result.message or "Paga request failed",
                response_code=result.responseCode,
                payload=result,
            )
        return result

    async def _send(
        self,
        http: httpx.AsyncClient,
        request_kwargs: Dict[str, Any],
    ) -> httpx.Response:
        """Send a request, retrying rate-limited calls when enabled.

        Only HTTP 429 is retried. A rate-limited request was rejected before
        Paga processed it, so replaying it is safe. Server errors are
        **not** retried: a 5xx or a timeout leaves the outcome unknown, and
        Paga's guidance is to check the transaction status with the original
        reference number rather than to send again.
        """
        attempt = 0
        while True:
            response = await http.request(**request_kwargs)
            if response.status_code != 429 or attempt >= self.max_retries:
                return response
            delay = self._retry_delay(response, attempt)
            await asyncio.sleep(delay)
            attempt += 1

    def _retry_delay(self, response: httpx.Response, attempt: int) -> float:
        """Seconds to wait before the next attempt."""
        retry_after = response.headers.get("retry-after")
        if retry_after:
            try:
                return float(retry_after)
            except ValueError:
                pass
        return self.retry_backoff * (2**attempt)

    def _to_api_error(self, response: httpx.Response) -> PagaAPIError:
        try:
            body: Any = response.json()
        except Exception:  # noqa: BLE001 - response may not be JSON
            body = {}

        message = body.get("message") if isinstance(body, dict) else None
        response_code = body.get("responseCode") if isinstance(body, dict) else None

        if response.status_code == 429:
            return PagaRateLimitError(
                message=message or "Paga rate limit exceeded",
                response_code=response_code if isinstance(response_code, int) else None,
                status_code=response.status_code,
                payload=body,
            )

        return PagaAPIError(
            message=message or f"Paga API returned status {response.status_code}",
            response_code=response_code if isinstance(response_code, int) else None,
            status_code=response.status_code,
            payload=body,
        )
