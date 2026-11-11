"""Subsidiary account operations for the Paga Engine API.

Covers the **Manage accounts → Subsidiary accounts** section of Paga's
documentation.

A subsidiary account is a Paga account for one of your customers, held on
your behalf. You can issue, hold and move money on their account, and set it
up to sweep straight into a bank account.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .auth import (
    SUBSIDIARY_ACCOUNT_HASH_FIELDS,
    SUBSIDIARY_BALANCE_HASH_FIELDS,
    SUBSIDIARY_CHARGE_HASH_FIELDS,
    SUBSIDIARY_HISTORY_HASH_FIELDS,
    SUBSIDIARY_RETRIEVE_HASH_FIELDS,
    SUBSIDIARY_TOPUP_HASH_FIELDS,
    SUBSIDIARY_TRANSFER_HASH_FIELDS,
    SUBSIDIARY_UPDATE_HASH_FIELDS,
)
from .models import (
    SubsidiaryAccountResponse,
    SubsidiaryBalanceResponse,
    SubsidiaryHistoryResponse,
    SubsidiaryMoneyResponse,
    SubsidiaryTransferResponse,
)

__all__ = ["SubsidiaryMixin"]


class SubsidiaryMixin:
    """Subsidiary account operations."""

    async def create_subsidiary_account(
        self,
        *,
        reference_number: str,
        account_reference: str,
        account_name: str,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        iifi_number: Optional[str] = None,
        funding_transaction_limit: Optional[float] = None,
        funding_daily_limit: Optional[float] = None,
        status: Optional[str] = None,
        auto_sweep_destination: Optional[str] = None,
        auto_sweep_bank_public_id: Optional[str] = None,
        auto_sweep_account_number: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> SubsidiaryAccountResponse:
        """Create a subsidiary account.

        Operation: Subsidiary Accounts - Create an account.

        Creates a subsidiary account. Leave out ``auto_sweep_destination`` for a
        ledger-backed account that holds funds; set it to ``"VIRTUAL_ACCOUNT"`` or
        ``"BANK"`` for a virtual account that settles straight away.

        Reusing a ``reference_number`` or ``account_reference`` returns status
        code ``102`` (duplicate) and never creates a second account.

        Args:
            reference_number: Your unique reference for this request.
            account_reference: Your permanent ID for the account (e.g.
                ``CUST-000184-WALLET``).
            account_name: Account holder name.
            first_name: Optional first name of the account holder.
            last_name: Optional last name of the account holder.
            phone_number: Optional phone number of the account holder.
            email: Optional email address of the account holder.
            iifi_number: BVN or NIN of the account holder. Hash value 3.
            funding_transaction_limit: Optional funding transaction limit.
            funding_daily_limit: Optional funding daily limit.
            status: Optional account status, e.g. ``"ACTIVE"`` or ``"DISABLED"``.
            auto_sweep_destination: Optional ``"VIRTUAL_ACCOUNT"`` or ``"BANK"``.
            auto_sweep_bank_public_id: Bank public ID, only when the destination
                is ``"BANK"``.
            auto_sweep_account_number: Bank account number, only when the
                destination is ``"BANK"``.
            callback_url: Where Paga sends callbacks. Optional.

        Returns:
            The parsed :class:`SubsidiaryAccountResponse`.

        ``status_code`` of ``"102"`` means a duplicate reference was used.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "accountReference": account_reference,
            "accountName": account_name,
        }
        if first_name is not None:
            payload["firstName"] = first_name
        if last_name is not None:
            payload["lastName"] = last_name
        if phone_number is not None:
            payload["phoneNumber"] = phone_number
        if email is not None:
            payload["email"] = email
        if iifi_number is not None:
            payload["iifiNumber"] = iifi_number
        if funding_transaction_limit is not None:
            payload["fundingTransactionLimit"] = funding_transaction_limit
        if funding_daily_limit is not None:
            payload["fundingDailyLimit"] = funding_daily_limit
        if status is not None:
            payload["status"] = status
        if auto_sweep_destination is not None:
            auto_sweep: Dict[str, Any] = {"destination": auto_sweep_destination}
            if auto_sweep_destination == "BANK":
                if auto_sweep_bank_public_id is not None:
                    auto_sweep["bankPublicId"] = auto_sweep_bank_public_id
                if auto_sweep_account_number is not None:
                    auto_sweep["accountNumber"] = auto_sweep_account_number
            payload["autoSweep"] = auto_sweep
        if callback_url is not None:
            payload["callbackUrl"] = callback_url

        response = await self._request(
            "POST",
            "/subsidiary-accounts",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=SUBSIDIARY_ACCOUNT_HASH_FIELDS,
        )
        return SubsidiaryAccountResponse.model_validate(response.model_dump())

    async def charge_subsidiary_account(
        self,
        *,
        account_reference: str,
        reference_number: str,
        amount: float,
        currency: str = "NGN",
        narration: Optional[str] = None,
    ) -> SubsidiaryMoneyResponse:
        """Charge a ledger-backed subsidiary account.

        Operation: Subsidiary Accounts - Charge an account.

        Debits a ledger-backed account. Not available on virtual accounts. Retrying
        with the same ``reference_number`` never moves money twice.

        Args:
            account_reference: The account's ``accountReference`` (the
                ``accountIdentifier``).
            reference_number: Your unique charge reference.
            amount: Amount to debit.
            currency: Transaction currency. Defaults to ``"NGN"``.
            narration: Optional narration for the charge.

        Returns:
            The parsed :class:`SubsidiaryMoneyResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "currency": currency,
        }
        if narration is not None:
            payload["narration"] = narration
        response = await self._request(
            "POST",
            f"/subsidiary-accounts/{account_reference}/charge",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=SUBSIDIARY_CHARGE_HASH_FIELDS,
        )
        return SubsidiaryMoneyResponse.model_validate(response.model_dump())

    async def top_up_subsidiary_account(
        self,
        *,
        account_reference: str,
        reference_number: str,
        amount: float,
        currency: str = "NGN",
        narration: Optional[str] = None,
    ) -> SubsidiaryMoneyResponse:
        """Top up a ledger-backed subsidiary account.

        Operation: Subsidiary Accounts - Top up an account.

        Credits a ledger-backed account from your business balance. Not available
        on virtual accounts.

        Args:
            account_reference: The account's ``accountReference`` (the
                ``accountIdentifier``).
            reference_number: Your unique top-up reference.
            amount: Amount to credit.
            currency: Transaction currency. Defaults to ``"NGN"``.
            narration: Optional narration for the top-up.

        Returns:
            The parsed :class:`SubsidiaryMoneyResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "currency": currency,
        }
        if narration is not None:
            payload["narration"] = narration
        response = await self._request(
            "POST",
            f"/subsidiary-accounts/{account_reference}/topup",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=SUBSIDIARY_TOPUP_HASH_FIELDS,
        )
        return SubsidiaryMoneyResponse.model_validate(response.model_dump())

    async def transfer_between_subsidiary_accounts(
        self,
        *,
        source_account_reference: str,
        destination_account_reference: str,
        reference_number: str,
        amount: float,
        currency: str = "NGN",
        narration: Optional[str] = None,
    ) -> SubsidiaryTransferResponse:
        """Transfer money between two subsidiary accounts.

        Operation: Subsidiary Accounts - Transfer between accounts.

        Moves money between two ledger-backed accounts. Paga sends one callback,
        for the source account only.

        Args:
            source_account_reference: The source account's ``accountReference``.
            destination_account_reference: The destination account's
                ``accountReference``.
            reference_number: Your unique transfer reference.
            amount: Amount to move.
            currency: Transaction currency. Defaults to ``"NGN"``.
            narration: Optional narration for the transfer.

        Returns:
            The parsed :class:`SubsidiaryTransferResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "sourceAccountIdentifier": source_account_reference,
            "destinationAccountIdentifier": destination_account_reference,
            "amount": amount,
            "currency": currency,
        }
        if narration is not None:
            payload["narration"] = narration
        response = await self._request(
            "POST",
            "/subsidiary-accounts/transfer",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=SUBSIDIARY_TRANSFER_HASH_FIELDS,
        )
        return SubsidiaryTransferResponse.model_validate(response.model_dump())

    async def retrieve_subsidiary_account(
        self,
        *,
        account_reference: str,
        reference_number: str,
    ) -> SubsidiaryAccountResponse:
        """Retrieve a subsidiary account.

        Operation: Subsidiary Accounts - Retrieve an account.

        Returns an account's details, limits, callback URL and balance.

        Args:
            account_reference: The account's ``accountReference`` (the
                ``accountIdentifier``).
            reference_number: Your unique retrieve reference.

        Returns:
            The parsed :class:`SubsidiaryAccountResponse`.
        """
        response = await self._request(
            "GET",
            f"/subsidiary-accounts/{account_reference}",
            {"referenceNumber": reference_number, "accountIdentifier": account_reference},
            use_hash=True,
            use_basic=True,
            base_url=self.base_url,
            hash_fields=SUBSIDIARY_RETRIEVE_HASH_FIELDS,
            params={"referenceNumber": reference_number},
        )
        return SubsidiaryAccountResponse.model_validate(response.model_dump())

    async def update_subsidiary_account(
        self,
        *,
        account_reference: str,
        reference_number: str,
        account_name: Optional[str] = None,
        iifi_number: Optional[str] = None,
        status: Optional[str] = None,
        auto_sweep_destination: Optional[str] = None,
        auto_sweep_bank_public_id: Optional[str] = None,
        auto_sweep_account_number: Optional[str] = None,
        callback_url: Optional[str] = None,
    ) -> SubsidiaryAccountResponse:
        """Update a subsidiary account.

        Operation: Subsidiary Accounts - Update an account.

        Changes an account. Send only what you want to change. ``accountNumber``
        and ``accountReference`` can't be changed.

        Args:
            account_reference: The account's ``accountReference`` (the
                ``accountIdentifier``).
            reference_number: Your unique update reference.
            account_name: Optional new account holder name.
            iifi_number: Optional new BVN / NIN.
            status: Optional new account status, e.g. ``"ACTIVE"`` or ``"DISABLED"``.
            auto_sweep_destination: Optional ``"VIRTUAL_ACCOUNT"`` or ``"BANK"``.
            auto_sweep_bank_public_id: Bank public ID, only when the destination
                is ``"BANK"``.
            auto_sweep_account_number: Bank account number, only when the
                destination is ``"BANK"``.
            callback_url: Optional new callback URL.

        Returns:
            The parsed :class:`SubsidiaryAccountResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "accountIdentifier": account_reference,
        }
        if account_name is not None:
            payload["accountName"] = account_name
        if iifi_number is not None:
            payload["iifiNumber"] = iifi_number
        if status is not None:
            payload["status"] = status
        if auto_sweep_destination is not None:
            auto_sweep: Dict[str, Any] = {"destination": auto_sweep_destination}
            if auto_sweep_destination == "BANK":
                if auto_sweep_bank_public_id is not None:
                    auto_sweep["bankPublicId"] = auto_sweep_bank_public_id
                if auto_sweep_account_number is not None:
                    auto_sweep["accountNumber"] = auto_sweep_account_number
            payload["autoSweep"] = auto_sweep
        if callback_url is not None:
            payload["callbackUrl"] = callback_url
        response = await self._request(
            "PUT",
            f"/subsidiary-accounts/{account_reference}",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=SUBSIDIARY_UPDATE_HASH_FIELDS,
        )
        return SubsidiaryAccountResponse.model_validate(response.model_dump())

    async def get_subsidiary_balance(
        self,
        *,
        account_reference: str,
        reference_number: str,
    ) -> SubsidiaryBalanceResponse:
        """Get a subsidiary account balance.

        Operation: Subsidiary Accounts - Get the balance.

        Returns an account's balance.

        Args:
            account_reference: The account's ``accountReference`` (the
                ``accountIdentifier``).
            reference_number: Your unique balance check reference.

        Returns:
            The parsed :class:`SubsidiaryBalanceResponse`.
        """
        response = await self._request(
            "GET",
            f"/subsidiary-accounts/{account_reference}/balance",
            {"referenceNumber": reference_number, "accountIdentifier": account_reference},
            use_hash=True,
            use_basic=True,
            base_url=self.base_url,
            hash_fields=SUBSIDIARY_BALANCE_HASH_FIELDS,
            params={"referenceNumber": reference_number},
        )
        return SubsidiaryBalanceResponse.model_validate(response.model_dump())

    async def get_subsidiary_history(
        self,
        *,
        account_reference: str,
        reference_number: str,
        start_date_time_utc: str,
        end_date_time_utc: str,
        page_number: int = 0,
        page_size: int = 20,
    ) -> SubsidiaryHistoryResponse:
        """Get a subsidiary account transaction history.

        Operation: Subsidiary Accounts - Get transaction history.

        Returns an account's transactions, up to 3 months at a time. Pages start
        at ``0``. ``reference_number`` is required, but isn't part of this hash.

        Args:
            account_reference: The account's ``accountReference`` (the
                ``accountIdentifier``).
            reference_number: Your unique history reference (query only).
            start_date_time_utc: Start of the range, in UTC.
            end_date_time_utc: End of the range, in UTC.
            page_number: Page number to fetch. Defaults to ``0``.
            page_size: Page size. Defaults to ``20``.

        Returns:
            The parsed :class:`SubsidiaryHistoryResponse`.
        """
        response = await self._request(
            "GET",
            f"/subsidiary-accounts/{account_reference}/history",
            {
                "accountIdentifier": account_reference,
                "startDateTimeUTC": start_date_time_utc,
                "endDateTimeUTC": end_date_time_utc,
            },
            use_hash=True,
            use_basic=True,
            base_url=self.base_url,
            hash_fields=SUBSIDIARY_HISTORY_HASH_FIELDS,
            params={
                "referenceNumber": reference_number,
                "startDateTimeUTC": start_date_time_utc,
                "endDateTimeUTC": end_date_time_utc,
                "pageSize": page_size,
                "pageNumber": page_number,
            },
        )
        return SubsidiaryHistoryResponse.model_validate(response.model_dump())
