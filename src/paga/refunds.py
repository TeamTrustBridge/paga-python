"""Refund operations for the Paga Engine API.

Covers the **Accept payments → Refunds** section of Paga's documentation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .auth import PAYMENT_STATUS_HASH_FIELDS, REFUND_HASH_FIELDS
from .models import RefundResponse, RefundStatusResponse

__all__ = ["RefundsMixin"]


class RefundsMixin:
    """Refund operations."""

    async def refund_payment(
        self,
        *,
        reference_number: str,
        payment_request_reference: str,
        refund_amount: float,
        currency: str = "NGN",
        reason: Optional[str] = None,
    ) -> RefundResponse:
        """Refund or cancel a payment request.

        Operation: Refunds - Refund or cancel a payment request.

        Refunds a paid payment request in full or in part, or cancels one that
        has not been paid. Send one request per partial refund, each with its
        own ``reference_number``. Reusing a ``reference_number`` returns status
        code ``102`` and never refunds twice.

        Args:
            reference_number: Your unique reference for this refund.
            payment_request_reference: The ``reference_number`` of the original
                payment request.
            refund_amount: Amount to refund.
            currency: Transaction currency. Defaults to ``"NGN"``.
            reason: Optional refund reason.

        Returns:
            The parsed :class:`RefundResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "paymentRequestReference": payment_request_reference,
            "refundAmount": refund_amount,
            "currency": currency,
        }
        if reason is not None:
            payload["reason"] = reason
        response = await self._request(
            "POST",
            "/refund/v2",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=REFUND_HASH_FIELDS,
        )
        return RefundResponse.model_validate(response.model_dump())

    async def get_refund_status(self, *, reference_number: str) -> RefundStatusResponse:
        """Check whether a payment request was refunded.

        Operation: Refunds - Check refund status.

        Call with the **original payment request's** ``referenceNumber``, not
        the refund's. ``refundStatus`` becomes ``"refunded"`` once the refund
        is made.

        Args:
            reference_number: The original payment request's reference number.

        Returns:
            The parsed :class:`RefundStatusResponse`.
        """
        response = await self._request(
            "POST",
            "/status",
            {"referenceNumber": reference_number},
            use_hash=True,
            use_basic=True,
            hash_fields=PAYMENT_STATUS_HASH_FIELDS,
            raise_on_error=False,
        )
        return RefundStatusResponse.model_validate(response.model_dump())
