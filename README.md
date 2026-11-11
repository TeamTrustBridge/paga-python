# paga-python

Async Python SDK for the **Paga Engine API**, built to make the developer workflow
easy for page/integration developers building checkout and payment experiences.

## Status

Phase 3 in progress — action operations shipped and hash-verified:

- Async client foundation (`PagaClient`, async context manager)
- Credentials + Paga hash signing (validated against Paga's documented hash examples)
- Checkout: create payment request, get payment status, verify charge
- Refunds: refund / cancel payment request
- Money transfer: send money to bank / Paga wallet
- Airtime & data: buy airtime / data
- Bill payment: pay bill

Full endpoint coverage is being delivered in phases across the sibling packages
`paga-ts` (TypeScript) and `paga-rs` (Rust).

## Install

```bash
pip install -e .
```

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

## Webhook verification

```python
from paga import verify_checkout_notification, verify_payment_callback, parse_payment_callback

# Checkout notification: hash = amount + timeStamp + paymentReference + hashKey
ok = verify_checkout_notification(payload, received_hash, hash_key)

# Dynamic virtual account callback: hash = notificationId + statusCode + externalReferenceNumber + state + outstandingBalance + hashKey
ok = verify_payment_callback(payload, received_hash, hash_key)
```

## License

GPL-3.0 (see [LICENSE](LICENSE))
