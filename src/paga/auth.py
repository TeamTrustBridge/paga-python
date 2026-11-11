"""Authentication and hash helpers for the Paga Engine API."""

from __future__ import annotations

import hashlib
from typing import Any, Mapping, Optional, Sequence, Union

HashKeyInput = Union[Mapping[str, Any], Sequence[tuple], None]

DEFAULT_HASH_ALGORITHM = "sha512"

# Hash fields for the Dynamic virtual account "Create a payment request" operation.
PAYMENT_REQUEST_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "currency",
    "payer.phoneNumber",
    "payer.email",
)

# The longer hash field order Paga's Collect API operations page lists for the
# payment request operation, which adds the payee fields. Use it with
# ``create_payment(..., hash_fields=PAYMENT_REQUEST_FULL_HASH_FIELDS)``.
PAYMENT_REQUEST_FULL_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "currency",
    "payer.phoneNumber",
    "payer.email",
    "payee.accountNumber",
    "payee.phoneNumber",
    "payee.bankId",
    "payee.bankAccountNumber",
)

# Hash fields for the Bill payment - Pay the bill operation.
BILL_PAYMENT_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "merchantAccount",
    "merchantReferenceNumber",
)

# Hash fields for the Airtime and data - Buy the airtime or data operation.
AIRTIME_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "destinationPhoneNumber",
)

# Hash fields for the Money transfer - Send the money operation.
MONEY_TRANSFER_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "destinationBankUUID",
    "destinationBankAccountNumber",
)

# Hash fields for the Check your business account balance operation.
ACCOUNT_BALANCE_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Check payment status operation.
PAYMENT_STATUS_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Get your transaction history operation.
TRANSACTION_HISTORY_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Subsidiary Accounts - Create an account operation.
SUBSIDIARY_ACCOUNT_HASH_FIELDS: tuple = (
    "referenceNumber",
    "accountReference",
    "iifiNumber",
    "autoSweep.bankPublicId",
    "autoSweep.destination",
    "autoSweep.accountNumber",
    "callbackUrl",
)

# Hash fields for the Subsidiary Accounts - Charge an account operation.
SUBSIDIARY_CHARGE_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "currency",
    "narration",
)

# Hash fields for the Subsidiary Accounts - Top up an account operation.
SUBSIDIARY_TOPUP_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "currency",
    "narration",
)

# Hash fields for the Subsidiary Accounts - Transfer between accounts operation.
SUBSIDIARY_TRANSFER_HASH_FIELDS: tuple = (
    "referenceNumber",
    "sourceAccountIdentifier",
    "destinationAccountIdentifier",
    "amount",
    "currency",
    "narration",
)

# Hash fields for the Subsidiary Accounts - Retrieve an account operation.
SUBSIDIARY_RETRIEVE_HASH_FIELDS: tuple = (
    "referenceNumber",
    "accountIdentifier",
)

# Hash fields for the Subsidiary Accounts - Update an account operation.
SUBSIDIARY_UPDATE_HASH_FIELDS: tuple = (
    "referenceNumber",
    "accountIdentifier",
    "iifiNumber",
    "autoSweep.destination",
    "autoSweep.bankPublicId",
    "autoSweep.accountNumber",
    "callbackUrl",
)

# Hash fields for the Subsidiary Accounts - Get the balance operation.
SUBSIDIARY_BALANCE_HASH_FIELDS: tuple = (
    "referenceNumber",
    "accountIdentifier",
)

# Hash fields for the Subsidiary Accounts - Get transaction history operation.
SUBSIDIARY_HISTORY_HASH_FIELDS: tuple = (
    "accountIdentifier",
    "startDateTimeUTC",
    "endDateTimeUTC",
)

# Hash fields for the Subsidiary Accounts - Handle a funding notification operation.
SUBSIDIARY_FUNDING_HASH_FIELDS: tuple = (
    "transactionReference",
    "transactionDate",
    "amount",
    "accountNumber",
    "timestamp",
)

# Hash fields for the Subsidiary Accounts - Handle a charge, top-up or transfer callback operation.
SUBSIDIARY_OPERATION_HASH_FIELDS: tuple = (
    "externalReferenceNumber",
    "transactionDate",
    "amount",
    "accountNumber",
)


# Hash fields for the Refunds - Refund or cancel a payment request operation.
REFUND_HASH_FIELDS: tuple = (
    "referenceNumber",
    "refundAmount",
)

# Hash fields for the Payment callback ("Handle the callback") operation.
PAYMENT_CALLBACK_HASH_FIELDS: tuple = (
    "notificationId",
    "statusCode",
    "externalReferenceNumber",
    "state",
    "outstandingBalance",
)


