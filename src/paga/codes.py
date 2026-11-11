"""Paga status and error codes.

Paga exposes two different code vocabularies:

- The **Collect API** (payments, refunds, subsidiary accounts, Direct Debit)
  reports a ``statusCode`` **string**. ``"0"`` means success.
- The **Business API** (money transfer, airtime, bill payment, business
  account) reports a ``responseCode`` **integer**. ``0`` means success.

They are modelled separately because the same numeric value means different
things in each family: ``114`` is ``FAILED`` on Collect but
``INVALID_ACCOUNT`` on Business.
"""

from __future__ import annotations

from enum import Enum
from typing import Any, Mapping, Optional, Union

__all__ = [
    "BusinessErrorCode",
    "ChargeStatusCode",
    "CollectStatusCode",
    "MandateProcessStatus",
    "MandateStatusCode",
    "PaymentRequestState",
    "as_mapping",
    "resolve_business_code",
    "resolve_collect_status",
]


class CollectStatusCode(str, Enum):
    """``statusCode`` values returned by the Collect API."""

    SUCCESS = "0"
    IN_PROCESS = "1"
    PARTIAL_PAYMENT = "2"
    SYSTEM_ERROR = "-1"
    REQUEST_EXPIRED = "-2"
    REQUEST_CANCELLED = "-3"
    FAILED = "114"
    FAILED_NON_REFUNDABLE = "115"
    NOT_FOUND = "121"


class BusinessErrorCode(int, Enum):
    """``responseCode`` values returned by the Business API."""

    SUCCESS = 0
    BULK_PARTIAL_SUCCESS = 1
    BULK_ALL_FAILED = 2
    PENDING = 3

    UNKNOWN_ERROR = -1
    UNSUPPORTED_OPERATION = -2

    INVALID_ACCOUNT_NUMBER = 4

    INVALID_BANK = 101
    DISABLED_ACCOUNT = 103
    INVALID_PRINCIPAL = 104
    DUPLICATE_REFERENCE = 105
    INVALID_RECIPIENT_ACCOUNT = 107
    INVALID_ORGANISATION_USER = 108
    AIRTIME_ERROR = 109
    INVALID_ORGANISATION = 110
    INVALID_CUSTOMER = 111
    INVALID_BILLER = 112
    INVALID_USER = 113
    INVALID_ACCOUNT = 114
    INVALID_BANK_ACCOUNT = 115
    INVALID_AMOUNT = 116
    MISSING_PARAMETER = 117
    INVALID_USER_IDENTIFIER = 118
    INVALID_PROCESS = 119
    PHOTO_ALREADY_SET = 120
    INVALID_IMAGE_TYPE = 121
    INVALID_IDENTIFICATION_DETAILS = 122
    INVALID_PHONE_NUMBER = 123
    INVALID_FIRST_NAME = 124
    INVALID_LAST_NAME = 125
    INVALID_USERNAME = 126
    INVALID_EMAIL = 127
    EMAIL_ALREADY_EXISTS = 128
    LOCKED_USER_ACCOUNT = 129
    INVALID_NAME = 130
    INVALID_MERCHANT = 131
    INVALID_PROCESS_CHANNEL = 132
    DESTINATION_BANK_NOT_FOUND = 133
    INVALID_DATE_OF_BIRTH = 134
    UNKNOWN_REFERENCE_NUMBER = 135
    EXCEEDS_TRANSACTION_LIMIT = 136
    BELOW_MINIMUM = 137
    EXCEEDS_ACCOUNT_LIMIT = 138
    INSUFFICIENT_BALANCE = 139
    REFERENCE_NUMBER_TOO_LONG = 140


class MandateStatusCode(str, Enum):
    """``statusCode`` values on a Direct Debit mandate callback."""

    PENDING = "003"
    VERIFIED = "004"
    APPROVED = "0"
    REJECTED = "005"
    UNKNOWN = "006"
    NOT_FOUND = "007"


class MandateProcessStatus(str, Enum):
    """``ProcessStatusId`` values on a mandate.

    This is the field to branch on. A mandate's ``data.statusCode`` stays
    ``"1"`` / ``"pending"`` forever, so it tells you nothing.
    """

    PENDING = "PENDING"
    VERIFIED = "VERIFIED"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ChargeStatusCode(int, Enum):
    """``data.statusCode`` values returned by ``/getChargeMandateStatus``."""

    CHARGED = 0
    PENDING = 1
    INVALID = -1
    UNKNOWN = -4


class PaymentRequestState(str, Enum):
    """States a payment request moves through."""

    PENDING = "PENDING"
    CHARGEABLE = "CHARGEABLE"
    CONSUMED = "CONSUMED"
    EXPIRED = "EXPIRED"
    FAILED = "FAILED"
    CANCELLED = "CANCELLED"


def as_mapping(body: Any) -> Optional[Mapping[str, Any]]:
    """Coerce a response body into a plain mapping.

    Accepts a dict, or any pydantic model exposing ``model_dump()``.
    Returns ``None`` when the body cannot be inspected.
    """
    if body is None:
        return None
    if isinstance(body, Mapping):
        return body
    dump = getattr(body, "model_dump", None)
    if callable(dump):
        try:
            dumped = dump()
        except Exception:  # noqa: BLE001 - a broken model is not a code source
            return None
        if isinstance(dumped, Mapping):
            return dumped
    return None


def resolve_collect_status(body: Optional[Mapping[str, Any]]) -> Optional[CollectStatusCode]:
    """Return the :class:`CollectStatusCode` carried by ``body``, if any.

    Paga sends ``statusCode`` as a string, but some legacy responses send it
    as an integer, so both are accepted.
    """
    body = as_mapping(body)
    if body is None:
        return None
    raw = body.get("statusCode")
    if raw is None:
        return None
    try:
        return CollectStatusCode(str(raw))
    except ValueError:
        return None


def resolve_business_code(body: Optional[Mapping[str, Any]]) -> Optional[BusinessErrorCode]:
    """Return the :class:`BusinessErrorCode` carried by ``body``, if any."""
    body = as_mapping(body)
    if body is None:
        return None
    raw = body.get("responseCode")
    if raw is None:
        return None
    try:
        return BusinessErrorCode(int(raw))
    except (TypeError, ValueError):
        return None


ResolvedCode = Union[CollectStatusCode, BusinessErrorCode, None]
