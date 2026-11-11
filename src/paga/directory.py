"""Directory lookups and transaction status checks for the Paga Engine API.

These are the read-only operations that resolve the identifiers the write
endpoints need — bank UUIDs, operator codes, bundle ids, biller UUIDs — plus
the status checks that tell you what happened to a transaction you already
sent.

Most Paga lookups are worth caching: bank and biller lists change rarely,
and Paga asks integrators to refresh them monthly.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .auth import (
    BANKS_HASH_FIELDS,
    COLLECT_BANKS_HASH_FIELDS,
    DATA_BUNDLE_HASH_FIELDS,
    MERCHANT_ACCOUNT_DETAILS_HASH_FIELDS,
    MERCHANT_SERVICES_HASH_FIELDS,
    MERCHANTS_HASH_FIELDS,
    MOBILE_OPERATORS_HASH_FIELDS,
    RECENT_TRANSACTION_HISTORY_HASH_FIELDS,
    TRANSACTION_STATUS_HASH_FIELDS,
    USD_PAYMENT_STATUS_HASH_FIELDS,
    VALIDATE_DEPOSIT_TO_BANK_HASH_FIELDS,
)
from .models import (
    BanksResponse,
    CollectBanksResponse,
    DataBundlesResponse,
    MerchantsResponse,
    MerchantAccountDetailsResponse,
    MerchantServicesResponse,
    MobileOperatorsResponse,
    PagaResponse,
    RecentTransactionsResponse,
    RefundStatusResponse,
    TransactionStatusResponse,
    ValidateDepositToBankResponse,
)

__all__ = ["DirectoryMixin"]


class DirectoryMixin:
    """Lookup and status operations."""

    # ----------------------------------------------------------------- #
    # Banks
    # ----------------------------------------------------------------- #

    async def get_collect_banks(self, *, reference_number: str) -> CollectBanksResponse:
        """List the banks a customer can pay from.

        Operation: Bank USSD - Get the customer's bank.

        Lists the banks available for a Bank USSD payment. Send the bank's
        ``uuid`` as ``payer.bankId`` when creating a payment request, or as
        ``autoSweep.bankPublicId`` when creating a subsidiary account.

        Args:
            reference_number: Your unique reference for this request.

        Returns:
            The parsed :class:`CollectBanksResponse`.
        """
        response = await self._request(
            "POST",
            "/banks",
            {"referenceNumber": reference_number},
            use_hash=True,
            use_basic=True,
            hash_fields=COLLECT_BANKS_HASH_FIELDS,
            raise_on_error=False,
        )
        return CollectBanksResponse.model_validate(response.model_dump())

    async def get_banks(self, *, reference_number: str) -> BanksResponse:
        """List every institution you can pay.

        Operation: Money transfer - Get the bank's UUID.

        Lists every institution money can be sent to, with the ``uuid`` you
        send as ``destinationBankUUID``. UUIDs never change, but new
        institutions are added every month — cache the list and refresh it
        weekly or monthly.

        To send to a Paga wallet, use Paga's UUID
        ``AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA``.

        Args:
            reference_number: Your unique reference for this request.

        Returns:
            The parsed :class:`BanksResponse`.
        """
        response = await self._request(
            "POST",
            "/getBanks",
            {"referenceNumber": reference_number},
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=BANKS_HASH_FIELDS,
            raise_on_error=False,
        )
        return BanksResponse.model_validate(response.model_dump())

    async def validate_deposit_to_bank(
        self,
        *,
        reference_number: str,
        amount: str,
        destination_bank_uuid: str,
        destination_bank_account_number: str,
        currency: str = "NGN",
        recipient_name: Optional[str] = None,
        recipient_phone_number: Optional[str] = None,
        recipient_mobile_operator_code: Optional[str] = None,
        recipient_email: Optional[str] = None,
        locale: Optional[str] = None,
    ) -> ValidateDepositToBankResponse:
        """Validate a destination account before sending money to it.

        Operation: Money transfer - Validate the account.

        Confirms the account exists and returns the account holder's name and
        the fee, before any money moves. Send ``amount`` exactly as you will
        send it later: ``"5000.00"`` and ``"5000"`` sign differently.

        Args:
            reference_number: Your unique reference for this request.
            amount: The amount you intend to send, as a string.
            destination_bank_uuid: The bank's UUID. From :meth:`get_banks`.
            destination_bank_account_number: The destination account number.
            currency: Transaction currency. Defaults to ``"NGN"``.
            recipient_name: Optional recipient name.
            recipient_phone_number: Optional recipient phone number.
            recipient_mobile_operator_code: Optional recipient network code.
            recipient_email: Optional recipient email address.
            locale: Optional locale.

        Returns:
            The parsed :class:`ValidateDepositToBankResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "currency": currency,
            "destinationBankUUID": destination_bank_uuid,
            "destinationBankAccountNumber": destination_bank_account_number,
        }
        if recipient_name is not None:
            payload["recipientName"] = recipient_name
        if recipient_phone_number is not None:
            payload["recipientPhoneNumber"] = recipient_phone_number
        if recipient_mobile_operator_code is not None:
            payload["recipientMobileOperatorCode"] = recipient_mobile_operator_code
        if recipient_email is not None:
            payload["recipientEmail"] = recipient_email
        if locale is not None:
            payload["locale"] = locale

        response = await self._request(
            "POST",
            "/validateDepositToBank",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=VALIDATE_DEPOSIT_TO_BANK_HASH_FIELDS,
            raise_on_error=False,
        )
        return ValidateDepositToBankResponse.model_validate(response.model_dump())

    # ----------------------------------------------------------------- #
    # Airtime and data
    # ----------------------------------------------------------------- #

    async def get_mobile_operators(
        self,
        *,
        reference_number: str,
        locale: Optional[str] = None,
    ) -> MobileOperatorsResponse:
        """List the mobile networks you can top up.

        Operation: Airtime and data - Get the mobile operator.

        Send a network's ``mobileOperatorCode`` as ``mobileOperatorPublicId``
        when buying airtime, and as ``operatorPublicId`` when listing data
        bundles. Cache the list.

        Args:
            reference_number: Your unique reference for this request.
            locale: Optional locale. Paga defaults to the empty string.

        Returns:
            The parsed :class:`MobileOperatorsResponse`.
        """
        payload: Dict[str, Any] = {"referenceNumber": reference_number}
        if locale is not None:
            payload["locale"] = locale

        response = await self._request(
            "POST",
            "/getMobileOperators",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=MOBILE_OPERATORS_HASH_FIELDS,
            raise_on_error=False,
        )
        return MobileOperatorsResponse.model_validate(response.model_dump())

    async def get_data_bundles(
        self,
        *,
        reference_number: str,
        operator_public_id: str,
    ) -> DataBundlesResponse:
        """List a network's data bundles.

        Operation: Airtime and data - For data, pick a bundle.

        Send a bundle's ``serviceId`` as ``mobileOperatorServiceId`` and
        **exactly** its ``servicePrice`` as ``amount`` — the two must match
        byte for byte or Paga rejects the purchase. Bundles rarely change, so
        cache the list and refresh it monthly.

        Args:
            reference_number: Your unique reference for this request.
            operator_public_id: The operator's ``mobileOperatorCode``.

        Returns:
            The parsed :class:`DataBundlesResponse`.
        """
        response = await self._request(
            "POST",
            "/getDataBundleByOperator",
            {
                "referenceNumber": reference_number,
                "operatorPublicId": operator_public_id,
            },
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=DATA_BUNDLE_HASH_FIELDS,
            raise_on_error=False,
        )
        return DataBundlesResponse.model_validate(response.model_dump())

    # ----------------------------------------------------------------- #
    # Bill payment
    # ----------------------------------------------------------------- #

    async def get_merchants(self, *, reference_number: str) -> MerchantsResponse:
        """List every biller you can pay.

        Operation: Bill payment - Find the biller.

        Lists every biller, with the ``uuid`` you send as ``merchantAccount``.
        Cache the list.

        Args:
            reference_number: Your unique reference for this request.

        Returns:
            The parsed :class:`MerchantsResponse`.
        """
        response = await self._request(
            "POST",
            "/getMerchants",
            {"referenceNumber": reference_number},
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=MERCHANTS_HASH_FIELDS,
            raise_on_error=False,
        )
        return MerchantsResponse.model_validate(response.model_dump())

    async def get_merchant_services(
        self,
        *,
        reference_number: str,
        merchant_public_id: str,
    ) -> MerchantServicesResponse:
        """List what a biller can be paid for.

        Operation: Bill payment - Pick the service.

        No services means any amount is allowed. A service with ``price``
        ``0.0`` means the customer chooses the amount. Otherwise pay the
        service's ``price``.

        Args:
            reference_number: Your unique reference for this request.
            merchant_public_id: The biller's ``uuid``.

        Returns:
            The parsed :class:`MerchantServicesResponse`.
        """
        response = await self._request(
            "POST",
            "/getMerchantServices",
            {
                "referenceNumber": reference_number,
                "merchantPublicId": merchant_public_id,
            },
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=MERCHANT_SERVICES_HASH_FIELDS,
            raise_on_error=False,
        )
        return MerchantServicesResponse.model_validate(response.model_dump())

    async def get_merchant_account_details(
        self,
        *,
        reference_number: str,
        merchant_account: str,
        merchant_reference_number: str,
        merchant_service_product_code: Optional[str] = None,
    ) -> MerchantAccountDetailsResponse:
        """Validate a customer's meter, smart card or account number.

        Operation: Bill payment - Validate the customer.

        Checks the customer's number and returns their name. If the customer
        chose a service, always send its ``code`` as
        ``merchant_service_product_code``. Billers that don't need it still
        take part in the hash — send ``""`` when there is no service.

        Args:
            reference_number: Your unique reference for this request.
            merchant_account: The biller's ``uuid``.
            merchant_reference_number: The customer's account / meter /
                smart card number at the biller.
            merchant_service_product_code: The chosen service's ``code``.
                Optional, but it participates in the hash either way.

        Returns:
            The parsed :class:`MerchantAccountDetailsResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "merchantAccount": merchant_account,
            "merchantReferenceNumber": merchant_reference_number,
        }
        # Always sent: the field is part of the hash even when unused.
        payload["merchantServiceProductCode"] = merchant_service_product_code or ""

        response = await self._request(
            "POST",
            "/getMerchantAccountDetails",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=MERCHANT_ACCOUNT_DETAILS_HASH_FIELDS,
            raise_on_error=False,
        )
        return MerchantAccountDetailsResponse.model_validate(response.model_dump())

    # ----------------------------------------------------------------- #
    # Status
    # ----------------------------------------------------------------- #

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

    async def get_recent_transactions(
        self,
        *,
        reference_number: str,
        locale: Optional[str] = None,
        account_principal: Optional[str] = None,
        account_credentials: Optional[str] = None,
    ) -> RecentTransactionsResponse:
        """Get the last five transactions on the business account.

        Operation: Your business account - Get your recent transactions.

        Newest first, no date range. For anything further back, use
        :meth:`get_business_transactions`.

        Args:
            reference_number: Your unique reference for this request.
            locale: Optional locale. Paga defaults to ``"en"``.
            account_principal: Principal to check instead of your own.
                Only for looking at a Paga user's account.
            account_credentials: Credentials for that principal.

        Returns:
            The parsed :class:`RecentTransactionsResponse`.
        """
        payload: Dict[str, Any] = {"referenceNumber": reference_number}
        if locale is not None:
            payload["locale"] = locale
        if account_principal is not None:
            payload["accountPrincipal"] = account_principal
        if account_credentials is not None:
            payload["accountCredentials"] = account_credentials

        response = await self._request(
            "POST",
            "/recentTransactionHistory",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=RECENT_TRANSACTION_HISTORY_HASH_FIELDS,
            raise_on_error=False,
        )
        return RecentTransactionsResponse.model_validate(response.model_dump())

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
            hash_fields=("referenceNumber",),
            raise_on_error=False,
        )
        return RefundStatusResponse.model_validate(response.model_dump())

    async def get_usd_payment_status(
        self,
        *,
        reference_number: str,
        payment_currency: str = "USD",
    ) -> PagaResponse:
        """Check the status of a USD (ACH, Wire, Swift) payment request.

        Operation: Bank transfer (ACH, Wire and Swift) - Check payment status.

        Unlike the other ``/status`` operations, this one signs the currency
        as well as the reference number.

        The outer ``statusCode`` says whether the status request worked; the
        payment's own status is in ``data.statusCode``, where ``"1"`` means
        still pending.

        Args:
            reference_number: The ``referenceNumber`` of the payment request.
            payment_currency: The payment currency. Defaults to ``"USD"``.

        Returns:
            The parsed :class:`PagaResponse`.
        """
        response = await self._request(
            "POST",
            "/status",
            {
                "referenceNumber": reference_number,
                "paymentCurrency": payment_currency,
            },
            use_hash=True,
            use_basic=True,
            hash_fields=USD_PAYMENT_STATUS_HASH_FIELDS,
            raise_on_error=False,
        )
        return response
