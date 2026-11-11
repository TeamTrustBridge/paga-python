"""Typed exceptions raised by the Paga Engine SDK."""

from __future__ import annotations

from typing import Any, Optional

from .codes import (
    BusinessErrorCode,
    CollectStatusCode,
    resolve_business_code,
    resolve_collect_status,
)
from .outcome import OperationOutcome, classify

__all__ = [
    "PagaAPIError",
    "PagaAuthenticationError",
    "PagaError",
    "PagaRateLimitError",
]


class PagaError(Exception):
    """Base exception for all errors raised by the Paga SDK."""


class PagaAuthenticationError(PagaError):
    """Raised when Paga rejects the supplied credentials or signature."""


class PagaAPIError(PagaError):
    """Raised when the Paga Engine API returns a non-success response.

    Attributes:
        message: The human-readable message returned by Paga.
        responseCode: The Business API ``responseCode``, when present.
        statusCode: The HTTP status of the response.
        payload: The full parsed response body.
        code: The resolved Collect status or Business error code, when the
            body carried one.
        outcome: The classified outcome of the operation. Use
            :attr:`is_unknown_outcome` to tell "definitely failed" apart from
            "we don't know yet".
    """

    def __init__(
        self,
        *,
        message: str,
        response_code: Optional[int] = None,
        status_code: Optional[int] = None,
        payload: Optional[Any] = None,
        code: Optional[Any] = None,
    ) -> None:
        super().__init__(message)
        self.message = message
        self.responseCode = response_code
        self.statusCode = status_code
        self.payload = payload
        if code is None:
            code = resolve_collect_status(payload)
            if code is None:
                code = resolve_business_code(payload)
        self.code = code
        self.outcome = classify(payload)

    @property
    def is_unknown_outcome(self) -> bool:
        """Whether the outcome is undetermined.

        When this is True, check the transaction status using the original
        reference number. Do not resend with a new reference.
        """
        return self.outcome is OperationOutcome.UNKNOWN

    def __str__(self) -> str:
        if self.code is not None:
            return (
                f"Paga API error (code={self.code.value}, "
                f"outcome={self.outcome.value}): {self.message}"
            )
        return f"Paga API error (responseCode={self.responseCode}): {self.message}"


class PagaRateLimitError(PagaAPIError):
    """Raised when the Paga API responds with a rate limit status."""
