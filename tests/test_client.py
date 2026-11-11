"""HTTP-level tests for the Paga client.

These assert the things Paga actually cares about: the URL that was called,
which base URL it was called against, the auth style, the ``hash`` header and
the request body.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import httpx
import pytest

from paga import PagaClient
from paga.auth import generate_hash
from helpers import (
    BUSINESS_BASE,
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
async def test_get_collect_banks_uses_collect_base_and_basic_auth() -> None:
    """``/banks`` is a Collect API call: Collect base URL, Basic auth."""
    recorder = Recorder([(200, {"statusCode": "0", "banks": [{"name": "GTBank", "uuid": "UUID-1"}]})])
    client, http = make_client(recorder)
    try:
        response = await client.get_collect_banks(reference_number="REF-1")
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/banks"
    assert recorder.last.method == "POST"
    assert basic_credentials(recorder.last) == (PUBLIC_KEY, SECRET_KEY)
    assert response.banks[0].uuid == "UUID-1"


@pytest.mark.asyncio
async def test_get_banks_uses_business_base_and_header_auth() -> None:
    """``/getBanks`` is a Business API call: Business base URL, header auth."""
    recorder = Recorder([(200, {"responseCode": 0, "banks": [{"uuid": "UUID-2", "name": "Access"}]})])
    client, http = make_client(recorder)
    try:
        response = await client.get_banks(reference_number="REF-2")
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/getBanks"
    assert recorder.last.headers["principal"] == PUBLIC_KEY
    assert recorder.last.headers["credentials"] == SECRET_KEY
    assert "authorization" not in recorder.last.headers
    assert response.banks[0].name == "Access"


@pytest.mark.asyncio
async def test_hash_header_matches_the_documented_fields() -> None:
    """The hash must be computed over exactly the documented field order."""
    recorder = Recorder([(200, {"responseCode": 0})])
    client, http = make_client(recorder)
    try:
        await client.get_merchant_services(
            reference_number="REF-3",
            merchant_public_id="MERCHANT-UUID",
        )
    finally:
        await http.aclose()

    body = request_json(recorder.last)
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "merchantPublicId"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_merchant_account_details_always_signs_the_service_code() -> None:
    """The service code is signed even when the customer chose no service."""
    recorder = Recorder([(200, {"responseCode": 0, "customerName": "Bello Ramon"})])
    client, http = make_client(recorder)
    try:
        await client.get_merchant_account_details(
            reference_number="REF-4",
            merchant_account="MERCHANT-UUID",
            merchant_reference_number="8110411076",
        )
    finally:
        await http.aclose()

    body = request_json(recorder.last)
    assert body["merchantServiceProductCode"] == ""
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=(
            "referenceNumber",
            "merchantAccount",
            "merchantReferenceNumber",
            "merchantServiceProductCode",
        ),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_validate_deposit_to_bank_signs_the_amount_verbatim() -> None:
    """``"5000.00"`` and ``"5000"`` must sign differently."""
    recorder = Recorder([(200, {"responseCode": 0, "fee": 20.0})])
    client, http = make_client(recorder)
    try:
        await client.validate_deposit_to_bank(
            reference_number="REF-5",
            amount="5000.00",
            destination_bank_uuid="BANK-UUID",
            destination_bank_account_number="0000000000",
        )
    finally:
        await http.aclose()

    body = request_json(recorder.last)
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "amount", "destinationBankUUID", "destinationBankAccountNumber"),
    )
    assert recorder.last.headers["hash"] == expected
    assert body["amount"] == "5000.00"


@pytest.mark.asyncio
async def test_get_transaction_status_posts_to_the_business_api() -> None:
    """Transaction status is a Business API call."""
    recorder = Recorder([(200, {"responseCode": 0, "status": "Successful", "transactionId": "TX-1"})])
    client, http = make_client(recorder)
    try:
        response = await client.get_transaction_status(reference_number="REF-6")
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/transactionStatus"
    assert response.transactionId == "TX-1"
    assert response.status == "Successful"


@pytest.mark.asyncio
async def test_get_refund_status_reads_the_refund_status() -> None:
    """The refund status endpoint exposes ``data.refundStatus``."""
    recorder = Recorder(
        [
            (
                200,
                {
                    "statusCode": "0",
                    "data": {"statusCode": "0", "refundStatus": "refunded"},
                },
            )
        ]
    )
    client, http = make_client(recorder)
    try:
        response = await client.get_refund_status(reference_number="REF-7")
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/status"
    assert response.refundStatus == "refunded"
    assert response.isRefunded is True


@pytest.mark.asyncio
async def test_get_usd_payment_status_signs_the_currency() -> None:
    """The USD status operation signs the currency as well as the reference."""
    recorder = Recorder([(200, {"statusCode": "0", "data": {"statusCode": "1"}})])
    client, http = make_client(recorder)
    try:
        await client.get_usd_payment_status(reference_number="REF-8")
    finally:
        await http.aclose()

    body = request_json(recorder.last)
    assert body["paymentCurrency"] == "USD"
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "paymentCurrency"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_get_recent_transactions_returns_the_last_five() -> None:
    """Recent transactions come back newest first."""
    recorder = Recorder(
        [
            (
                200,
                {
                    "responseCode": 0,
                    "recordCount": 2,
                    "items": [
                        {"referenceNumber": "TX-2", "amount": 100.0},
                        {"referenceNumber": "TX-1", "amount": 50.0},
                    ],
                },
            )
        ]
    )
    client, http = make_client(recorder)
    try:
        response = await client.get_recent_transactions(reference_number="REF-9")
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/recentTransactionHistory"
    assert response.recordCount == 2
    assert response.items[0].referenceNumber == "TX-2"


@pytest.mark.asyncio
async def test_get_data_bundles_signs_the_operator_id() -> None:
    """The bundle lookup signs the operator's public id."""
    recorder = Recorder([(200, {"responseCode": 0, "mobileOperatorServices": []})])
    client, http = make_client(recorder)
    try:
        await client.get_data_bundles(
            reference_number="REF-10",
            operator_public_id="OPERATOR-1",
        )
    finally:
        await http.aclose()

    body = request_json(recorder.last)
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "operatorPublicId"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_live_environment_switches_base_urls() -> None:
    """The live environment must use the production base URLs."""
    recorder = Recorder([(200, {"responseCode": 0, "banks": []})])
    client, http = make_client(recorder, environment="live")
    try:
        await client.get_banks(reference_number="REF-11")
    finally:
        await http.aclose()

    assert str(recorder.last.url) == (
        "https://www.mypaga.com/paga-webservices/business-rest/secured/getBanks"
    )


