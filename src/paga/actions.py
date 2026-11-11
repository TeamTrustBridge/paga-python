"""Action operations for the Paga Engine API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .auth import (
    AIRTIME_HASH_FIELDS,
    BILL_PAYMENT_HASH_FIELDS,
    MONEY_TRANSFER_HASH_FIELDS,
    REFUND_HASH_FIELDS,
)
from .models import (
    DepositToBankResponse,
    MerchantPaymentResponse,
    PagaResponse,
    PurchaseResponse,
    RefundResponse,
)


class ActionMixin:
    """Action operations: refunds, money transfers, airtime and bill payments."""

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

    async def send_money(
        self,
        *,
        reference_number: str,
        amount: str,
        destination_bank_uuid: str,
        destination_bank_account_number: str,
        currency: str = "NGN",
        remarks: Optional[str] = None,
        status_callback_url: Optional[str] = None,
    ) -> DepositToBankResponse:
        """Send money from the business balance to a bank account or Paga wallet.

        Operation: Money transfer - Send the money.

        Sends money from the business balance to a bank account, or to a Paga
        wallet (using Paga's UUID ``AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA``).

        Args:
            reference_number: Your unique transfer reference.
            amount: Amount to send (e.g. ``"5000.00"``).
            destination_bank_uuid: The bank's UUID from get banks, or Paga's UUID
                for a wallet.
            destination_bank_account_number: Destination bank account number.
            currency: Transaction currency. Defaults to ``"NGN"``.
            remarks: Optional transfer remarks.
            status_callback_url: Where Paga notifies once the transfer is processed. Optional.

        Returns:
            The parsed :class:`DepositToBankResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "currency": currency,
            "destinationBankUUID": destination_bank_uuid,
            "destinationBankAccountNumber": destination_bank_account_number,
        }
        if remarks is not None:
            payload["remarks"] = remarks
        if status_callback_url is not None:
            payload["statusCallbackUrl"] = status_callback_url
        response = await self._request(
            "POST",
            "/depositToBank",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=MONEY_TRANSFER_HASH_FIELDS,
            raise_on_error=False,
        )
        return DepositToBankResponse.model_validate(response.model_dump())

    async def buy_airtime(
        self,
        *,
        reference_number: str,
        amount: str,
        destination_phone_number: str,
        mobile_operator_public_id: str,
        currency: str = "NGN",
        is_data_bundle: bool = False,
        mobile_operator_service_id: Optional[str] = None,
        is_suppress_recipient_messages: bool = False,
    ) -> PurchaseResponse:
        """Buy airtime or data.

        Operation: Airtime and data - Buy the airtime or data.

        Tops up a phone with airtime or data from the business balance. There
        is no callback: decide on ``responseCode``, and check the transaction
        status if needed.

        Args:
            reference_number: Your unique airtime purchase reference.
            amount: Airtime value, or exactly the bundle's ``servicePrice`` for data.
            destination_phone_number: Phone number to credit.
            mobile_operator_public_id: The network's mobile operator public id.
            currency: Transaction currency. Defaults to ``"NGN"``.
            is_data_bundle: Whether this is a data bundle purchase. Defaults to ``False``.
            mobile_operator_service_id: Data only. The bundle's ``serviceId``.
            is_suppress_recipient_messages: Whether to suppress recipient messages.

        Returns:
            The parsed :class:`PurchaseResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "destinationPhoneNumber": destination_phone_number,
            "mobileOperatorPublicId": mobile_operator_public_id,
            "currency": currency,
            "isDataBundle": is_data_bundle,
        }
        if mobile_operator_service_id is not None:
            payload["mobileOperatorServiceId"] = mobile_operator_service_id
        if is_suppress_recipient_messages:
            payload["isSuppressRecipientMessages"] = True

        response = await self._request(
            "POST",
            "/airtimePurchase",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=AIRTIME_HASH_FIELDS,
            raise_on_error=False,
        )
        return PurchaseResponse.model_validate(response.model_dump())

    async def pay_bill(
        self,
        *,
        reference_number: str,
        amount: float,
        merchant_account: str,
        merchant_reference_number: str,
        merchant_service: Optional[List[str]] = None,
        currency: str = "NGN",
        payment_channel: Optional[str] = None,
        locale: Optional[str] = None,
        merchant_service_product_code: Optional[str] = None,
    ) -> MerchantPaymentResponse:
        """Pay a bill from the business balance.

        Operation: Bill payment - Pay the bill.

        Pays a bill from the business balance. There is no callback: decide on
        ``responseCode``. ``integrationStatus`` is for information only.

        Args:
            reference_number: Your unique bill payment reference.
            amount: Bill amount.
            merchant_account: The biller's UUID. From the biller lookup.
            merchant_reference_number: The customer's account / meter /
                smart card / account number at the biller.
            merchant_service: Optional chosen service code. Leave out for
                billers with no services.
            currency: Transaction currency. Defaults to ``"NGN"``.
            payment_channel: Optional payment channel.
            locale: Optional locale.
            merchant_service_product_code: Optional chosen service code, as
                returned by :meth:`get_merchant_services`.

        Returns:
            The parsed :class:`MerchantPaymentResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "merchantAccount": merchant_account,
            "merchantReferenceNumber": merchant_reference_number,
            "currency": currency,
        }
        if merchant_service is not None:
            payload["merchantService"] = merchant_service
        if payment_channel is not None:
            payload["paymentChannel"] = payment_channel
        if locale is not None:
            payload["locale"] = locale
        if merchant_service_product_code is not None:
            payload["merchantServiceProductCode"] = merchant_service_product_code
        response = await self._request(
            "POST",
            "/merchantPayment",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=BILL_PAYMENT_HASH_FIELDS,
            raise_on_error=False,
        )
        return MerchantPaymentResponse.model_validate(response.model_dump())