# --------------------------------------------------------------------------- #
# Directory lookups
# --------------------------------------------------------------------------- #

# Hash fields for the Bank USSD - Get the customer's bank operation.
COLLECT_BANKS_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Money transfer - Get the bank's UUID operation.
BANKS_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Airtime and data - Get the mobile operator operation.
MOBILE_OPERATORS_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Airtime and data - For data, pick a bundle operation.
DATA_BUNDLE_HASH_FIELDS: tuple = (
    "referenceNumber",
    "operatorPublicId",
)

# Hash fields for the Bill payment - Find the biller operation.
MERCHANTS_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Bill payment - Pick the service operation.
MERCHANT_SERVICES_HASH_FIELDS: tuple = (
    "referenceNumber",
    "merchantPublicId",
)

# Hash fields for the Bill payment - Validate the customer operation.
MERCHANT_ACCOUNT_DETAILS_HASH_FIELDS: tuple = (
    "referenceNumber",
    "merchantAccount",
    "merchantReferenceNumber",
    "merchantServiceProductCode",
)

# Hash fields for the Money transfer - Validate the account operation.
VALIDATE_DEPOSIT_TO_BANK_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "destinationBankUUID",
    "destinationBankAccountNumber",
)


# --------------------------------------------------------------------------- #
# Status lookups
# --------------------------------------------------------------------------- #

# Hash fields for the Money transfer / Airtime / Bill payment - Check the
# transaction status operation.
TRANSACTION_STATUS_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Business account - Get your recent transactions operation.
RECENT_TRANSACTION_HISTORY_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the USD bank transfer - Check payment status operation.
# Unlike the other /status operations, this one signs the currency too.
USD_PAYMENT_STATUS_HASH_FIELDS: tuple = (
    "referenceNumber",
    "paymentCurrency",
)


# --------------------------------------------------------------------------- #
# Direct Debit (Open Banking)
# --------------------------------------------------------------------------- #

# Hash fields for the Direct Debit - Charge the mandate operation.
CHARGE_MANDATE_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "accountReference",
)

# Hash fields for the Direct Debit - Disable a mandate operation.
DISABLE_MANDATE_HASH_FIELDS: tuple = (
    "referenceNumber",
    "accountReference",
)

# Hash fields for the Direct Debit - Check charge status operation.
CHARGE_MANDATE_STATUS_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Direct Debit - Check mandate status operation.
MANDATE_STATUS_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Direct Debit mandate callback.
# The timeStamp carries nanosecond precision and must be hashed exactly as
# received, never re-serialised.
MANDATE_CALLBACK_HASH_FIELDS: tuple = (
    "statusCode",
    "timeStamp",
    "accountNumber",
    "bankName",
    "referenceNumber",
    "mandateStatus",
)

# Hash fields for the Direct Debit charge callback. The amount is a string
# with two decimals and no commas, such as "600.00".
CHARGE_CALLBACK_HASH_FIELDS: tuple = (
    "statusCode",
    "referenceNumber",
    "accountReference",
    "amount",
)


# --------------------------------------------------------------------------- #
# Persistent payment accounts
# --------------------------------------------------------------------------- #

# Hash fields for the Collect API - Register a persistent payment account
# operation.
REGISTER_PERSISTENT_ACCOUNT_HASH_FIELDS: tuple = (
    "referenceNumber",
    "accountReference",
    "financialIdentificationNumber",
    "creditBankId",
    "creditBankAccountNumber",
    "callbackUrl",
)

# Hash fields for the Collect API - Delete a persistent payment account
# operation.
DELETE_PERSISTENT_ACCOUNT_HASH_FIELDS: tuple = (
    "referenceNumber",
    "accountIdentifier",
)

# Hash fields for the Collect API - Update a persistent payment account
# operation.
UPDATE_PERSISTENT_ACCOUNT_HASH_FIELDS: tuple = (
    "referenceNumber",
    "accountIdentifier",
    "financialIdentificationNumber",
    "creditBankId",
    "creditBankAccountNumber",
    "callbackUrl",
)

# Hash fields for the Collect API - Get a persistent payment account operation.
GET_PERSISTENT_ACCOUNT_HASH_FIELDS: tuple = (
    "referenceNumber",
    "accountIdentifier",
)

# Hash fields for the Collect API - Payment request history operation.
HISTORY_HASH_FIELDS: tuple = (
    "referenceNumber",
)


# --------------------------------------------------------------------------- #
# Customer registration
# --------------------------------------------------------------------------- #

# Hash fields for the Business API - Register a customer operation.
CUSTOMER_HASH_FIELDS: tuple = (
    "referenceNumber",
    "customerPhoneNumber",
    "customerFirstName",
    "customerLastName",
)

