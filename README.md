# paga-python

**Async Python SDK for the [Paga Engine API](https://developer-docs.paga.com/).**

`paga-python` makes the Paga developer workflow easy for page and integration
developers building checkout and payment experiences. It wraps every Paga Engine
endpoint — payments, refunds, money transfers, airtime, bill payments, subsidiary
accounts, and business account operations — behind a single, fully async client.

The TypeScript (`paga-ts`) and Rust (`paga-rs`) counterparts are in the pipeline.

## Features

- **Async all the way through** — built on `httpx.AsyncClient`, usable as an async context manager.
- **Simple interface** — every operation takes plain keyword-only parameters; no raw JSON payloads needed.
- **Built-in Paga hash signing** — SHA-512 request hashing validated against Paga's documented examples, plus webhook signature verification helpers.
- **Typed responses** — pydantic models for every endpoint response.
- **Typed exceptions** — `PagaError`, `PagaAuthenticationError`, `PagaAPIError`, `PagaRateLimitError`.

## Installation

```bash
pip install -e .
```

Requires Python 3.11+ and runs on an asyncio event loop.

## Quick start

```python
import asyncio
from paga import PagaClient

async def main() -> None:
    async with PagaClient(
        public_id="YOUR_PUBLIC_KEY",
        credentials="YOUR_SECRET_KEY",
        hash_key="YOUR_HASH_KEY",
        environment="test",  # or "live"
    ) as client:
        payment = await client.create_payment(
            reference_number="ORD-2026-0187",
            amount=50,
            payer_name="Bello Ramon",
            payer_phone_number="08064343187",
            payee_name="Your business name",
            call_back_url="https://yourstore.com/webhooks/paga",
            payment_methods=["BANK_TRANSFER"],
        )
        status = await client.get_payment_status(reference_number="ORD-2026-0187")
        # status.data.statusCode -> "0" means paid

asyncio.run(main())
```

## Supported operations

| Area | Operation | Method | Endpoint |
|---|---|---|---|
| Checkout | Create payment request | `create_payment` | `POST /paymentRequest` |
| Checkout | Check payment status | `get_payment_status` | `POST /status` |
| Checkout | Verify charge | `verify_charge` | `POST /checkout/transaction/verify` |
| Refunds | Refund / cancel | `refund_payment` | `POST /refund/v2` |
| Money transfer | Send money | `send_money` | `POST /depositToBank` |
| Airtime & data | Buy airtime / data | `buy_airtime` | `POST /airtimePurchase` |
| Bill payment | Pay bill | `pay_bill` | `POST /merchantPayment` |
| Business | Check balance | `get_business_balance` | `POST /accountBalance` |
| Business | Transaction history | `get_business_transactions` | `POST /transactionHistory` |
| Subsidiary accounts | Create account | `create_subsidiary_account` | `POST /subsidiary-accounts` |

## Usage

All operations take simple, keyword-only parameters — no raw JSON payloads needed.

### Create a payment request

```python
payment = await client.create_payment(
    reference_number="ORD-2026-0187",
    amount=50,
    payer_name="Bello Ramon",
    payer_phone_number="08064343187",
    payee_name="Your business name",
    call_back_url="https://yourstore.com/webhooks/paga",
    payment_methods=["BANK_TRANSFER"],
)
```

### Check payment status

```python
status = await client.get_payment_status(reference_number="ORD-2026-0187")
# status.data.statusCode -> "0" means paid
```

### Verify a charge

```python
verified = await client.verify_charge(
    payment_reference=payment.referenceNumber,
    public_key="...",
    amount=50,
    currency="NGN",
)
# verified.status_code == 0 -> paid; 2 -> pending
```

### Refund / cancel a payment request

```python
refund = await client.refund_payment(
    reference_number="RFD-2026-0031",
    payment_request_reference="ORD-2026-0187",
    refund_amount=1000,
    currency="NGN",
    reason="Item out of stock",
)
# refund.statusCode -> "102" means duplicate reference (no double refund)
```

### Send money to a bank account or Paga wallet

```python
transfer = await client.send_money(
    reference_number="PAY-2026-0311",
    amount="5000.00",
    destination_bank_uuid="40090E2F-7446-4217-9345-7BBAB7043C4C",
    destination_bank_account_number="0000000000",
    remarks="Salary for June",
)
```

### Buy airtime or data

```python
purchase = await client.buy_airtime(
    reference_number="AIR-2026-0042",
    amount="500",
    destination_phone_number="08063332187",
    mobile_operator_public_id="42419156-DD57-4737-8373-20678CD9AA29",
    is_data_bundle=False,
)
```

### Pay a bill

```python
bill = await client.pay_bill(
    reference_number="BILL-2026-0042",
    amount=6000,
    merchant_account="A3878DC1-F07D-48E7-AA59-8276C3C26647",
    merchant_reference_number="8110411076",
    merchant_service=["STARTERE36"],
)
# bill.responseCode -> 0 means success
```

### Check business account balance

```python
balance = await client.get_business_balance(reference_number="BAL-2026-0042")
# balance.availableBalance -> what you can actually send before a payout run
```

### Get business transaction history

```python
history = await client.get_business_transactions(
    reference_number="HIS-2026-0042",
    start_date_utc="2026-11-01T00:00:00",
    end_date_utc="2026-11-04T00:00:00",
)
# history.items -> transactions between the two dates
```

### Create a subsidiary account

```python
account = await client.create_subsidiary_account(
    reference_number="REF-100005550002",
    account_reference="CUST-000184-WALLET",
    account_name="Bello Ramon",
    iifi_number="22222132329",
    callback_url="https://yourstore.com/webhooks/paga",
)
# account.statusCode -> "0" means created; "102" means duplicate reference
```

## Webhook verification

```python
from paga import verify_checkout_notification, verify_payment_callback, parse_payment_callback

# Checkout notification: hash = amount + timeStamp + paymentReference + hashKey
ok = verify_checkout_notification(payload, received_hash, hash_key)

# Dynamic virtual account callback: hash = notificationId + statusCode + externalReferenceNumber + state + outstandingBalance + hashKey
ok = verify_payment_callback(payload, received_hash, hash_key)
```

## Error handling

```python
from paga import PagaError

try:
    payment = await client.create_payment(...)
except PagaAuthenticationError:
    ...  # invalid public key / secret key / hash key
except PagaRateLimitError:
    ...  # 429 from Paga
except PagaAPIError as err:
    ...  # err.responseCode, err.status_code, err.message
```

## License

GPL-3.0 — see [LICENSE](LICENSE).
