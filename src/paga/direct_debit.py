"""Direct Debit (Open Banking) operations for the Paga Engine API.

Direct Debit lets a customer authorise you to debit their bank account. The
flow is:

1. Start a hosted set-up session (or create a mandate by API) and send the
   customer to the returned checkout URL.
2. Paga calls your mandate callback once the bank responds. Read the
   mandate's ``ProcessStatusId`` — it becomes ``APPROVED`` only when the
   customer has genuinely authorised the debit.
3. Charge the mandate. A successful charge means *accepted*, not completed.
4. Wait for the charge callback before you fulfil.

Only charge a mandate whose ``ProcessStatusId`` is ``APPROVED``.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .auth import (
    CHARGE_MANDATE_HASH_FIELDS,
    CHARGE_MANDATE_STATUS_HASH_FIELDS,
    DISABLE_MANDATE_HASH_FIELDS,
    MANDATE_STATUS_HASH_FIELDS,
    PAYMENT_REQUEST_HASH_FIELDS,
)
from .models import (
    ChargeMandateResponse,
    ChargeMandateStatusResponse,
    DisableMandateResponse,
    DirectDebitSessionResponse,
    MandateStatusResponse,
)

__all__ = ["DirectDebitMixin"]


class DirectDebitMixin:
    """Direct Debit (Open Banking) operations."""

    async def start_direct_debit_session(
        self,
        *,
        reference_number: str,
        account_reference: str,
        amount_limit: float,
        callback_url: str,
        redirect_url: Optional[str] = None,
        session_expiry_seconds: Optional[str] = None,
        payment_expiry_seconds: Optional[str] = None,
        payer_phone_number: Optional[str] = None,
        payer_email: Optional[str] = None,
        authorization_amount: Optional[float] = None,
    ) -> DirectDebitSessionResponse:
        """Start a hosted Direct Debit set-up session.

        Operation: Direct Debit - Start a hosted set-up session.

        Creates a hosted session and returns the ``checkoutUrl`` to redirect
        your customer to. This endpoint uses HTTP Basic only — it sends no
        ``hash`` header.

        Args:
            reference_number: Your unique reference for this request.
            account_reference: Your permanent ID for the customer whose
                mandate is being set up.
            amount_limit: The maximum amount you may debit under the
                mandate.
            callback_url: Where Paga sends the mandate callback.
            redirect_url: Where to send the customer after the session.
            session_expiry_seconds: How long the session stays open, as a
                string of seconds (e.g. ``"50000"``).
            payment_expiry_seconds: How long the mandate stays valid, as a
                string of seconds (e.g. ``"157680000"`` for five years).
            payer_phone_number: Optional payer phone number.
            payer_email: Optional payer email address.
            authorization_amount: Optional initial authorisation amount.

        Returns:
            The parsed :class:`DirectDebitSessionResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "accountReference": account_reference,
            "amountLimit": amount_limit,
            "paymentMethods": ["BANK_ACCOUNT_DIRECT_DEBIT"],
            "callbackUrl": callback_url,
        }
        if redirect_url is not None:
            payload["redirectUrl"] = redirect_url
        if session_expiry_seconds is not None:
            payload["sessionExpirySeconds"] = session_expiry_seconds
        if payment_expiry_seconds is not None:
            payload["paymentExpirySeconds"] = payment_expiry_seconds
        additional: Dict[str, Any] = {}
        if payer_phone_number is not None:
            additional["payerPhoneNumber"] = payer_phone_number
        if payer_email is not None:
            additional["payerEmail"] = payer_email
        if authorization_amount is not None:
            additional["authorizationAmount"] = authorization_amount
        if additional:
            payload["additionalProperties"] = additional

        response = await self._request(
            "POST",
            "/checkout/charge-process/start",
            payload,
            use_hash=False,
            use_basic=True,
            base_url=self.checkout_base_url,
        )
        return DirectDebitSessionResponse.model_validate(response.model_dump())

    async def create_direct_debit_mandate(
        self,
        *,
        reference_number: str,
        amount: float,
        payer_name: str,
        payer_phone_number: str,
        payee_name: str,
        account_reference: str,
        currency: str = "NGN",
        payer_email: Optional[str] = None,
        payer_address: Optional[str] = None,
        payer_bank_id: Optional[str] = None,
        payer_bank_account_number: Optional[str] = None,
        payer_currency: Optional[str] = None,
        call_back_url: Optional[str] = None,
        redirect_url: Optional[str] = None,
        narration: Optional[str] = None,
        expiry_date_time_utc: Optional[str] = None,
        is_single_use: bool = True,
        is_allow_partial_payments: bool = False,
        is_allow_over_payments: bool = False,
        is_suppress_messages: bool = False,
        payer_collection_fee_share: float = 1,
        payee_collection_fee_share: float = 0,
    ) -> PagaResponse:
        """Set up a mandate by API, without a hosted session.

        Operation: Direct Debit - Set up a mandate by API.

        Creates a payment request with ``paymentMethods`` set to
        ``["DIRECT_DEBIT"]``.

        The authorisation transfer must come from mobile banking, internet
        banking or a branch — not from POS, USSD or ATM.

        ``payerCollectionFeeShare`` and ``payeeCollectionFeeShare`` must sum
        to 1.0.

        Args:
            reference_number: Your unique reference. At most 50 characters.
            amount: The amount to authorise.
            payer_name: Customer's name.
            payer_phone_number: Customer's phone number.
            payee_name: Your business name.
            account_reference: Your permanent ID for the customer.
            currency: Currency of the transaction. Defaults to ``"NGN"``.
            payer_email: Customer's email address. Optional.
            payer_address: Customer's address. Optional.
            payer_bank_id: The customer's bank UUID. Optional.
            payer_bank_account_number: The customer's account number. Optional.
            payer_currency: The payer's currency. Optional.
            call_back_url: Where Paga sends the mandate callback. Optional.
            redirect_url: Where to send the customer after the flow. Optional.
            narration: Optional narration.
            expiry_date_time_utc: When the mandate expires, in UTC. Optional.
            is_single_use: Whether the mandate may be charged only once.
                Defaults to ``True``. Set it to ``False`` for mandates that
                last more than 30 days.
            is_allow_partial_payments: Whether partial payments are allowed.
            is_allow_over_payments: Whether over-payments are allowed.
            is_suppress_messages: Whether to suppress emails and SMS.
            payer_collection_fee_share: Share of the fee the customer pays.
            payee_collection_fee_share: Share of the fee the business pays.

        Returns:
            The parsed :class:`PagaResponse`.
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

        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "currency": currency,
            "accountReference": account_reference,
            "payer": payer,
            "payee": {"name": payee_name},
            "paymentMethods": ["DIRECT_DEBIT"],
            "isSingleUse": is_single_use,
            "isAllowPartialPayments": is_allow_partial_payments,
            "isAllowOverPayments": is_allow_over_payments,
            "payerCollectionFeeShare": payer_collection_fee_share,
            "payeeCollectionFeeShare": payee_collection_fee_share,
        }
        if call_back_url is not None:
            payload["callBackUrl"] = call_back_url
        if redirect_url is not None:
            payload["redirectUrl"] = redirect_url
        if narration is not None:
            payload["narration"] = narration
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
            hash_fields=PAYMENT_REQUEST_HASH_FIELDS,
        )
        return response

    async def get_mandate_status(self, *, reference_number: str) -> MandateStatusResponse:
        """Check a mandate's status.

        Operation: Direct Debit - Check mandate status.

        Read ``mandateStatus`` (``ProcessStatusId``) from the response:
        ``PENDING``, ``VERIFIED``, ``APPROVED`` or ``REJECTED``. The response's
        own ``data.statusCode`` stays ``"1"`` / ``"pending"`` forever and tells
        you nothing.

        Args:
            reference_number: The ``referenceNumber`` of the mandate.

        Returns:
            The parsed :class:`MandateStatusResponse`.
        """
        response = await self._request(
            "POST",
            "/status",
            {"referenceNumber": reference_number},
            use_hash=True,
            use_basic=True,
            hash_fields=MANDATE_STATUS_HASH_FIELDS,
            raise_on_error=False,
        )
        return MandateStatusResponse.model_validate(response.model_dump())

    async def charge_mandate(
        self,
        *,
        reference_number: str,
        amount: float,
        account_reference: str,
    ) -> ChargeMandateResponse:
        """Charge an approved mandate.

        Operation: Direct Debit - Charge the mandate.

        Debits an approved mandate for any amount up to its limit. A
        successful response means the charge was **accepted**, not completed —
        fulfil only once the charge callback confirms it.

        Args:
            reference_number: Your unique reference for this charge.
            amount: The amount to debit. Must not exceed the mandate's limit.
            account_reference: The mandate's ``accountReference``.

        Returns:
            The parsed :class:`ChargeMandateResponse`.
        """
        response = await self._request(
            "POST",
            "/chargeDebitMandate",
            {
                "referenceNumber": reference_number,
                "amount": amount,
                "accountReference": account_reference,
            },
            use_hash=True,
            use_basic=True,
            hash_fields=CHARGE_MANDATE_HASH_FIELDS,
        )
        return ChargeMandateResponse.model_validate(response.model_dump())

    async def get_charge_mandate_status(
        self,
        *,
        reference_number: str,
    ) -> ChargeMandateStatusResponse:
        """Check a mandate charge's status.

        Operation: Direct Debit - Check charge status.

        Args:
            reference_number: The **charge's** ``referenceNumber``.

        Returns:
            The parsed :class:`ChargeMandateStatusResponse`. ``chargeStatus``
            is ``0`` charged, ``1`` pending, ``-1`` invalid and ``-4`` unknown.
        """
        response = await self._request(
            "POST",
            "/getChargeMandateStatus",
            {"referenceNumber": reference_number},
            use_hash=True,
            use_basic=True,
            hash_fields=CHARGE_MANDATE_STATUS_HASH_FIELDS,
            raise_on_error=False,
        )
        return ChargeMandateStatusResponse.model_validate(response.model_dump())

    async def disable_mandate(
        self,
        *,
        reference_number: str,
        account_reference: str,
    ) -> DisableMandateResponse:
        """Disable a mandate.

        Operation: Direct Debit - Disable a mandate.

        Stops all future charges on a mandate. Its ``ProcessStatusId`` then
        becomes ``REJECTED``, and it can never be charged again.

        Args:
            reference_number: Your unique reference for this request.
            account_reference: The mandate's ``accountReference``.

        Returns:
            The parsed :class:`DisableMandateResponse`.
        """
        response = await self._request(
            "POST",
            "/disableMandate",
            {
                "referenceNumber": reference_number,
                "accountReference": account_reference,
            },
            use_hash=True,
            use_basic=True,
            hash_fields=DISABLE_MANDATE_HASH_FIELDS,
        )
        return DisableMandateResponse.model_validate(response.model_dump())
