"""Tests for the persistent account, customer and extra Business operations."""

from __future__ import annotations

import json
from typing import Any, Dict

import pytest

from paga.auth import generate_hash
from helpers import (
    BUSINESS_BASE,
    COLLECT_BASE,
    HASH_KEY,
    Recorder,
    make_client,
    request_json,
)


@pytest.mark.asyncio
async def test_register_persistent_account_signs_six_fields() -> None:
    """Registering a persistent account signs all six documented fields."""
    recorder = Recorder([(200, {"statusCode": "0", "accountReference": "ACC-1"})])
    client, http = make_client(recorder)
    try:
        await client.register_persistent_payment_account(
            reference_number="REF-1",
            account_reference="ACC-1",
            financial_identification_number="22222132329",
            credit_bank_id="BANK-UUID",
            credit_bank_account_number="0000000000",
            callback_url="https://yourstore.com/webhooks/paga",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/registerPersistentPaymentAccount"
    body = request_json(recorder.last)
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=(
            "referenceNumber",
            "accountReference",
            "financialIdentificationNumber",
            "creditBankId",
            "creditBankAccountNumber",
            "callbackUrl",
        ),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_delete_persistent_account_signs_the_identifier() -> None:
    """Deleting signs the reference and the account identifier."""
    recorder = Recorder([(200, {"statusCode": "0"})])
    client, http = make_client(recorder)
    try:
        await client.delete_persistent_payment_account(
            reference_number="REF-2",
            account_identifier="ACC-2",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/deletePersistentPaymentAccount"
    body = request_json(recorder.last)
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "accountIdentifier"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_payment_request_history_posts_to_the_collect_api() -> None:
    """The payment request history is a Collect API operation."""
    recorder = Recorder([(200, {"statusCode": "0", "items": []})])
    client, http = make_client(recorder)
    try:
        await client.get_payment_request_history(reference_number="REF-3")
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{COLLECT_BASE}/history"


@pytest.mark.asyncio
async def test_register_customer_posts_json_to_the_business_api() -> None:
    """Plain customer registration is a JSON POST, not multipart."""
    recorder = Recorder([(200, {"responseCode": 0, "pagaAccountNumber": "0123456789"})])
    client, http = make_client(recorder)
    try:
        response = await client.register_customer(
            reference_number="REF-4",
            customer_phone_number="08031234567",
            customer_first_name="Bello",
            customer_last_name="Ramon",
            customer_email="customer@example.com",
            customer_date_of_birth="1989-10-02",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/registerCustomer"
    assert recorder.last.headers["content-type"].startswith("application/json")
    body = request_json(recorder.last)
    assert body["customerEmail"] == "customer@example.com"
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "customerPhoneNumber", "customerFirstName", "customerLastName"),
    )
    assert recorder.last.headers["hash"] == expected
    assert response.pagaAccountNumber == "0123456789"


@pytest.mark.asyncio
async def test_register_customer_with_kyc_sends_multipart() -> None:
    """KYC registration sends a JSON part plus two image parts."""
    recorder = Recorder([(200, {"responseCode": 0})])
    client, http = make_client(recorder)
    try:
        await client.register_customer_with_kyc(
            reference_number="REF-5",
            customer_phone_number="08031234567",
            customer_email="customer@example.com",
            customer_first_name="Bello",
            customer_last_name="Ramon",
            customer_date_of_birth="1989-10-02",
            customer_gender="MALE",
            customer_account_photo=b"account-photo-bytes",
            customer_id_photo=b"id-photo-bytes",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/registerCustomerWithKYC"
    content_type = recorder.last.headers["content-type"]
    assert content_type.startswith("multipart/form-data")

    raw = recorder.last.content
    assert b'name="customer"' in raw
    assert b'name="customerAccountPhoto"' in raw
    assert b'name="customerIdPhoto"' in raw
    assert b"account-photo-bytes" in raw
    assert b"id-photo-bytes" in raw


@pytest.mark.asyncio
async def test_kyc_registration_hashes_the_customer_json_part() -> None:
    """The hash covers the customer JSON, not the multipart envelope."""
    recorder = Recorder([(200, {"responseCode": 0})])
    client, http = make_client(recorder)
    try:
        await client.register_customer_with_kyc(
            reference_number="REF-6",
            customer_phone_number="08031234567",
            customer_email="customer@example.com",
            customer_first_name="Bello",
            customer_last_name="Ramon",
            customer_date_of_birth="1989-10-02",
            customer_gender="MALE",
            customer_account_photo=b"a",
            customer_id_photo=b"i",
        )
    finally:
        await http.aclose()

    customer_payload = {
        "referenceNumber": "REF-6",
        "customerPhoneNumber": "08031234567",
        "customerEmail": "customer@example.com",
        "customerFirstName": "Bello",
        "customerLastName": "Ramon",
        "customerDateOfBirth": "1989-10-02",
        "customerGender": "MALE",
    }
    expected = generate_hash(
        customer_payload,
        HASH_KEY,
        fields=("referenceNumber", "customerPhoneNumber", "customerFirstName", "customerLastName"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_register_customer_identification_signs_five_fields() -> None:
    """Identification upload signs the five documented fields."""
    recorder = Recorder([(200, {"responseCode": 0})])
    client, http = make_client(recorder)
    try:
        await client.register_customer_identification(
            reference_number="REF-7",
            customer_phone_number="08031234567",
            customer_id_type="NATIONAL_ID",
            customer_id_number="12345678901",
            customer_id_expiration_date="2030-01-01",
            customer_id_photo=b"photo",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/registerCustomerIdentification"
    customer_payload = {
        "referenceNumber": "REF-7",
        "customerPhoneNumber": "08031234567",
        "customerIdType": "NATIONAL_ID",
        "customerIdNumber": "12345678901",
        "customerIdExpirationDate": "2030-01-01",
    }
    expected = generate_hash(
        customer_payload,
        HASH_KEY,
        fields=(
            "referenceNumber",
            "customerPhoneNumber",
            "customerIdType",
            "customerIdNumber",
            "customerIdExpirationDate",
        ),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_bulk_transfer_signs_the_first_item_and_the_count() -> None:
    """The bulk hash covers the first item's fields plus the item count."""
    recorder = Recorder([(200, {"responseCode": 0, "results": []})])
    client, http = make_client(recorder)
    try:
        await client.send_bulk_money_transfer(
            items=[
                {
                    "referenceNumber": "ITEM-1",
                    "amount": 100.0,
                    "destinationAccount": "08031234567",
                },
                {
                    "referenceNumber": "ITEM-2",
                    "amount": 200.0,
                    "destinationAccount": "08031234568",
                },
            ],
            bulk_reference_number="BULK-1",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/moneyTransferBulk"
    body = request_json(recorder.last)
    assert body["bulkReferenceNumber"] == "BULK-1"
    assert len(body["items"]) == 2

    expected = generate_hash(
        {
            "referenceNumber": "ITEM-1",
            "amount": 100.0,
            "destinationAccount": "08031234567",
            "itemCount": 2,
        },
        HASH_KEY,
        fields=("referenceNumber", "amount", "destinationAccount", "itemCount"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_bulk_transfer_rejects_more_than_300_items() -> None:
    """The 300-item limit is enforced before the request is sent."""
    recorder = Recorder()
    client, http = make_client(recorder)
    try:
        items = [
            {"referenceNumber": f"ITEM-{index}", "amount": 1.0, "destinationAccount": "080"}
            for index in range(301)
        ]
        with pytest.raises(ValueError):
            await client.send_bulk_money_transfer(items=items)
    finally:
        await http.aclose()

    assert recorder.count == 0


@pytest.mark.asyncio
async def test_transfer_to_paga_wallet_signs_the_destination_account() -> None:
    """A Paga wallet transfer signs the destination account."""
    recorder = Recorder([(200, {"responseCode": 0, "transactionId": "TX-1"})])
    client, http = make_client(recorder)
    try:
        await client.transfer_to_paga_wallet(
            reference_number="REF-8",
            amount=5000.0,
            destination_account="08031234567",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/moneyTransfer"
    body = request_json(recorder.last)
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "amount", "destinationAccount"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_get_operation_status_reads_transaction_status() -> None:
    """The operation status endpoint reports ``transactionStatus``."""
    recorder = Recorder(
        [(200, {"responseCode": "0", "transactionStatus": "SUCCESSFUL", "message": "ok"})]
    )
    client, http = make_client(recorder)
    try:
        response = await client.get_operation_status(reference_number="REF-9")
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/getOperationStatus"
    assert response.transactionStatus == "SUCCESSFUL"


@pytest.mark.asyncio
async def test_dispense_cash_signs_four_fields() -> None:
    """Cash dispensing signs the reference, phone, amount and code."""
    recorder = Recorder([(200, {"responseCode": 0, "transactionId": "TX-2"})])
    client, http = make_client(recorder)
    try:
        await client.dispense_cash(
            reference_number="REF-10",
            customer_phone_number="08031234567",
            amount=5000.0,
            withdrawal_code="123456",
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/dispenseCash"
    body = request_json(recorder.last)
    expected = generate_hash(
        body,
        HASH_KEY,
        fields=("referenceNumber", "customerPhoneNumber", "amount", "withdrawalCode"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_onboard_merchant_signs_the_assembled_fields() -> None:
    """Merchant onboarding signs the reference, id, name, phone and email."""
    recorder = Recorder([(200, {"responseCode": 0})])
    client, http = make_client(recorder)
    try:
        await client.onboard_merchant(
            reference="REF-11",
            merchant_external_id="MERCH-1",
            legal_entity={"name": "Acme Ltd"},
            legal_entity_representative={
                "firstName": "Bello",
                "lastName": "Ramon",
                "phone": "08031234567",
                "email": "director@example.com",
                "dateOfBirth": "1989-10-02",
            },
            integration={"type": "EMAIL_NOTIFICATION", "financeAdminEmail": "fin@example.com"},
        )
    finally:
        await http.aclose()

    assert str(recorder.last.url) == f"{BUSINESS_BASE}/onboardMerchant"
    body = request_json(recorder.last)
    assert body["reference"] == "REF-11"
    expected = generate_hash(
        {
            "referenceNumber": "REF-11",
            "merchantExternalId": "MERCH-1",
            "name": "Acme Ltd",
            "phone": "08031234567",
            "email": "director@example.com",
        },
        HASH_KEY,
        fields=("referenceNumber", "merchantExternalId", "name", "phone", "email"),
    )
    assert recorder.last.headers["hash"] == expected


@pytest.mark.asyncio
async def test_banks_response_accepts_the_singular_bank_key() -> None:
    """Paga's legacy docs show ``bank``; the current API returns ``banks``."""
    recorder = Recorder([(200, {"responseCode": 0, "bank": [{"uuid": "UUID-1", "name": "Paga"}]})])
    client, http = make_client(recorder)
    try:
        response = await client.get_banks(reference_number="REF-12")
    finally:
        await http.aclose()

    assert response.banks[0].uuid == "UUID-1"


@pytest.mark.asyncio
async def test_rate_limited_requests_are_not_retried_by_default() -> None:
    """A 429 is not retried unless the client opts in."""
    from paga import PagaRateLimitError

    recorder = Recorder([(429, {"message": "slow down"})])
    client, http = make_client(recorder)
    try:
        with pytest.raises(PagaRateLimitError):
            await client.get_banks(reference_number="REF-13")
    finally:
        await http.aclose()

    assert recorder.count == 1


@pytest.mark.asyncio
async def test_rate_limited_requests_are_retried_when_enabled() -> None:
    """With ``max_retries`` set, a rate-limited request is replayed."""
    from paga import PagaRateLimitError

    recorder = Recorder(
        [
            (429, {"message": "slow down"}),
            (429, {"message": "slow down"}),
        ]
    )
    client, http = make_client(recorder, max_retries=1, retry_backoff=0.01)
    try:
        with pytest.raises(PagaRateLimitError):
            await client.get_banks(reference_number="REF-14")
    finally:
        await http.aclose()

    assert recorder.count == 2
