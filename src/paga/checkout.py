"""Checkout operations for the Paga Engine API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .auth import PAYMENT_REQUEST_HASH_FIELDS, PAYMENT_STATUS_HASH_FIELDS
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
        payer_address: Optional[str] = None,
        payer_bank_id: Optional[str] = None,
        payer_bank_account_number: Optional[str] = None,
        payer_currency: Optional[str] = None,
        payee_account_number: Optional[str] = None,
        payee_phone_number: Optional[str] = None,
        payee_bank_id: Optional[str] = None,
        payee_bank_account_number: Optional[str] = None,
        is_single_use: Optional[bool] = None,
        is_allow_partial_payments: Optional[bool] = None,
        is_allow_over_payments: Optional[bool] = None,
        narration: Optional[str] = None,
        redirect_url: Optional[str] = None,
        hash_fields: Optional[tuple] = None,
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
            payer_address: Customer's address. Optional.
            payer_bank_id: The customer's bank UUID, for Bank USSD and
                Direct Debit. From :meth:`get_collect_banks`.
            payer_bank_account_number: The customer's account number. Optional.
            payer_currency: The payer's currency. Optional.
            payee_account_number: Your account number to be credited. Optional.
            payee_phone_number: Your phone number. Optional.
            payee_bank_id: Your bank's UUID. Optional.
            payee_bank_account_number: Your account number to be credited.
                Optional.
            is_single_use: Whether the request may be paid only once.
                Optional.
            is_allow_partial_payments: Whether partial payments are allowed.
                Optional.
            is_allow_over_payments: Whether over-payments are allowed. Optional.
            narration: Optional narration shown to the payer.
            redirect_url: Where to send the customer after the flow. Optional.
            hash_fields: Override the hash field order. The default signs
                ``referenceNumber + amount + currency + payer.phoneNumber +
                payer.email``. Paga's Collect API operations page also lists
                a variant that adds the ``payee`` fields — pass
                :data:`paga.auth.PAYMENT_REQUEST_FULL_HASH_FIELDS` for that
                one.

        Returns:
            The parsed :class:`CollectPaymentRequestResponse`.
        """
        payer: Dict[str, Any] = {
            "name": payer_name,
            "phoneNumber": payer_phone_number,
        }
        if payer_email is not None:
            payer["email"] = payer_email
        if payer_address is not None:
            payer["address"] = payer_address
        if payer_bank_id is not None:
            payer["bankId"] = payer_bank_id
        if payer_bank_account_number is not None:
            payer["bankAccountNumber"] = payer_bank_account_number
        if payer_currency is not None:
            payer["currency"] = payer_currency

        payee: Dict[str, Any] = {"name": payee_name}
        if payee_account_number is not None:
            payee["accountNumber"] = payee_account_number
        if payee_phone_number is not None:
            payee["phoneNumber"] = payee_phone_number
        if payee_bank_id is not None:
            payee["bankId"] = payee_bank_id
        if payee_bank_account_number is not None:
            payee["bankAccountNumber"] = payee_bank_account_number

        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "currency": currency,
            "payer": payer,
            "payee": payee,
            "payerCollectionFeeShare": payer_collection_fee_share,
            "payeeCollectionFeeShare": payee_collection_fee_share,
            "paymentMethods": payment_methods or ["BANK_TRANSFER"],
        }
        if call_back_url is not None:
            payload["callBackUrl"] = call_back_url
        if expiry_date_time_utc is not None:
            payload["expiryDateTimeUTC"] = expiry_date_time_utc
        if is_suppress_messages:
            payload["isSuppressMessages"] = True
        if is_single_use is not None:
            payload["isSingleUse"] = is_single_use
        if is_allow_partial_payments is not None:
            payload["isAllowPartialPayments"] = is_allow_partial_payments
        if is_allow_over_payments is not None:
            payload["isAllowOverPayments"] = is_allow_over_payments
        if narration is not None:
            payload["narration"] = narration
        if redirect_url is not None:
            payload["redirectUrl"] = redirect_url

        response = await self._request(
            "POST",
            "/paymentRequest",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=hash_fields or PAYMENT_REQUEST_HASH_FIELDS,
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
