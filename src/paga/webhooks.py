"""Helpers for verifying and parsing Paga payment callbacks (webhooks)."""

from __future__ import annotations

import hmac
from typing import Any, Iterable, Mapping, Optional, Sequence

from .auth import (
    CHARGE_CALLBACK_HASH_FIELDS,
    DEFAULT_HASH_ALGORITHM,
    MANDATE_CALLBACK_HASH_FIELDS,
    PAYMENT_CALLBACK_HASH_FIELDS,
    SUBSIDIARY_FUNDING_HASH_FIELDS,
    SUBSIDIARY_OPERATION_HASH_FIELDS,
    generate_hash,
)
from .models import MoneyTransferNotification, PagaPaymentCallback, UsdPaymentWebhook

# Hash fields for the Checkout payment notification callback.
CHECKOUT_NOTIFICATION_HASH_FIELDS: tuple = (
    "amount",
    "timeStamp",
    "paymentReference",
)

# Hash fields for the Money transfer notification callback. Paga sends the
# digest in the ``x-paga-hash`` header and the field order in
# ``x-paga-hash-parameters``.
MONEY_TRANSFER_NOTIFICATION_HASH_FIELDS: tuple = (
    "referenceNumber",
    "transactionDate",
    "transactionId",
    "amount",
    "sessionId",
)

# Hash fields for the Persistent Payment Account callback, as signed into the
# body's ``hash`` field.
PERSISTENT_PAYMENT_ACCOUNT_HASH_FIELDS: tuple = (
    "statusCode",
    "accountNumber",
    "amount",
    "clearingFeeAmount",
    "transferFeeAmount",
)

# Hash fields for the Persistent Payment Account callback, as signed into the
# ``x-paga-hash`` header.
PERSISTENT_PAYMENT_ACCOUNT_HEADER_HASH_FIELDS: tuple = (
    "transactionReference",
    "accountNumber",
    "amount",
)


def _normalise_fields(
    fields: Optional[Iterable[str]],
    hash_parameters: Optional[Iterable[str]] = None,
) -> tuple:
    """Resolve the signed field order.

    Paga's ``x-paga-hash-parameters`` header names the fields in the order it
    signed them, which is authoritative when present. A trailing ``hashKey``
    entry is dropped: the key is appended by the SDK, never signed as a field.
    """
    if hash_parameters:
        cleaned = [name.strip() for name in hash_parameters if name and name.strip()]
        cleaned = [name for name in cleaned if name.lower() != "hashkey"]
        if cleaned:
            return tuple(cleaned)
    if fields:
        return tuple(fields)
    return tuple(PAYMENT_CALLBACK_HASH_FIELDS)


def _split_hash_parameters(raw: Optional[str]) -> Optional[tuple]:
    """Parse the ``x-paga-hash-parameters`` header value."""
    if not raw:
        return None
    parts = [part.strip() for part in raw.replace(";", ",").split(",") if part.strip()]
    return tuple(parts) if parts else None


def parse_hash_parameters(raw: Optional[str]) -> Optional[tuple]:
    """Parse Paga's ``x-paga-hash-parameters`` header.

    The header names the fields Paga signed, in order. A trailing ``hashKey``
    entry is dropped, because the SDK appends the key itself.

    Args:
        raw: The raw header value, for example
            ``"referenceNumber,transactionDate,transactionId,amount,sessionId"``.

    Returns:
        The field names in signing order, or ``None`` when the header is
        absent or empty.
    """
    parts = _split_hash_parameters(raw)
    if not parts:
        return None
    cleaned = tuple(name for name in parts if name.lower() != "hashkey")
    return cleaned or None


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


