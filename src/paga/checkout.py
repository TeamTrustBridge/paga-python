"""Checkout operations for the Paga Engine API.

Covers the **Accept payments → Checkout** section of Paga's documentation.

Checkout takes a card or bank payment on a Paga-hosted page. The customer
redirects to Paga, pays, and Paga notifies your server.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .models import CheckoutVerifyChargeResponse

__all__ = ["CheckoutMixin"]


class CheckoutMixin:
    """Checkout operations."""

    async def verify_charge(
        self,
        *,
        payment_reference: str,
        public_key: str,
        amount: float,
        currency: str = "NGN",
    ) -> CheckoutVerifyChargeResponse:
        """Verify a checkout charge.

        Operation: Checkout - Verify a charge.

        Confirms a Checkout payment from your server at any time using its
        ``paymentReference``. Uses HTTP Basic only — it sends no ``hash``
        header.

        - ``status_code`` of ``0`` means paid.
        - ``status_code`` of ``2`` means pending.

        The response is returned rather than raised: a pending charge is a
        legitimate answer, so branch on ``status_code``.

        Args:
            payment_reference: The ``paymentReference`` of the charge to verify.
            public_key: The public key used for the checkout.
            amount: The amount to verify.
            currency: The currency of the charge. Defaults to ``"NGN"``.

        Returns:
            The parsed :class:`CheckoutVerifyChargeResponse`.
        """
        payload = {
            "paymentReference": payment_reference,
            "publicKey": public_key,
            "amount": amount,
            "currency": currency,
        }
        response = await self._request(
            "POST",
            "/checkout/transaction/verify",
            payload,
            use_hash=False,
            use_basic=True,
            base_url=self.checkout_base_url,
            raise_on_error=False,
        )
        return CheckoutVerifyChargeResponse.model_validate(response.model_dump())
