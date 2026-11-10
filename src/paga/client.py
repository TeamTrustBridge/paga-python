"""Async client for the Paga Engine API."""

from __future__ import annotations

from typing import Any, Dict, Mapping, Optional

import httpx

from .auth import (
    DEFAULT_HASH_ALGORITHM,
    PAYMENT_REQUEST_HASH_FIELDS,
    PagaAuth,
    generate_hash,
)
from .exceptions import PagaAPIError, PagaAuthenticationError, PagaRateLimitError
from .models import (
    CheckoutVerifyChargeResponse,
    CollectPaymentRequestResponse,
    PagaResponse,
)

DEFAULT_COLLECT_TEST_BASE_URL = "https://beta-collect.paga.com"
DEFAULT_COLLECT_LIVE_BASE_URL = "https://collect.paga.com"
DEFAULT_CHECKOUT_TEST_BASE_URL = "https://beta-checkout.paga.com"
DEFAULT_CHECKOUT_LIVE_BASE_URL = "https://checkout.paga.com"


class PagaClient:
    """Async-first client for the Paga Engine API.

    The client is intended to be used as an async context manager::

        async with PagaClient(
            public_id="...",
            credentials="...",
            hash_key="...",
        ) as client:
            payment = await client.create_payment({...})
            verified = await client.verify_charge({...})

    All operations return typed responses on success and raise
    :class:`PagaAPIError` (or subclasses) when Paga reports a failure.
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
        timeout: float = 30.0,
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
        self.timeout = httpx.Timeout(timeout)
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

        Returns:
            The parsed :class:`PagaResponse`.

        Raises:
            PagaAuthenticationError: If Paga rejects the credentials.
            PagaAPIError: If the API responds with a failure.
        """
        target_base = (base_url or self.base_url).rstrip("/")
        url = f"{target_base}{path}"
        http = await self._ensure_client()

        auth = self.auth.basic_auth() if use_basic else None
        headers: Optional[Dict[str, str]] = None
        if use_basic:
            if use_hash and payload is not None:
                headers = {
                    "hash": generate_hash(
                        payload,
                        self.hash_key,
                        algorithm=DEFAULT_HASH_ALGORITHM,
                        fields=hash_fields or PAYMENT_REQUEST_HASH_FIELDS,
                    ),
                }
        elif use_hash and payload is not None:
            headers = self.auth.build_headers(payload, hash_fields=hash_fields)

        response = await http.request(
            method=method.upper(),
            url=url,
            json=dict(payload) if payload is not None else None,
            headers=headers,
            auth=auth,
        )

        if response.status_code in (401, 403):
            raise PagaAuthenticationError(
                f"Paga authentication failed with status {response.status_code}"
            )
        if response.status_code >= 400:
            raise self._to_api_error(response)

        body: Any = response.json() if response.content else {}
        result = PagaResponse.model_validate(body)
        if not result.is_success:
            raise PagaAPIError(
                message=result.message or "Paga request failed",
                response_code=result.responseCode,
                payload=result,
            )
        return result

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

    async def create_payment(self, payload: Mapping[str, Any]) -> CollectPaymentRequestResponse:
        """Create a Paga payment request.

        Operation: Dynamic virtual account - Create a payment request.

        The customer pays via the payment methods supplied (e.g. bank transfer
        with a one-time Paga virtual account number). Paga sends a callback to
        the configured ``callBackUrl`` when the payment completes.

        Args:
            payload: Payment request fields (``referenceNumber``, ``amount``,
                ``currency``, ``payer``, ``payee``, ``callBackUrl``,
                ``paymentMethods``, ...).

        Returns:
            The parsed :class:`CollectPaymentRequestResponse`.
        """
        response = await self._request(
            "POST",
            "/paymentRequest",
            payload,
            use_hash=True,
            use_basic=True,
        )
        return CollectPaymentRequestResponse.model_validate(response.model_dump())

    async def verify_charge(self, payload: Mapping[str, Any]) -> CheckoutVerifyChargeResponse:
        """Verify a checkout charge.

        Confirms a Checkout payment from your server at any time using its
        ``paymentReference``. Uses HTTP Basic auth only.

        - ``status_code`` of ``0`` means paid.
        - ``status_code`` of ``2`` means pending.

        Args:
            payload: Charge verification fields (``paymentReference``,
                ``publicKey``, ``amount``, ``currency``).

        Returns:
            The parsed :class:`CheckoutVerifyChargeResponse`.
        """
        response = await self._request(
            "POST",
            "/checkout/transaction/verify",
            payload,
            use_hash=False,
            use_basic=True,
            base_url=self.checkout_base_url,
        )
        return CheckoutVerifyChargeResponse.model_validate(response.model_dump())