def verify_hash_header(
    payload: Optional[Mapping[str, Any]],
    received_hash: Optional[str],
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    fields: Optional[Sequence[str]] = None,
    hash_parameters: Optional[Sequence[str]] = None,
) -> bool:
    """Verify a Paga hash that arrived in a header rather than the body.

    Some Paga callbacks sign the digest into the ``x-paga-hash`` header and
    declare the signed field order in ``x-paga-hash-parameters``. When that
    header is present it wins over the caller's default order.

    Args:
        payload: The callback payload.
        received_hash: The value of the ``x-paga-hash`` header.
        hash_key: Business hash key provided by Paga.
        algorithm: Hash algorithm used for computation.
        fields: Default ordered hash field paths.
        hash_parameters: The parsed ``x-paga-hash-parameters`` header, which
            takes precedence over ``fields``.

    Returns:
        True when the received hash matches the computed hash.
    """
    computed = generate_hash(
        payload,
        hash_key,
        algorithm=algorithm,
        fields=_normalise_fields(fields, hash_parameters),
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


def verify_funding_notification(
    payload: Optional[Mapping[str, Any]],
    received_hash: Optional[str],
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    hash_fields: Optional[tuple] = None,
) -> bool:
    """Verify the hash of a subsidiary account funding notification.

    Operation: Subsidiary Accounts - Handle a funding notification.

    Sent when someone pays into a subsidiary account; the hash travels in the
    ``x-paga-hash-v3`` header, not the body.

    Hash: ``transactionReference + transactionDate + amount + accountNumber +
    timestamp + hashKey``.
    """
    return verify_hash(
        payload,
        received_hash,
        hash_key,
        algorithm=algorithm,
        fields=hash_fields or SUBSIDIARY_FUNDING_HASH_FIELDS,
    )


def verify_subsidiary_operation(
    payload: Optional[Mapping[str, Any]],
    received_hash: Optional[str],
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    hash_fields: Optional[tuple] = None,
) -> bool:
    """Verify the hash of a subsidiary charge, top-up or transfer callback.

    Operation: Subsidiary Accounts - Handle a charge, top-up or transfer callback.

    Sent when a charge (``SUBSIDIARY_ACCOUNT_CHARGE_COMPLETE``), top-up
    (``SUBSIDIARY_ACCOUNT_TOP_UP_COMPLETE``) or transfer
    (``SUBSIDIARY_ACCOUNT_TRANSFER_COMPLETE``, source account only) completes.

    Hash: ``externalReferenceNumber + transactionDate + amount + accountNumber +
    hashKey``. ``amount`` is a formatted string with commas, such as ``"1,000.00"``.
    """
    return verify_hash(
        payload,
        received_hash,
        hash_key,
        algorithm=algorithm,
        fields=hash_fields or SUBSIDIARY_OPERATION_HASH_FIELDS,
    )


def parse_payment_callback(payload: Optional[Mapping[str, Any]]) -> PagaPaymentCallback:
    """Parse and validate a Paga payment callback payload."""
    return PagaPaymentCallback.model_validate(payload or {})


def verify_money_transfer_notification(
    payload: Optional[Mapping[str, Any]],
    received_hash: Optional[str],
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    hash_parameters: Optional[Sequence[str]] = None,
) -> bool:
    """Verify the hash of a money transfer notification.

    Operation: Money transfer - Handle the notification.

    The digest travels in the ``x-paga-hash`` **header**, not the body. The
    signed fields are ``referenceNumber + transactionDate + transactionId +
    amount + sessionId``, unless Paga's ``x-paga-hash-parameters`` header says
    otherwise.

    Answer HTTP 200 with ``{"status": "SUCCESS"}`` once you have accepted the
    notification; Paga retries until it gets that.
    """
    return verify_hash_header(
        payload,
        received_hash,
        hash_key,
        algorithm=algorithm,
        fields=MONEY_TRANSFER_NOTIFICATION_HASH_FIELDS,
        hash_parameters=hash_parameters,
    )


def parse_money_transfer_notification(
    payload: Optional[Mapping[str, Any]],
) -> MoneyTransferNotification:
    """Parse a money transfer notification payload."""
    return MoneyTransferNotification.model_validate(payload or {})


def verify_persistent_payment_account_callback(
    payload: Optional[Mapping[str, Any]],
    received_hash: Optional[str],
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    hash_parameters: Optional[Sequence[str]] = None,
) -> bool:
    """Verify the hash of a persistent payment account callback.

    Operation: Collect API - Persistent Payment Account callback.

    Paga signs two digests over the same callback. The body's ``hash`` field
    covers ``statusCode + accountNumber + amount + clearingFeeAmount +
    transferFeeAmount``; the ``x-paga-hash`` header covers
    ``transactionReference + accountNumber + amount``.

    Pass the **body** hash as ``received_hash`` to verify the body digest, or
    the header digest to verify the header one.
    """
    return verify_hash_header(
        payload,
        received_hash,
        hash_key,
        algorithm=algorithm,
        fields=PERSISTENT_PAYMENT_ACCOUNT_HASH_FIELDS,
        hash_parameters=hash_parameters,
    )


def parse_usd_payment_webhook(payload: Optional[Mapping[str, Any]]) -> UsdPaymentWebhook:
    """Parse a USD (ACH, Wire, Swift) payment webhook.

    This webhook carries **no signature**, so there is nothing to verify.
    De-duplicate on ``referenceNumber`` + ``paymentId``.
    """
    return UsdPaymentWebhook.model_validate(payload or {})


def verify_mandate_callback(
    payload: Optional[Mapping[str, Any]],
    received_hash: Optional[str],
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
) -> bool:
    """Verify the hash of a Direct Debit mandate callback.

    Operation: Direct Debit - Handle the mandate callback.

    Hash: ``statusCode + timeStamp + accountNumber + bankName +
    referenceNumber + mandateStatus``. The ``timeStamp`` carries nanosecond
    precision and must be hashed exactly as received.

    The callback body carries the digest in its ``hash`` field. De-duplicate
    on ``notificationId``.
    """
    return verify_hash(
        payload,
        received_hash,
        hash_key,
        algorithm=algorithm,
        fields=MANDATE_CALLBACK_HASH_FIELDS,
    )


def verify_charge_callback(
    payload: Optional[Mapping[str, Any]],
    received_hash: Optional[str],
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
) -> bool:
    """Verify the hash of a Direct Debit charge callback.

    Operation: Direct Debit - Handle the charge callback.

    Hash: ``statusCode + referenceNumber + accountReference + amount``. The
    amount is a string with two decimals and no commas, such as ``"600.00"``.

    The callback body carries the digest in its ``hash`` field. De-duplicate
    on ``notificationId``.
    """
    return verify_hash(
        payload,
        received_hash,
        hash_key,
        algorithm=algorithm,
        fields=CHARGE_CALLBACK_HASH_FIELDS,
    )
