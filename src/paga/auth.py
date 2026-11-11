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
