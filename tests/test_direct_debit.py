"""Direct Debit (Open Banking) tests."""

from __future__ import annotations

import json
from typing import Any, Dict

import pytest

from paga.auth import generate_hash
from paga.webhooks import verify_charge_callback, verify_mandate_callback
from helpers import (
    CHECKOUT_BASE,
    COLLECT_BASE,
    HASH_KEY,
    PUBLIC_KEY,
    SECRET_KEY,
    Recorder,
    basic_credentials,
    make_client,
    request_json,
)


@pytest.mark.asyncio
async def test_start_session_targets_checkout_and_sends_no_hash() -> None:
    """The hosted set-up session uses Basic auth and sends no hash header."""
    recorder = Recorder(
        [
            (
                200,
                {
                    "statusCode": "0",
                    "data": {
                        "sessionKey": "SESSION-KEY",
                        "status": "INITIALIZED",
                        "checkoutUrl": "https://checkout.paga.com/s/SESSION-KEY",
                    },
                },
            )
        ]
    )
    client, http = make_client(recorder)
    try:
        response = await client.start_direct_debit_session(
            reference_number="REF-1",
            account_reference="CUST-001",
            amount_limit=50000,
            callback_url="https://yourstore.com/webhooks/mandate",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{CHECKOUT_BASE}/checkout/charge-process/start"
    assert basic_credentials(recorder.last) == (PUBLIC_KEY, SECRET_KEY)
    assert "hash" not in recorder.last.headers

    body = request_json(recorder.last)
    assert body["paymentMethods"] == ["BANK_ACCOUNT_DIRECT_DEBIT"]
    assert body["amountLimit"] == 50000
    assert response.checkoutUrl == "https://checkout.paga.com/s/SESSION-KEY"


@pytest.mark.asyncio
async def test_start_session_groups_additional_properties() -> None:
    """The optional payer details are nested under ``additionalProperties``."""
    recorder = Recorder([(200, {"statusCode": "0", "data": {}})])
    client, http = make_client(recorder)
    try:
        await client.start_direct_debit_session(
            reference_number="REF-2",
            account_reference="CUST-002",
            amount_limit=1000,
            callback_url="https://yourstore.com/webhooks/mandate",
            payer_email="customer@example.com",
            authorization_amount=100.0,
        )
    finally:
        await http.aclose()

    body = request_json(recorder.last)
    assert body["additionalProperties"] == {
        "payerEmail": "customer@example.com",
        "authorizationAmount": 100.0,
    }


@pytest.mark.asyncio
async def test_create_mandate_uses_direct_debit_payment_method() -> None:
    """A mandate set up by API posts to /paymentRequest with DIRECT_DEBIT."""
    recorder = Recorder([(200, {"statusCode": "0", "referenceNumber": "REF-3"})])
    client, http = make_client(recorder)
    try:
        await client.create_direct_debit_mandate(
            reference_number="REF-3",
            amount=5000,
            payer_name="Bello Ramon",
            payer_phone_number="08064343187",
            payee_name="Your business name",
            account_reference="CUST-003",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/paymentRequest"
    body = request_json(recorder.last)
    assert body["paymentMethods"] == ["DIRECT_DEBIT"]
    assert body["accountReference"] == "CUST-003"
    assert body["isSingleUse"] is True

    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "amount", "currency", "payer.phoneNumber", "payer.email"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_get_mandate_status_reads_the_process_status_id() -> None:
    """The mandate status comes from ``additionalData.mandate[].ProcessStatusId``."""
    recorder = Recorder(
        [
            (
                200,
                {
                    "referenceNumber": "REF-4",
                    "statusCode": "0",
                    "statusMessage": "pending",
                    "data": {
                        "statusCode": "1",
                        "statusMessage": "pending",
                        "additionalData": {
                            "mandate": [
                                {
                                    "ProcessStatusId": "APPROVED",
                                    "AccountReference": "CUST-004",
                                }
                            ]
                        },
                    },
                },
            )
        ]
    )
    client, http = make_client(recorder)
    try:
        response = await client.get_mandate_status(reference_number="REF-4")
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/status"
    # The outer status code stays "1"/pending even for an approved mandate.
    assert response.data.statusCode == "1"
    assert response.mandateStatus == "APPROVED"
    assert response.isApproved is True


@pytest.mark.asyncio
async def test_mandate_status_is_not_approved_when_rejected() -> None:
    """A rejected mandate must not be chargeable."""
    recorder = Recorder(
        [
            (
                200,
                {
                    "statusCode": "0",
                    "data": {"additionalData": {"mandate": [{"ProcessStatusId": "REJECTED"}]}},
                },
            )
        ]
    )
    client, http = make_client(recorder)
    try:
        response = await client.get_mandate_status(reference_number="REF-5")
    finally:
        await http.aclose()

    assert response.mandateStatus == "REJECTED"
    assert response.isApproved is False


@pytest.mark.asyncio
async def test_charge_mandate_signs_the_account_reference() -> None:
    """Charging a mandate signs the reference, amount and account reference."""
    recorder = Recorder([(200, {"statusCode": "0", "referenceNumber": "REF-6"})])
    client, http = make_client(recorder)
    try:
        await client.charge_mandate(
            reference_number="REF-6",
            amount=600,
            account_reference="CUST-006",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/chargeDebitMandate"
    body = request_json(recorder.last)
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "amount", "accountReference"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_get_charge_mandate_status_reads_the_capitalised_keys() -> None:
    """Paga capitalises the charge status keys, so they are kept verbatim."""
    recorder = Recorder(
        [
            (
                200,
                {
                    "statusCode": "0",
                    "statusMessage": "ok",
                    "data": {
                        "statusCode": 0,
                        "ReferenceNumber": "REF-7",
                        "Amount": 600.0,
                        "ProcessStatusId": "COMPLETED",
                    },
                },
            )
        ]
    )
    client, http = make_client(recorder)
    try:
        response = await client.get_charge_mandate_status(reference_number="REF-7")
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/getChargeMandateStatus"
    assert response.chargeStatus == 0
    assert response.data.ReferenceNumber == "REF-7"


@pytest.mark.asyncio
async def test_disable_mandate_signs_the_account_reference() -> None:
    """Disabling a mandate signs the reference and account reference."""
    recorder = Recorder([(200, {"statusCode": "0", "referenceNumber": "REF-8"})])
    client, http = make_client(recorder)
    try:
        await client.disable_mandate(
            reference_number="REF-8",
            account_reference="CUST-008",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/disableMandate"
    body = request_json(recorder.last)
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "accountReference"),
    )
    assert recorder.last.headers["hash"] == expected


def test_verify_mandate_callback() -> None:
    """The mandate callback hash covers the six documented fields."""
    payload = {
        "event": "Tokenization",
        "notificationId": "NOTIF-1",
        "statusCode": "004",
        "statusMessage": "verified",
        "mandateStatus": "VERIFIED",
        "referenceNumber": "REF-9",
        "accountReference": "CUST-009",
        "bankName": "GTBank",
        "accountNumber": "12345678901",
        "timeStamp": "2026-11-03T11:02:25.123456789Z",
        "hash": "",
    }
    digest = generate_hash(
        payload,
        HASH_KEY,
        fields=(
            "statusCode",
            "timeStamp",
            "accountNumber",
            "bankName",
            "referenceNumber",
            "mandateStatus",
        ),
    )
    assert verify_mandate_callback(payload, digest, HASH_KEY) is True
    assert verify_mandate_callback(payload, "deadbeef", HASH_KEY) is False


def test_verify_charge_callback() -> None:
    """The charge callback hash covers four fields."""
    payload = {
        "event": "Charge_Complete",
        "notificationId": "NOTIF-2",
        "statusCode": "0",
        "processStatusId": "COMPLETED",
        "referenceNumber": "REF-10",
        "accountReference": "CUST-010",
        "amount": "600.00",
        "currency": "NGN",
        "hash": "",
    }
    digest = generate_hash(
        payload,
        HASH_KEY,
        fields=("statusCode", "referenceNumber", "accountReference", "amount"),
    )
    assert verify_charge_callback(payload, digest, HASH_KEY) is True
    assert verify_charge_callback(payload, "deadbeef", HASH_KEY) is False


def test_charge_callback_amount_string_is_signed_verbatim() -> None:
    """The charge callback amount keeps its two decimals and no commas."""
    payload = {
        "statusCode": "0",
        "referenceNumber": "REF-11",
        "accountReference": "CUST-011",
        "amount": "50000.00",
    }
    digest = generate_hash(
        payload,
        HASH_KEY,
        fields=("statusCode", "referenceNumber", "accountReference", "amount"),
    )
    assert verify_charge_callback(payload, digest, HASH_KEY) is True
