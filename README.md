# paga-python

**Async Python SDK for the [Paga Engine API](https://developer-docs.paga.com/).**

> **This is an unofficial SDK.** It is not built, endorsed, supported or
> published by Paga. It is community-maintained and follows Paga's published
> API reference. Paga's own documentation is the source of truth — if this
> documentation and Paga's disagree, Paga's is right.

> **Documentation:** <https://teamtrustbridge.github.io/paga-python-docs/> — the full
> Python API reference, organised like Paga's own documentation.

`paga-python` makes the Paga developer workflow easy for page and integration
developers building checkout and payment experiences. It wraps the Paga Engine
API — payments, refunds, money transfers, airtime, bill payments, Direct
Debit, subsidiary accounts and business account operations — behind a single,
fully async client.

The TypeScript (`paga-ts`) and Rust (`paga-rs`) counterparts live in the same
organisation and track the same operation set.

## Features

- **Async all the way through** — built on `httpx.AsyncClient`, usable as an async context manager.
- **Simple interface** — every operation takes plain keyword-only parameters; no raw JSON payloads needed.
- **Built-in Paga hash signing** — SHA-512 request hashing validated against Paga's documented examples, plus webhook signature verification helpers.
- **Typed responses** — pydantic models for every endpoint response.
- **Typed exceptions** — `PagaError`, `PagaAuthenticationError`, `PagaAPIError`, `PagaRateLimitError`.
- **Typed status codes** — `CollectStatusCode` and `BusinessErrorCode` enums, with `classify()` to turn a response into a `SUCCESS` / `PENDING` / `PARTIAL` / `FAILED` / `UNKNOWN` outcome.
- **Unknown-outcome detection** — Paga's `-1`, `105` and `135` mean *unknown*, not *failed*. `PagaAPIError.is_unknown_outcome` tells you when to check the transaction status instead of resending.

> Paga requires your server's IP address to be whitelisted before any call will
> succeed. A 403 usually means the IP is not on the list.

## Installation

```bash
pip install paga-python
```

Requires Python 3.9+ and runs on an asyncio event loop.

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
| Refunds | Check refund status | `get_refund_status` | `POST /status` |
| Bank USSD | List customer's banks | `get_collect_banks` | `POST /banks` |
| Direct Debit | Start hosted set-up session | `start_direct_debit_session` | `POST /checkout/charge-process/start` |
| Direct Debit | Set up a mandate by API | `create_direct_debit_mandate` | `POST /paymentRequest` |
| Direct Debit | Check mandate status | `get_mandate_status` | `POST /status` |
| Direct Debit | Charge the mandate | `charge_mandate` | `POST /chargeDebitMandate` |
| Direct Debit | Check charge status | `get_charge_mandate_status` | `POST /getChargeMandateStatus` |
| Direct Debit | Disable a mandate | `disable_mandate` | `POST /disableMandate` |
| USD collection | Check payment status | `get_usd_payment_status` | `POST /status` |
| Money transfer | List institutions | `get_banks` | `POST /getBanks` |
| Money transfer | Validate the account | `validate_deposit_to_bank` | `POST /validateDepositToBank` |
| Money transfer | Send money to a bank account | `send_money` | `POST /depositToBank` |
| Money transfer | Send money to a Paga wallet | `transfer_to_paga_wallet` | `POST /moneyTransfer` |
| Money transfer | Validate a Paga wallet transfer | `validate_money_transfer` | `POST /validateMoneyTransfer` |
| Money transfer | Bulk money transfer | `send_bulk_money_transfer` | `POST /moneyTransferBulk` |
| Money transfer | Check transaction status | `get_transaction_status` | `POST /transactionStatus` |
| Airtime & data | List operators | `get_mobile_operators` | `POST /getMobileOperators` |
| Airtime & data | List data bundles | `get_data_bundles` | `POST /getDataBundleByOperator` |
| Airtime & data | Buy airtime / data | `buy_airtime` | `POST /airtimePurchase` |
| Bill payment | List billers | `get_merchants` | `POST /getMerchants` |
| Bill payment | List a biller's services | `get_merchant_services` | `POST /getMerchantServices` |
| Bill payment | Validate the customer | `get_merchant_account_details` | `POST /getMerchantAccountDetails` |
| Bill payment | Pay bill | `pay_bill` | `POST /merchantPayment` |
| Business | Check balance | `get_business_balance` | `POST /accountBalance` |
| Business | Transaction history | `get_business_transactions` | `POST /transactionHistory` |
| Business | Recent transactions | `get_recent_transactions` | `POST /recentTransactionHistory` |
| Business | Operation status | `get_operation_status` | `POST /getOperationStatus` |
| Business | Onboard a merchant | `onboard_merchant` | `POST /onboardMerchant` |
| Business | Dispense cash | `dispense_cash` | `POST /dispenseCash` |
| Subsidiary accounts | Create account | `create_subsidiary_account` | `POST /subsidiary-accounts` |
| Subsidiary accounts | Charge account | `charge_subsidiary_account` | `POST /subsidiary-accounts/{accountReference}/charge` |
| Subsidiary accounts | Top up account | `top_up_subsidiary_account` | `POST /subsidiary-accounts/{accountReference}/topup` |
| Subsidiary accounts | Transfer between accounts | `transfer_between_subsidiary_accounts` | `POST /subsidiary-accounts/transfer` |
| Subsidiary accounts | Retrieve account | `retrieve_subsidiary_account` | `GET /subsidiary-accounts/{accountReference}` |
| Subsidiary accounts | Update account | `update_subsidiary_account` | `PUT /subsidiary-accounts/{accountReference}` |
| Subsidiary accounts | Get balance | `get_subsidiary_balance` | `GET /subsidiary-accounts/{accountReference}/balance` |
| Subsidiary accounts | History | `get_subsidiary_history` | `GET /subsidiary-accounts/{accountReference}/history` |
| Persistent accounts | Register | `register_persistent_payment_account` | `POST /registerPersistentPaymentAccount` |
| Persistent accounts | Update | `update_persistent_payment_account` | `POST /updatePersistentPaymentAccount` |
| Persistent accounts | Get | `get_persistent_payment_account` | `POST /getPersistentPaymentAccount` |
| Persistent accounts | Delete | `delete_persistent_payment_account` | `POST /deletePersistentPaymentAccount` |
| Payment history | Request history | `get_payment_request_history` | `POST /history` |
| Customers | Register | `register_customer` | `POST /registerCustomer` |
| Customers | Register with KYC | `register_customer_with_kyc` | `POST /registerCustomerWithKYC` |
| Customers | Upload account photo | `register_customer_account_photo` | `POST /registerCustomerAccountPhoto` |
| Customers | Upload identification | `register_customer_identification` | `POST /registerCustomerIdentification` |

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

### Charge a subsidiary account

```python
charge = await client.charge_subsidiary_account(
    account_reference="CUST-000184-WALLET",
    reference_number="REF-CHARGE-001",
    amount=1000,
    currency="NGN",
    narration="Service fee",
)
# charge.transactionId -> the debit transaction
# charge.newBalance -> balance after the debit
```

### Top up a subsidiary account

```python
top_up = await client.top_up_subsidiary_account(
    account_reference="CUST-000184-WALLET",
    reference_number="REF-TOPUP-001",
    amount=500,
    currency="NGN",
    narration="Bonus credit",
)
# top_up.newBalance -> balance after the credit
```

### Transfer between subsidiary accounts

```python
transfer = await client.transfer_between_subsidiary_accounts(
    source_account_reference="CUST-000184-WALLET",
    destination_account_reference="CUST-000221-WALLET",
    reference_number="REF-TRANSFER-001",
    amount=1500,
    currency="NGN",
    narration="Payment for goods",
)
```

### Retrieve / update / balance / history for a subsidiary account

```python
account = await client.retrieve_subsidiary_account(
    account_reference="CUST-000184-WALLET",
    reference_number="REF-GET-001",
)
account = await client.update_subsidiary_account(
    account_reference="CUST-000184-WALLET",
    reference_number="REF-UPDATE-001",
    status="DISABLED",  # send only what you want to change
)

balance = await client.get_subsidiary_balance(
    account_reference="CUST-000184-WALLET",
    reference_number="REF-BAL-001",
)

history = await client.get_subsidiary_history(
    account_reference="CUST-000184-WALLET",
    reference_number="REF-HIS-001",
    start_date_time_utc="2026-06-01T00:00:00",
    end_date_time_utc="2026-06-30T23:59:59",
    page_number=0,
    page_size=20,
)
```

## Webhook verification

```python
from paga import (
    parse_usd_payment_webhook,
    verify_charge_callback,
    verify_checkout_notification,
    verify_funding_notification,
    verify_mandate_callback,
    verify_money_transfer_notification,
    verify_payment_callback,
    verify_persistent_payment_account_callback,
    verify_subsidiary_operation,
)

# Checkout notification: hash = amount + timeStamp + paymentReference + hashKey
ok = verify_checkout_notification(payload, received_hash, hash_key)

# Dynamic virtual account callback: hash = notificationId + statusCode + externalReferenceNumber + state + outstandingBalance + hashKey
ok = verify_payment_callback(payload, received_hash, hash_key)

# Subsidiary funding notification: hash = transactionReference + transactionDate + amount + accountNumber + timestamp + hashKey
ok = verify_funding_notification(payload, received_hash, hash_key)

# Subsidiary charge / top-up / transfer callback: hash = externalReferenceNumber + transactionDate + amount + accountNumber + hashKey
ok = verify_subsidiary_operation(payload, received_hash, hash_key)

# Money transfer notification: the digest arrives in the x-paga-hash HEADER,
# not the body. hash = referenceNumber + transactionDate + transactionId + amount + sessionId
ok = verify_money_transfer_notification(payload, request.headers["x-paga-hash"], hash_key)

# Direct Debit mandate callback: hash = statusCode + timeStamp + accountNumber + bankName + referenceNumber + mandateStatus
ok = verify_mandate_callback(payload, payload["hash"], hash_key)

# Direct Debit charge callback: hash = statusCode + referenceNumber + accountReference + amount
ok = verify_charge_callback(payload, payload["hash"], hash_key)

# Persistent payment account callback: hash = statusCode + accountNumber + amount + clearingFeeAmount + transferFeeAmount
ok = verify_persistent_payment_account_callback(payload, payload["hash"], hash_key)
```

The USD (ACH, Wire and Swift) webhook carries **no signature at all**, so
there is nothing to verify — parse it and de-duplicate on `referenceNumber`
plus `paymentId`:

```python
webhook = parse_usd_payment_webhook(payload)
if webhook.isCaptured:
    ...  # fulfil
elif webhook.isFundingFailed:
    ...  # do not fulfil
```

## Error handling

```python
from paga import PagaAPIError, PagaAuthenticationError, PagaRateLimitError

try:
    payment = await client.create_payment(...)
except PagaAuthenticationError:
    ...  # invalid public key / secret key / hash key, or a non-whitelisted IP
except PagaRateLimitError:
    ...  # 429 from Paga
except PagaAPIError as err:
    ...  # err.code, err.responseCode, err.statusCode, err.outcome
```

A 200 response does not mean the money moved. Read the code in the body:

```python
from paga import classify, is_unknown_outcome, OperationOutcome

status = await client.get_transaction_status(reference_number="PAY-2026-0311")
if classify(status.model_dump()) is OperationOutcome.SUCCESS:
    ...  # settled
```

When the outcome is **unknown** — Paga's `-1`, `105` and `135`, a timeout or a
504 — do not send again. Check the transaction status with the *original*
reference number:

```python
if is_unknown_outcome(body):
    final = await client.get_transaction_status(reference_number=original_reference)
```

## License

GPL-3.0 — see [LICENSE](LICENSE).