@pytest.mark.asyncio
async def test_authentication_failure_raises() -> None:
    """A 401 raises the authentication error."""
    from paga import PagaAuthenticationError

    recorder = Recorder([(401, {"error": "Invalid paga account id or password"})])
    client, http = make_client(recorder)
    try:
        with pytest.raises(PagaAuthenticationError):
            await client.get_banks(reference_number="REF-12")
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_rate_limit_raises() -> None:
    """A 429 raises the rate limit error."""
    from paga import PagaRateLimitError

    recorder = Recorder([(429, {"message": "slow down"})])
    client, http = make_client(recorder)
    try:
        with pytest.raises(PagaRateLimitError):
            await client.get_banks(reference_number="REF-13")
    finally:
        await http.aclose()


@pytest.mark.asyncio
async def test_existing_create_payment_is_unchanged() -> None:
    """Adding the directory mixin must not disturb the checkout operations."""
    recorder = Recorder([(200, {"statusCode": "0", "referenceNumber": "REF-14"})])
    client, http = make_client(recorder)
    try:
        await client.create_payment(
            reference_number="REF-14",
            amount=50,
            payer_name="Bello Ramon",
            payer_phone_number="08064343187",
            payee_name="Your business name",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/paymentRequest"
    body = request_json(recorder.last)
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "amount", "currency", "payer.phoneNumber", "payer.email"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_verify_charge_targets_the_checkout_base() -> None:
    """Checkout verification uses the Checkout base URL and Basic auth."""
    recorder = Recorder([(200, {"status_code": 0, "chargeId": "CHARGE-1"})])
    client, http = make_client(recorder)
    try:
        await client.verify_charge(
            payment_reference="PAY-1",
            public_key=PUBLIC_KEY,
            amount=50,
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{CHECKOUT_BASE}/checkout/transaction/verify"
    assert basic_credentials(recorder.last) == (PUBLIC_KEY, SECRET_KEY)
    assert request_json(recorder.last)["paymentReference"] == "PAY-1"
