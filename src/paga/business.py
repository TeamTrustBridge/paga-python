"""Business account operations for the Paga Engine API.

Covers the **Manage accounts → Your business account** section of Paga's
documentation, plus the Business API operations that act on the account
itself.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .auth import (
    ACCOUNT_BALANCE_HASH_FIELDS,
    DISPENSE_CASH_HASH_FIELDS,
    GET_OPERATION_STATUS_HASH_FIELDS,
    ONBOARD_MERCHANT_HASH_FIELDS,
    RECENT_TRANSACTION_HISTORY_HASH_FIELDS,
    TRANSACTION_HISTORY_HASH_FIELDS,
)
from .models import (
    AccountBalanceResponse,
    DispenseCashResponse,
    OnboardMerchantResponse,
    OperationStatusResponse,
    RecentTransactionsResponse,
    TransactionHistoryResponse,
)

__all__ = ["BusinessMixin"]


class BusinessMixin:
    """Business account operations."""

    async def get_business_balance(self, *, reference_number: str) -> AccountBalanceResponse:
        """Check the business account balance.

        Operation: Your business account - Check your balance.

        Returns the business account balance. Check ``availableBalance``, not
        ``totalBalance``, before a payout run: it is what you can actually send.

        Args:
            reference_number: Your unique balance check reference.

        Returns:
            The parsed :class:`AccountBalanceResponse`.
        """
        response = await self._request(
            "POST",
            "/accountBalance",
            {"referenceNumber": reference_number},
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=ACCOUNT_BALANCE_HASH_FIELDS,
            raise_on_error=False,
        )
        return AccountBalanceResponse.model_validate(response.model_dump())

    async def get_business_transactions(
        self,
        *,
        reference_number: str,
        start_date_utc: str,
        end_date_utc: str,
        locale: Optional[str] = None,
    ) -> TransactionHistoryResponse:
        """Get the business transaction history.

        Operation: Your business account - Get your transaction history.

        Returns every transaction on the business account between two dates:
        money in, money out and fees, up to 10,000 at a time.

        Args:
            reference_number: Your unique history reference.
            start_date_utc: Start of the range, in UTC.
            end_date_utc: End of the range, in UTC.
            locale: Optional IETF language tag.

        Returns:
            The parsed :class:`TransactionHistoryResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "startDateUTC": start_date_utc,
            "endDateUTC": end_date_utc,
        }
        if locale is not None:
            payload["locale"] = locale
        response = await self._request(
            "POST",
            "/transactionHistory",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=TRANSACTION_HISTORY_HASH_FIELDS,
        )
        return TransactionHistoryResponse.model_validate(response.model_dump())

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

    async def get_operation_status(
        self,
        *,
        reference_number: str,
        locale: Optional[str] = None,
    ) -> OperationStatusResponse:
        """Check an operation's status.

        Operation: Business API - Get an operation status.

        Args:
            reference_number: The reference number the operation was sent
                with.
            locale: Optional IETF language tag.

        Returns:
            The parsed :class:`OperationStatusResponse`. The status is in
            ``transactionStatus``, not ``status``.
        """
        payload: Dict[str, Any] = {"referenceNumber": reference_number}
        if locale is not None:
            payload["locale"] = locale

        response = await self._request(
            "POST",
            "/getOperationStatus",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=GET_OPERATION_STATUS_HASH_FIELDS,
            raise_on_error=False,
        )
        return OperationStatusResponse.model_validate(response.model_dump())

    async def onboard_merchant(
        self,
        *,
        reference: str,
        merchant_external_id: str,
        legal_entity: Dict[str, Any],
        legal_entity_representative: Dict[str, Any],
        integration: Dict[str, Any],
        additional_parameters: Optional[Dict[str, Any]] = None,
    ) -> OnboardMerchantResponse:
        """Onboard a merchant.

        Operation: Business API - Onboard a merchant.

        For aggregators only.

        Paga signs the request over the reference, the merchant's external
        id, the legal entity's ``name`` and the representative's ``phone``
        and ``email`` — the SDK assembles that from the arguments.

        Args:
            reference: Your unique reference. Paga names this field
                ``reference``, not ``referenceNumber``.
            merchant_external_id: Your own identifier for the merchant.
            legal_entity: The legal entity. Needs at least ``name``.
            legal_entity_representative: The representative. Needs
                ``firstName``, ``lastName``, ``phone``, ``email`` and
                ``dateOfBirth``.
            integration: How Paga notifies the merchant. Either
                ``{"type": "EMAIL_NOTIFICATION", "financeAdminEmail": ...}``
                or ``{"type": "MERCHANT_NOTIFICATION_REVERSE_API",
                "callbackUrl": ..., "username": ..., "password": ...}``.
            additional_parameters: Optional extra merchant parameters. Needs
                at least ``displayName`` and ``establishedDate``.

        Returns:
            The parsed :class:`OnboardMerchantResponse`.
        """
        merchant_info: Dict[str, Any] = {
            "legalEntity": legal_entity,
            "legalEntityRepresentative": legal_entity_representative,
            "additionalParameters": additional_parameters or {},
        }
        payload: Dict[str, Any] = {
            "reference": reference,
            "merchantExternalId": merchant_external_id,
            "merchantInfo": merchant_info,
            "integration": integration,
        }

        hash_payload = {
            "referenceNumber": reference,
            "merchantExternalId": merchant_external_id,
            "name": legal_entity.get("name"),
            "phone": legal_entity_representative.get("phone"),
            "email": legal_entity_representative.get("email"),
        }
        response = await self._request(
            "POST",
            "/onboardMerchant",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=ONBOARD_MERCHANT_HASH_FIELDS,
            hash_payload=hash_payload,
            raise_on_error=False,
        )
        return OnboardMerchantResponse.model_validate(response.model_dump())

    async def dispense_cash(
        self,
        *,
        reference_number: str,
        customer_phone_number: str,
        amount: float,
        withdrawal_code: str,
        locale: Optional[str] = None,
    ) -> DispenseCashResponse:
        """Dispense cash against a customer's withdrawal code.

        Operation: Business API - Dispense cash.

        Args:
            reference_number: Your unique reference for this request.
            customer_phone_number: The customer's phone number.
            amount: The amount to dispense.
            withdrawal_code: The customer's withdrawal code.
            locale: Optional IETF language tag.

        Returns:
            The parsed :class:`DispenseCashResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "customerPhoneNumber": customer_phone_number,
            "amount": amount,
            "withdrawalCode": withdrawal_code,
        }
        if locale is not None:
            payload["locale"] = locale

        response = await self._request(
            "POST",
            "/dispenseCash",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=DISPENSE_CASH_HASH_FIELDS,
            raise_on_error=False,
        )
        return DispenseCashResponse.model_validate(response.model_dump())
