"""Webhook verification tests."""

from __future__ import annotations

import hashlib
from typing import Any, Dict

import pytest

from paga.auth import generate_hash
from paga.webhooks import (
    MONEY_TRANSFER_NOTIFICATION_HASH_FIELDS,
    PERSISTENT_PAYMENT_ACCOUNT_HASH_FIELDS,
    parse_hash_parameters,
    parse_money_transfer_notification,
    parse_usd_payment_webhook,
    verify_money_transfer_notification,
    verify_persistent_payment_account_callback,
)

HASH_KEY = "hashkey123"


def _digest(payload: Dict[str, Any], fields: Any) -> str:
    return generate_hash(payload, HASH_KEY, fields=fields)


def test_parse_hash_parameters_splits_and_strips_the_key() -> None:
    """The parameters header names the signed fields, without the key."""
    assert parse_hash_parameters(
        "referenceNumber,transactionDate,transactionId,amount,sessionId"
    ) == ("referenceNumber", "transactionDate", "transactionId", "amount", "sessionId")


def test_parse_hash_parameters_drops_a_trailing_hash_key() -> None:
    """The hash key is appended by the SDK, never signed as a field."""
    assert parse_hash_parameters("referenceNumber,amount,hashKey") == (
        "referenceNumber",
        "amount",
    )


def test_parse_hash_parameters_accepts_semicolons() -> None:
    """Both separators Paga uses are accepted."""
    assert parse_hash_parameters("referenceNumber;amount") == ("referenceNumber", "amount")


def test_parse_hash_parameters_handles_absence() -> None:
    """An absent header yields ``None``."""
    assert parse_hash_parameters(None) is None
    assert parse_hash_parameters("") is None


def test_money_transfer_notification_verifies() -> None:
    """A correctly signed money transfer notification verifies."""
    payload = {
        "referenceNumber": "REF-1",
        "transactionDate": "2026-11-03 11:02:25.56",
        "transactionId": "TX-1",
        "amount": "5000.0",
        "sessionId": "SESSION-1",
        "responseCode": 0,
    }
    digest = _digest(payload, MONEY_TRANSFER_NOTIFICATION_HASH_FIELDS)
    assert verify_money_transfer_notification(payload, digest, HASH_KEY) is True


def test_money_transfer_notification_rejects_a_tampered_amount() -> None:
    """Changing the amount invalidates the signature."""
    payload = {
        "referenceNumber": "REF-1",
        "transactionDate": "2026-11-03 11:02:25.56",
        "transactionId": "TX-1",
        "amount": "5000.0",
        "sessionId": "SESSION-1",
    }
    digest = _digest(payload, MONEY_TRANSFER_NOTIFICATION_HASH_FIELDS)
    tampered = dict(payload, amount="50000.0")
    assert verify_money_transfer_notification(tampered, digest, HASH_KEY) is False


def test_money_transfer_notification_honours_the_parameters_header() -> None:
    """``x-paga-hash-parameters`` overrides the default field order."""
    payload = {"referenceNumber": "REF-1", "sessionId": "SESSION-1"}
    # Signed with the reverse order, as the header would declare.
    digest = _digest(payload, ("sessionId", "referenceNumber"))
    assert (
        verify_money_transfer_notification(
            payload,
            digest,
            HASH_KEY,
            hash_parameters=("sessionId", "referenceNumber"),
        )
        is True
    )
    # The default order must not verify the same digest.
    assert verify_money_transfer_notification(payload, digest, HASH_KEY) is False


def test_money_transfer_notification_is_case_insensitive() -> None:
    """An uppercase header digest still verifies."""
    payload = {"referenceNumber": "REF-1", "transactionId": "TX-1", "amount": "1.0"}
    digest = _digest(payload, MONEY_TRANSFER_NOTIFICATION_HASH_FIELDS)
    assert (
        verify_money_transfer_notification(payload, digest.upper(), HASH_KEY) is True
    )


def test_parse_money_transfer_notification() -> None:
    """The notification body parses into a typed model."""
    payload = {
        "responseCode": 0,
        "referenceNumber": "REF-1",
        "transactionId": "TX-1",
        "amount": "5000.0",
        "fee": 20.0,
        "currency": "NGN",
    }
    notification = parse_money_transfer_notification(payload)
    assert notification.referenceNumber == "REF-1"
    assert notification.amount == "5000.0"
    assert notification.fee == 20.0


def test_persistent_payment_account_callback_verifies() -> None:
    """The persistent payment account body hash verifies."""
    payload = {
        "statusCode": "0",
        "accountNumber": "12345678901",
        "amount": "5000.00",
        "clearingFeeAmount": "10.00",
        "transferFeeAmount": "5.00",
    }
    digest = _digest(payload, PERSISTENT_PAYMENT_ACCOUNT_HASH_FIELDS)
    assert verify_persistent_payment_account_callback(payload, digest, HASH_KEY) is True


def test_persistent_payment_account_callback_rejects_a_tampered_amount() -> None:
    """Changing the amount invalidates the signature."""
    payload = {
        "statusCode": "0",
        "accountNumber": "12345678901",
        "amount": "5000.00",
        "clearingFeeAmount": "10.00",
        "transferFeeAmount": "5.00",
    }
    digest = _digest(payload, PERSISTENT_PAYMENT_ACCOUNT_HASH_FIELDS)
    tampered = dict(payload, amount="50000.00")
    assert (
        verify_persistent_payment_account_callback(tampered, digest, HASH_KEY) is False
    )


def test_usd_webhook_has_no_signature_but_parses() -> None:
    """The USD webhook carries no hash; it only parses."""
    payload = {
        "event": "CAPTURED",
        "referenceNumber": "REF-1",
        "paymentId": "PAY-1",
        "paymentStatus": "CAPTURED",
        "receivedAmounts": {"currency": "USD", "amounts": {"BASE": 10.0}},
        "serviceDetails": {
            "sourceCurrency": "USD",
            "destinationCurrency": "NGN",
            "foreignExchangeRate": 1500.0,
            "destinationAmount": 15000.0,
        },
    }
    webhook = parse_usd_payment_webhook(payload)
    assert webhook.isCaptured is True
    assert webhook.isFundingFailed is False
    assert webhook.referenceNumber == "REF-1"
    assert webhook.paymentId == "PAY-1"


def test_usd_webhook_detects_funding_failure() -> None:
    """``FUNDING_FAILED`` is recognised."""
    webhook = parse_usd_payment_webhook({"event": "FUNDING_FAILED"})
    assert webhook.isFundingFailed is True
    assert webhook.isCaptured is False


def test_verify_hash_header_matches_a_hand_computed_digest() -> None:
    """The header verifier agrees with a plain SHA-512 of the concatenation."""
    from paga.webhooks import verify_hash_header

    payload = {"referenceNumber": "REF-1", "amount": "10.00"}
    expected = hashlib.sha512(("REF-1" + "10.00" + HASH_KEY).encode("utf-8")).hexdigest()
    assert verify_hash_header(payload, expected, HASH_KEY, fields=("referenceNumber", "amount"))
