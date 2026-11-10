"""Typed exceptions raised by the Paga Engine SDK."""

from __future__ import annotations

from typing import Any, Optional


class PagaError(Exception):
    """Base exception for all errors raised by the Paga SDK."""


class PagaAuthenticationError(PagaError):
    """Raised when Paga rejects the supplied credentials or signature."""


class PagaAPIError(PagaError):
    """Raised when the Paga Engine API returns a non-success response."""

    def __init__(
        self,
        *,
        message: str,
        response_code: Optional[int] = None,
        status_code: Optional[int] = None,
        payload: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.responseCode = response_code
        self.statusCode = status_code
        self.payload = payload

    def __str__(self) -> str:
        return f"Paga API error (responseCode={self.responseCode}): {self.message}"


class PagaRateLimitError(PagaAPIError):
    """Raised when the Paga API responds with a rate limit status."""
