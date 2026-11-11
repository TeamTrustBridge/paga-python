"""Status code and outcome classification tests."""

from __future__ import annotations

from typing import Any, Dict

import pytest

from paga.codes import (
    BusinessErrorCode,
    ChargeStatusCode,
    CollectStatusCode,
    MandateProcessStatus,
    MandateStatusCode,
    resolve_business_code,
    resolve_collect_status,
)
from paga.exceptions import PagaAPIError
from paga.outcome import OperationOutcome, classify, is_unknown_outcome


@pytest.mark.parametrize(
    "body,expected",
    [
        ({"statusCode": "0"}, CollectStatusCode.SUCCESS),
        ({"statusCode": "1"}, CollectStatusCode.IN_PROCESS),
        ({"statusCode": "2"}, CollectStatusCode.PARTIAL_PAYMENT),
        ({"statusCode": "-1"}, CollectStatusCode.SYSTEM_ERROR),
        ({"statusCode": "-2"}, CollectStatusCode.REQUEST_EXPIRED),
        ({"statusCode": "-3"}, CollectStatusCode.REQUEST_CANCELLED),
        ({"statusCode": "114"}, CollectStatusCode.FAILED),
        ({"statusCode": "115"}, CollectStatusCode.FAILED_NON_REFUNDABLE),
        ({"statusCode": "121"}, CollectStatusCode.NOT_FOUND),
    ],
)
def test_collect_status_codes_resolve(body: Dict[str, Any], expected: CollectStatusCode) -> None:
    assert resolve_collect_status(body) is expected


def test_collect_status_accepts_integer_status_code() -> None:
    """Some legacy responses send ``statusCode`` as an integer."""
    assert resolve_collect_status({"statusCode": 0}) is CollectStatusCode.SUCCESS


def test_unrecognised_collect_status_resolves_to_none() -> None:
    """An unknown code must not raise."""
    assert resolve_collect_status({"statusCode": "999"}) is None


@pytest.mark.parametrize(
    "raw,expected",
    [
        (0, BusinessErrorCode.SUCCESS),
        (1, BusinessErrorCode.BULK_PARTIAL_SUCCESS),
        (3, BusinessErrorCode.PENDING),
        (-1, BusinessErrorCode.UNKNOWN_ERROR),
        (105, BusinessErrorCode.DUPLICATE_REFERENCE),
        (135, BusinessErrorCode.UNKNOWN_REFERENCE_NUMBER),
        (139, BusinessErrorCode.INSUFFICIENT_BALANCE),
    ],
)
def test_business_error_codes_resolve(raw: int, expected: BusinessErrorCode) -> None:
    assert resolve_business_code({"responseCode": raw}) is expected


@pytest.mark.parametrize(
    "body,expected",
    [
        ({"statusCode": "0"}, OperationOutcome.SUCCESS),
        ({"statusCode": "1"}, OperationOutcome.PENDING),
        ({"statusCode": "2"}, OperationOutcome.PARTIAL),
        ({"statusCode": "-1"}, OperationOutcome.UNKNOWN),
        ({"statusCode": "-2"}, OperationOutcome.FAILED),
        ({"statusCode": "-3"}, OperationOutcome.FAILED),
        ({"statusCode": "114"}, OperationOutcome.FAILED),
        ({"statusCode": "121"}, OperationOutcome.FAILED),
        ({"responseCode": 0}, OperationOutcome.SUCCESS),
        ({"responseCode": 1}, OperationOutcome.SUCCESS),
        ({"responseCode": 3}, OperationOutcome.PENDING),
        ({"responseCode": -1}, OperationOutcome.UNKNOWN),
        ({"responseCode": 105}, OperationOutcome.UNKNOWN),
        ({"responseCode": 135}, OperationOutcome.UNKNOWN),
        ({"responseCode": 2}, OperationOutcome.FAILED),
        ({"responseCode": 139}, OperationOutcome.FAILED),
        ({"responseCode": -2}, OperationOutcome.FAILED),
    ],
)
def test_classify(body: Dict[str, Any], expected: OperationOutcome) -> None:
    assert classify(body) is expected


def test_classify_without_a_code_is_unknown() -> None:
    """A body with no code tells us nothing."""
    assert classify({"message": "ok"}) is OperationOutcome.UNKNOWN
    assert classify(None) is OperationOutcome.UNKNOWN


def test_unknown_outcome_codes_are_flagged() -> None:
    """The three Business "unknown outcome" codes are flagged as such."""
    assert is_unknown_outcome({"responseCode": -1}) is True
    assert is_unknown_outcome({"responseCode": 105}) is True
    assert is_unknown_outcome({"responseCode": 135}) is True
    assert is_unknown_outcome({"responseCode": 139}) is False


def test_error_carries_the_resolved_code_and_outcome() -> None:
    """``PagaAPIError`` exposes the code and the classified outcome."""
    error = PagaAPIError(
        message="Duplicate reference",
        response_code=105,
        payload={"responseCode": 105, "message": "Duplicate reference"},
    )
    assert error.code is BusinessErrorCode.DUPLICATE_REFERENCE
    assert error.outcome is OperationOutcome.UNKNOWN
    assert error.is_unknown_outcome is True


def test_error_string_includes_the_code() -> None:
    """The string form names the failing code."""
    error = PagaAPIError(message="Insufficient balance", payload={"responseCode": 139})
    assert "139" in str(error)
    assert "failed" in str(error)


def test_error_without_a_payload_still_constructs() -> None:
    """A payload-less error keeps working."""
    error = PagaAPIError(message="boom")
    assert error.code is None
    assert error.outcome is OperationOutcome.UNKNOWN


def test_mandate_and_charge_enums_expose_the_documented_values() -> None:
    """The Direct Debit vocabularies match the documentation."""
    assert MandateStatusCode.APPROVED.value == "0"
    assert MandateStatusCode.VERIFIED.value == "004"
    assert MandateProcessStatus.APPROVED.value == "APPROVED"
    assert ChargeStatusCode.CHARGED.value == 0
    assert ChargeStatusCode.INVALID.value == -1
    assert ChargeStatusCode.UNKNOWN.value == -4
