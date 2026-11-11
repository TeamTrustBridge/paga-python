"""Shared transaction status operations for the Paga Engine API.

Covers the **Check the transaction status** operation that Paga documents
under money transfer, airtime and bill payment alike.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .auth import TRANSACTION_STATUS_HASH_FIELDS
from .models import TransactionStatusResponse

__all__ = ["StatusMixin"]


class StatusMixin:
    """Transaction status operations."""

    async def get_transaction_status(
        self,
        *,
        reference_number: str,
        locale: Optional[str] = None,
    ) -> TransactionStatusResponse:
        """Check what happened to a transaction you already sent.

        Operation: Money transfer / Airtime / Bill payment - Check the
        transaction status.

        Covers money transfers, airtime purchases and bill payments. Only the
        last 48 hours are covered. After a timeout or an ambiguous response,
        wait at least 5 seconds before the first check.

        The ``status`` field is human-readable and may be reworded at any
        time. Branch on ``responseCode``, not on ``status``.

        Args:
            reference_number: The reference number you sent the transaction
                with.
            locale: Optional locale.

        Returns:
            The parsed :class:`TransactionStatusResponse`.
        """
        payload: Dict[str, Any] = {"referenceNumber": reference_number}
        if locale is not None:
            payload["locale"] = locale

        response = await self._request(
            "POST",
            "/transactionStatus",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=TRANSACTION_STATUS_HASH_FIELDS,
            raise_on_error=False,
        )
        return TransactionStatusResponse.model_validate(response.model_dump())
