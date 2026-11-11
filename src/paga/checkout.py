"""Checkout operations for the Paga Engine API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .auth import PAYMENT_STATUS_HASH_FIELDS
from .models import (
    CheckoutVerifyChargeResponse,
    CollectPaymentRequestResponse,
    PagaResponse,
    PaymentStatusResponse,
)


class CheckoutMixin:
    """Payment checkout operations."""

    async def create_payment(
        self,
        *,
        reference_number: str,
        amount: float,
        payer_name: str,
        payer_phone_number: str,
        payee_name: str,
        currency: str = "NGN",
        payer_email: Optional[str] = None,
        call_back_url: Optional[str] = None,
        payment_methods: Optional[List[str]] = None,
        expiry_date_time_utc: Optional[str] = None,
        is_suppress_messages: bool = False,
        payer_collection_fee_share: float = 1,
        payee_collection_fee_share: float = 0,
    ) -> CollectPaymentRequestResponse:
        """Create a Paga payment request.

        Operation: Dynamic virtual account - Create a payment request.

        The customer pays via the payment methods supplied (e.g. bank transfer
        with a one-time Paga virtual account number). Paga sends a callback to
        the configured ``callBackUrl`` when the payment completes.

        Args:
            reference_number: Your unique payment request reference.
            amount: Amount to request, in the major currency unit.
            payer_name: Customer's name.
            payer_phone_number: Customer's phone number.
            payee_name: Your business name, shown to the customer.
            currency: Currency of the transaction. Defaults to ``"NGN"``.
            payer_email: Customer's email address. Optional.
            call_back_url: Where Paga sends the callback. Optional.
            payment_methods: Payment methods to accept. Defaults to
                ``["BANK_TRANSFER"]``.
            expiry_date_time_utc: When the request expires, in UTC. Optional.
            is_suppress_messages: Whether Paga should suppress emails/SMS. Defaults
                to ``False``.
            payer_collection_fee_share: Share of the fee the customer pays. Defaults
                to ``1``.
            payee_collection_fee_share: Share of the fee the business pays. Defaults
                to ``0``.

        Returns:
            The parsed :class:`CollectPaymentRequestResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "currency": currency,
            "payer": {
                "name": payer_name,
                "phoneNumber": payer_phone_number,
            },
            "payee": {"name": payee_name},
            "payerCollectionFeeShare": payer_collection_fee_share,
            "payeeCollectionFeeShare": payee_collection_fee_share,
            "paymentMethods": payment_methods or ["BANK_TRANSFER"],
        }
        if payer_email is not None:
            payload["payer"]["email"] = payer_email
        if call_back_url is not None:
            payload["callBackUrl"] = call_back_url
        if expiry_date_time_utc is not None:
            payload["expiryDateTimeUTC"] = expiry_date_time_utc
        if is_suppress_messages:
            payload["isSuppressMessages"] = True

        response = await self._request(
            "POST",
            "/paymentRequest",
            payload,
            use_hash=True,
            use_basic=True,
        )
        return CollectPaymentRequestResponse.model_validate(response.model_dump())

    async def get_payment_status(self, *, reference_number: str) -> PaymentStatusResponse:
        """Check the status of a payment request.

        Operation: Dynamic virtual account - Check payment status.

        The outer ``statusCode`` only says whether the status request worked;
        the payment's own status is in ``data.statusCode``.

        Args:
            reference_number: The ``referenceNumber`` of the payment request.

        Returns:
            The parsed :class:`PaymentStatusResponse`.
        """
        response = await self._request(
            "POST",
            "/status",
            {"referenceNumber": reference_number},
            use_hash=True,
            use_basic=True,
            hash_fields=PAYMENT_STATUS_HASH_FIELDS,
        )
        return PaymentStatusResponse.model_validate(response.model_dump())

    async def verify_charge(
        self,
        *,
        payment_reference: str,
        public_key: str,
        amount: float,
        currency: str = "NGN",
    ) -> CheckoutVerifyChargeResponse:
        """Verify a checkout charge.

        Confirms a Checkout payment from your server at any time using its
        ``paymentReference``. Uses HTTP Basic auth only.

        - ``status_code`` of ``0`` means paid.
        - ``status_code`` of ``2`` means pending.

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
        )
        return CheckoutVerifyChargeResponse.model_validate(response.model_dump())