# Hash fields for the Business API - Register a customer account photo
# operation.
CUSTOMER_ACCOUNT_PHOTO_HASH_FIELDS: tuple = (
    "referenceNumber",
    "customerPhoneNumber",
)

# Hash fields for the Business API - Register a customer identification
# operation.
CUSTOMER_IDENTIFICATION_HASH_FIELDS: tuple = (
    "referenceNumber",
    "customerPhoneNumber",
    "customerIdType",
    "customerIdNumber",
    "customerIdExpirationDate",
)


# --------------------------------------------------------------------------- #
# Additional Business API operations
# --------------------------------------------------------------------------- #

# Hash fields for the Business API - Money transfer to a Paga wallet operation.
# Distinct from MONEY_TRANSFER_HASH_FIELDS, which signs a transfer to a
# bank account.
PAGA_WALLET_TRANSFER_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "destinationAccount",
)

# Hash fields for the Business API - Validate a money transfer operation.
VALIDATE_MONEY_TRANSFER_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "destinationAccount",
)

# Hash fields for the Business API - Bulk money transfer operation. The hash
# covers the first item's fields plus the total number of items.
MONEY_TRANSFER_BULK_HASH_FIELDS: tuple = (
    "referenceNumber",
    "amount",
    "destinationAccount",
    "itemCount",
)

# Hash fields for the Business API - Get an operation's status operation.
GET_OPERATION_STATUS_HASH_FIELDS: tuple = (
    "referenceNumber",
)

# Hash fields for the Business API - Onboard a merchant operation.
ONBOARD_MERCHANT_HASH_FIELDS: tuple = (
    "referenceNumber",
    "merchantExternalId",
    "name",
    "phone",
    "email",
)

# Hash fields for the Business API - Dispense cash operation.
DISPENSE_CASH_HASH_FIELDS: tuple = (
    "referenceNumber",
    "customerPhoneNumber",
    "amount",
    "withdrawalCode",
)


def _resolve_value(payload: Any, path: str) -> Any:
    """Resolve a possibly dotted field path (e.g. ``payer.phoneNumber``) on a payload."""
    node: Any = payload
    for key in path.split("."):
        node = node.get(key) if isinstance(node, Mapping) else None
    return node


def _field_to_text(value: Any, field: str) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return str(value)
    if isinstance(value, (int, float)):
        # Money fields are formatted with two decimal places and no commas.
        if field.endswith("Balance"):
            return f"{float(value):.2f}"
        return str(value)
    return str(value)


def generate_hash(
    payload: HashKeyInput,
    hash_key: str,
    *,
    algorithm: str = DEFAULT_HASH_ALGORITHM,
    fields: Optional[Sequence[str]] = None,
) -> str:
    """Generate the Paga request hash.

    The hash is the SHA-512 hex digest of the concatenated hash field values
    (in field order) followed by the business hash key.

    Args:
        payload: Request payload (mapping) or ordered ``(key, value)`` pairs.
        hash_key: Business hash key provided by Paga.
        algorithm: Hash algorithm name accepted by :func:`hashlib.new`.
        fields: Ordered hash field paths. Defaults to the payment request hash
            fields.

    Returns:
        The computed hash string (lowercase hex).
    """
    if payload is None:
        items: list = []
    elif isinstance(payload, Mapping):
        items = list(payload.items())
    else:
        items = [(str(key), value) for key, value in payload]

    field_tuple = tuple(fields) if fields is not None else PAYMENT_REQUEST_HASH_FIELDS
    parts = [_field_to_text(_resolve_value(payload, field), field) for field in field_tuple]
    message = "".join(parts) + str(hash_key)
    return hashlib.new(algorithm, message.encode("utf-8")).hexdigest()


class PagaAuth:
    """Holds business credentials and builds request auth material."""

    def __init__(self, public_id: str, credentials: str, hash_key: str) -> None:
        self.public_id = public_id
        self.credentials = credentials
        self.hash_key = hash_key

    def build_headers(
        self,
        payload: Optional[Mapping[str, Any]] = None,
        *,
        hash_fields: Optional[Sequence[str]] = None,
    ) -> dict:
        """Build headers for hash-based (secured) Paga endpoints."""
        return {
            "principal": self.public_id,
            "credentials": self.credentials,
            "hash": generate_hash(payload or {}, self.hash_key, fields=hash_fields),
        }

    def basic_auth(self) -> Any:
        """Build HTTP Basic auth for endpoints that use Basic auth only."""
        import httpx

        # Public key is used as username and secret key as password.
        return httpx.BasicAuth(self.public_id, self.credentials)
