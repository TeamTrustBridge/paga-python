"""Hash signing tests.

The digests in ``fixtures/hash_vectors.json`` are generated outside the SDK
(``printf '%s' "$message" | sha512sum``), so these tests pin the SDK's
byte-level behaviour rather than merely confirming it agrees with itself.
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, Mapping

import pytest

from paga.auth import (
    AIRTIME_HASH_FIELDS,
    BILL_PAYMENT_HASH_FIELDS,
    MONEY_TRANSFER_HASH_FIELDS,
    PAYMENT_CALLBACK_HASH_FIELDS,
    PAYMENT_REQUEST_HASH_FIELDS,
    REFUND_HASH_FIELDS,
    SUBSIDIARY_OPERATION_HASH_FIELDS,
    generate_hash,
)
from paga.webhooks import verify_hash


def _resolve(payload: Mapping[str, Any], path: str) -> str:
    """Resolve a dotted field path, mirroring the documented signing rule."""
    node: Any = payload
    for key in path.split("."):
        node = node.get(key) if isinstance(node, Mapping) else None
    if node is None:
        return ""
    if isinstance(node, bool):
        return str(node)
    if isinstance(node, float) and path.endswith("Balance"):
        return f"{node:.2f}"
    return str(node)


def _message(payload: Mapping[str, Any], fields: Any, hash_key: str) -> str:
    return "".join(_resolve(payload, field) for field in fields) + hash_key


def test_shared_vectors_sign_exactly(hash_vectors: Dict[str, Any]) -> None:
    """Every shared vector must sign to its recorded digest."""
    key = hash_vectors["hashKey"]
    for vector in hash_vectors["vectors"]:
        digest = generate_hash(vector["payload"], key, fields=vector["fields"])
        assert digest == vector["digest"], vector["name"]


def test_shared_vectors_concatenate_exactly(hash_vectors: Dict[str, Any]) -> None:
    """The signed message must match the recorded concatenation."""
    key = hash_vectors["hashKey"]
    for vector in hash_vectors["vectors"]:
        message = _message(vector["payload"], vector["fields"], key)
        assert message == vector["message"], vector["name"]
        assert hashlib.sha512(message.encode("utf-8")).hexdigest() == vector["digest"]


def test_hash_is_lowercase_hex_sha512(hash_vectors: Dict[str, Any]) -> None:
    """Paga expects a 128-character lowercase hex SHA-512 digest."""
    vector = hash_vectors["vectors"][0]
    digest = generate_hash(vector["payload"], hash_vectors["hashKey"], fields=vector["fields"])
    assert len(digest) == 128
    assert digest == digest.lower()
    assert all(char in "0123456789abcdef" for char in digest)


def test_missing_field_contributes_empty_string(hash_vectors: Dict[str, Any]) -> None:
    """An omitted field signs as empty, not as "None"."""
    key = hash_vectors["hashKey"]
    payload = {"referenceNumber": "REF-1", "amount": 100}
    digest = generate_hash(payload, key, fields=("referenceNumber", "amount", "currency"))
    expected = hashlib.sha512(("REF-1" + "100" + "" + key).encode("utf-8")).hexdigest()
    assert digest == expected


def test_nested_field_resolution() -> None:
    """Dotted paths resolve into nested objects."""
    key = "hashkey123"
    payload = {"referenceNumber": "REF-1", "payer": {"phoneNumber": "08031234567"}}
    digest = generate_hash(payload, key, fields=("referenceNumber", "payer.phoneNumber"))
    expected = hashlib.sha512(("REF-1" + "08031234567" + key).encode("utf-8")).hexdigest()
    assert digest == expected


def test_balance_field_is_formatted_to_two_decimals() -> None:
    """``outstandingBalance`` is signed as ``#.00``."""
    key = "hashkey123"
    payload = {"outstandingBalance": 1000.0}
    digest = generate_hash(payload, key, fields=("outstandingBalance",))
    expected = hashlib.sha512(("1000.00" + key).encode("utf-8")).hexdigest()
    assert digest == expected


def test_amount_string_is_not_reformatted() -> None:
    """A string amount is signed verbatim, commas and all."""
    key = "hashkey123"
    payload = {"amount": "1,000.00"}
    digest = generate_hash(payload, key, fields=("amount",))
    expected = hashlib.sha512(("1,000.00" + key).encode("utf-8")).hexdigest()
    assert digest == expected


def test_hash_key_is_never_transmitted_but_is_signed() -> None:
    """The hash key is part of the signed message but never sent."""
    key = "hashkey123"
    payload = {"referenceNumber": "REF-1"}
    with_key = generate_hash(payload, key, fields=("referenceNumber",))
    without_key = generate_hash(payload, "", fields=("referenceNumber",))
    assert with_key != without_key
    assert "hashkey123" not in with_key


def test_field_order_matters() -> None:
    """Reordering the hash fields changes the digest."""
    key = "hashkey123"
    payload = {"referenceNumber": "REF-1", "amount": 100}
    forward = generate_hash(payload, key, fields=("referenceNumber", "amount"))
    backward = generate_hash(payload, key, fields=("amount", "referenceNumber"))
    assert forward != backward


@pytest.mark.parametrize(
    "constant,expected_prefix",
    [
        (PAYMENT_REQUEST_HASH_FIELDS, ("referenceNumber", "amount")),
        (BILL_PAYMENT_HASH_FIELDS, ("referenceNumber", "amount", "merchantAccount")),
        (AIRTIME_HASH_FIELDS, ("referenceNumber", "amount", "destinationPhoneNumber")),
        (MONEY_TRANSFER_HASH_FIELDS, ("referenceNumber", "amount", "destinationBankUUID")),
        (REFUND_HASH_FIELDS, ("referenceNumber", "refundAmount")),
        (PAYMENT_CALLBACK_HASH_FIELDS, ("notificationId", "statusCode")),
        (SUBSIDIARY_OPERATION_HASH_FIELDS, ("externalReferenceNumber", "transactionDate")),
    ],
)
def test_documented_hash_field_orders(constant: Any, expected_prefix: Any) -> None:
    """The shipped field orders must match Paga's documented order."""
    assert tuple(constant[: len(expected_prefix)]) == expected_prefix


def test_verify_hash_accepts_matching_digest() -> None:
    """``verify_hash`` accepts a correct digest."""
    key = "hashkey123"
    payload = {"referenceNumber": "REF-1"}
    digest = generate_hash(payload, key, fields=("referenceNumber",))
    assert verify_hash(payload, digest, key, fields=("referenceNumber",)) is True


def test_verify_hash_rejects_wrong_digest() -> None:
    """``verify_hash`` rejects a digest computed over a different payload."""
    key = "hashkey123"
    payload = {"referenceNumber": "REF-1"}
    digest = generate_hash({"referenceNumber": "REF-2"}, key, fields=("referenceNumber",))
    assert verify_hash(payload, digest, key, fields=("referenceNumber",)) is False


def test_verify_hash_rejects_digest_over_different_fields() -> None:
    """A digest signed over extra fields must not verify against fewer fields."""
    key = "hashkey123"
    payload = {"referenceNumber": "REF-1", "amount": 100}
    digest = generate_hash(payload, key, fields=("referenceNumber", "amount"))
    assert verify_hash(payload, digest, key, fields=("referenceNumber",)) is False


def test_verify_hash_is_case_insensitive() -> None:
    """An uppercase digest still verifies."""
    key = "hashkey123"
    payload = {"referenceNumber": "REF-1"}
    digest = generate_hash(payload, key, fields=("referenceNumber",)).upper()
    assert verify_hash(payload, digest, key, fields=("referenceNumber",)) is True
