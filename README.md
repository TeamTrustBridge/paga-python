# paga-python

Async Python SDK for the **Paga Engine API**, built to make the developer workflow
easy for page/integration developers building checkout and payment experiences.

## Status

Phase 2 of the phased rollout complete:

- Async client foundation (`PagaClient`, async context manager)
- Credentials handling + Paga hash signing (validated against Paga's documented hash example)
- Checkout operations: create payment request, verify charge
- Payment callback (notification) parsing + hash verification

Full endpoint coverage is being delivered in phases across the sibling packages
`paga-ts` (TypeScript) and `paga-rs` (Rust).

## Install

```bash
pip install -e .
```

## Usage

### Create a payment request

```python
async with PagaClient(public_id=..., credentials=..., hash_key=...) as client:
    payment = await client.create_payment({
        "referenceNumber": "ORD-2026-0187",
        "amount": 50,
        "currency": "NGN",
        "payer": {"name": "Bello Ramon", "phoneNumber": "08064343187"},
        "payee": {"name": "Your business name"},
        "callBackUrl": "https://yourstore.com/webhooks/paga",
        "paymentMethods": ["BANK_TRANSFER"],
    })
    # payment.statusCode -> "0" means created; payment.paymentMethods[0].properties["AccountNumber"]
```

### Verify a charge

```python
verified = await client.verify_charge({
    "paymentReference": payment.referenceNumber,
    "publicKey": "...",
    "amount": 50,
    "currency": "NGN",
})
# verified.status_code == 0 -> paid; 2 -> pending
```

### Handle the payment callback (webhook)

```python
from paga import verify_checkout_notification, verify_payment_callback, parse_payment_callback

# Checkout notification: hash = amount + timeStamp + paymentReference + hashKey
ok = verify_checkout_notification(payload, received_hash, hash_key)

# Dynamic virtual account callback: hash = notificationId + statusCode + externalReferenceNumber + state + outstandingBalance + hashKey
ok = verify_payment_callback(payload, received_hash, hash_key)
```

### Refund or cancel a payment request

```python
refund = await client.refund_payment({
    "referenceNumber": "RFD-2026-0031",
    "paymentRequestReference": "ORD-2026-0187",
    "refundAmount": 1000,
    "currency": "NGN",
    "reason": "Item out of stock",
})
# refund.statusCode -> "102" means duplicate reference (no double refund)
```

### Send money to a bank account or Paga wallet

```python
transfer = await client.send_money({
    "referenceNumber": "PAY-2026-0311",
    "amount": "5000.00",
    "currency": "NGN",
    "destinationBankUUID": "40090E2F-7446-4217-9345-7BBAB7043C4C",
    "destinationBankAccountNumber": "0000000000",
    "remarks": "Salary for June",
})
# transfer.responseCode -> "0" means success; other codes mean pending/duplicate/failed
```

### Buy airtime or data

```python
purchase = await client.buy_airtime({
    "referenceNumber": "AIR-2026-0042",
    "amount": "500",
    "currency": "NGN",
    "destinationPhoneNumber": "08063332187",
    "mobileOperatorPublicId": "42419156-DD57-4737-8373-20678CD9AA29",
    "isDataBundle": False,
})
# purchase.responseCode -> "0" means success; check transaction status if needed
```

## License

GPL-3.0 (see [LICENSE](LICENSE))
