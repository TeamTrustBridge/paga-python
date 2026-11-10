"""Helpers for verifying and parsing Paga payment callbacks (webhooks)."""

from __future__ import annotations

import hmac
from typing import Any, Mapping, Optional

from .auth import DEFAULT_HASH_ALGORITHM, PAYMENT_CALLBACK_HASH_FIELDS, generate_hash
from .models import PagaPaymentCallback

# Hash fields for the Checkout payment notification callback.
CHECKOUT_NOTIFICATION_HASH_FIELDS: tuple = (
    "amount",
    "timeStamp",
    "paymentReference",
)


def verify_hash(
    payload: Optional[Mapping[str, Any]],
    received_hash: Optional[str],
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    fields: Optional[tuple] = None,
) -> bool:
    """Verify a Paga hash signature sent with an operation.

    The hash is the configured algorithm digest of the concatenated hash field
    values followed by the business hash key, compared in constant time.

    Args:
        payload: The operation payload (or callback payload).
        received_hash: The hash received from Paga.
        hash_key: Business hash key provided by Paga.
        algorithm: Hash algorithm used for computation.
        fields: Ordered hash field paths. Defaults to the payment callback hash
            fields.

    Returns:
        True when the received hash matches the computed hash.
    """
    computed = generate_hash(
        payload,
        hash_key,
        algorithm=algorithm,
        fields=fields or PAYMENT_CALLBACK_HASH_FIELDS,
    )
    received = str(received_hash or "").lower()
    return hmac.compare_digest(computed, received)


def verify_payment_callback(
    payload: Optional[Mapping[str, Any]],
    received_hash: Optional[str],
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    hash_fields: Optional[tuple] = None,
) -> bool:
    """Verify the hash of a Paga payment callback (dynamic virtual account).

    Hash: ``notificationId + statusCode + externalReferenceNumber + state +
    outstandingBalance + hashKey``.
    """
    return verify_hash(
        payload,
        received_hash,
        hash_key,
        algorithm=algorithm,
        fields=hash_fields or PAYMENT_CALLBACK_HASH_FIELDS,
    )


def verify_checkout_notification(
    payload: Optional[Mapping[str, Any]],
    received_hash: Optional[str],
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
) -> bool:
    """Verify the hash of a Paga checkout payment notification.

    Hash: ``amount + timeStamp + paymentReference + hashKey``. Use ``amount``
    exactly as received (e.g. ``"10.00"``).
    """
    return verify_hash(
        payload,
        received_hash,
        hash_key,
        algorithm=algorithm,
        fields=CHECKOUT_NOTIFICATION_HASH_FIELDS,
    )


def parse_payment_callback(payload: Optional[Mapping[str, Any]]) -> PagaPaymentCallback:
    """Parse and validate a Paga payment callback payload."""
    return PagaPaymentCallback.model_validate(payload or {})
