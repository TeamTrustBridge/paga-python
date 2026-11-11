"""Classify a Paga response into an outcome.

Paga's error handling is two-layered: the HTTP status says whether Paga
accepted the request, and the body code says what happened to the
*transaction*. A 200 response can still mean the money never moved.

Three of the Business API codes are **unknown outcomes** rather than
failures: ``-1`` (unknown error), ``105`` (duplicate reference) and ``135``
(unknown reference number). The correct response to those is to check the
transaction status with the *original* reference number, never to resend with
a new reference. :func:`classify` separates them so callers do not have to
remember the list.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Optional

from .codes import (
    BusinessErrorCode,
    CollectStatusCode,
    as_mapping,
    resolve_business_code,
    resolve_collect_status,
)

__all__ = [
    "OperationOutcome",
    "UNKNOWN_OUTCOME_BUSINESS_CODES",
    "classify",
    "is_unknown_outcome",
]


class OperationOutcome(str, Enum):
    """The outcome of a Paga operation."""

    SUCCESS = "success"
    """The operation completed. Money moved, or the request was created."""

    PENDING = "pending"
    """Accepted and still in flight. Poll the status endpoint or await the callback."""

    PARTIAL = "partial"
    """Partially fulfilled: some of the money arrived. More may still come."""

    FAILED = "failed"
    """The operation was rejected. Safe to retry with a new reference."""

    UNKNOWN = "unknown"
    """The outcome is undetermined. Check status with the original reference."""


#: Business API codes that mean "unknown outcome", not "failed".
UNKNOWN_OUTCOME_BUSINESS_CODES = frozenset(
    {
        BusinessErrorCode.UNKNOWN_ERROR,
        BusinessErrorCode.DUPLICATE_REFERENCE,
        BusinessErrorCode.UNKNOWN_REFERENCE_NUMBER,
    }
)

_COLLECT_PENDING = frozenset({CollectStatusCode.IN_PROCESS})
_COLLECT_PARTIAL = frozenset({CollectStatusCode.PARTIAL_PAYMENT})
_COLLECT_UNKNOWN = frozenset({CollectStatusCode.SYSTEM_ERROR})


def classify(body: Optional[Mapping[str, Any]]) -> OperationOutcome:
    """Classify a Paga response body into an :class:`OperationOutcome`.

    The Collect API is detected by the presence of ``statusCode`` and the
    Business API by ``responseCode``. A body carrying neither is treated as
    :attr:`OperationOutcome.UNKNOWN`, since there is nothing to conclude from.

    Args:
        body: The parsed JSON response body.

    Returns:
        The classified outcome.
    """
    if not isinstance(body, Mapping):
        body = as_mapping(body)
    if body is None:
        return OperationOutcome.UNKNOWN

    collect_status = resolve_collect_status(body)
    if collect_status is not None:
        if collect_status is CollectStatusCode.SUCCESS:
            return OperationOutcome.SUCCESS
        if collect_status in _COLLECT_PENDING:
            return OperationOutcome.PENDING
        if collect_status in _COLLECT_PARTIAL:
            return OperationOutcome.PARTIAL
        if collect_status in _COLLECT_UNKNOWN:
            return OperationOutcome.UNKNOWN
        return OperationOutcome.FAILED

    business_code = resolve_business_code(body)
    if business_code is not None:
        if business_code in (
            BusinessErrorCode.SUCCESS,
            BusinessErrorCode.BULK_PARTIAL_SUCCESS,
        ):
            return OperationOutcome.SUCCESS
        if business_code is BusinessErrorCode.PENDING:
            return OperationOutcome.PENDING
        if business_code in UNKNOWN_OUTCOME_BUSINESS_CODES:
            return OperationOutcome.UNKNOWN
        return OperationOutcome.FAILED

    return OperationOutcome.UNKNOWN


def is_unknown_outcome(body: Optional[Mapping[str, Any]]) -> bool:
    """Return True when the outcome of ``body`` is undetermined.

    An unknown outcome means you must check the transaction status using the
    original reference number. Retrying with a fresh reference risks moving
    money twice.
    """
    return classify(body) is OperationOutcome.UNKNOWN
