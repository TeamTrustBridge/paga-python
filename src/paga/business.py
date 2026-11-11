"""Business and subsidiary account operations for the Paga Engine API."""

from __future__ import annotations

from typing import Any, Dict, Optional

from .auth import (
    ACCOUNT_BALANCE_HASH_FIELDS,
    DISPENSE_CASH_HASH_FIELDS,
    GET_OPERATION_STATUS_HASH_FIELDS,
    MONEY_TRANSFER_BULK_HASH_FIELDS,
    ONBOARD_MERCHANT_HASH_FIELDS,
    PAGA_WALLET_TRANSFER_HASH_FIELDS,
    SUBSIDIARY_ACCOUNT_HASH_FIELDS,
    SUBSIDIARY_BALANCE_HASH_FIELDS,
    SUBSIDIARY_CHARGE_HASH_FIELDS,
    SUBSIDIARY_HISTORY_HASH_FIELDS,
    SUBSIDIARY_RETRIEVE_HASH_FIELDS,
    SUBSIDIARY_TOPUP_HASH_FIELDS,
    SUBSIDIARY_TRANSFER_HASH_FIELDS,
    SUBSIDIARY_UPDATE_HASH_FIELDS,
    TRANSACTION_HISTORY_HASH_FIELDS,
    VALIDATE_MONEY_TRANSFER_HASH_FIELDS,
)
from .models import (
    AccountBalanceResponse,
    BulkMoneyTransferResponse,
    DispenseCashResponse,
    MoneyTransferResponse,
    OnboardMerchantResponse,
    OperationStatusResponse,
    PagaResponse,
    SubsidiaryAccountResponse,
    SubsidiaryBalanceResponse,
    SubsidiaryHistoryResponse,
    SubsidiaryMoneyResponse,
    SubsidiaryTransferResponse,
    TransactionHistoryResponse,
    ValidateMoneyTransferResponse,
)


class BusinessMixin:
    """Business account operations and subsidiary account management."""

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
            use_basic=False,
            base_url=self.business_base_url,
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

    # ----------------------------------------------------------------- #
    # Transfers to Paga wallets
    # ----------------------------------------------------------------- #

    async def transfer_to_paga_wallet(
        self,
        *,
        reference_number: str,
        amount: float,
        destination_account: str,
        currency: str = "NGN",
        destination_bank: Optional[str] = None,
        send_withdrawal_code: bool = True,
        source_of_funds: Optional[str] = None,
        transfer_reference: Optional[str] = None,
        suppress_recipient_message: bool = False,
        alternate_sender_name: Optional[str] = None,
        locale: Optional[str] = None,
    ) -> MoneyTransferResponse:
        """Send money to a Paga wallet.

        Operation: Business API - Money transfer to a Paga wallet.

        Sends money from the business balance to a Paga user, identified by
        their phone number, nickname or account number. This is the
        Paga-wallet sibling of :meth:`send_money`, which sends to a bank
        account.

        Args:
            reference_number: Your unique transfer reference. At most 50
                characters.
            amount: The amount to send.
            destination_account: The recipient's phone number, nickname or
                account number.
            currency: Transaction currency. Defaults to ``"NGN"``.
            destination_bank: Bank code, when transferring to a bank account.
            send_withdrawal_code: Whether to issue the recipient a withdrawal
                code. Defaults to ``True``.
            source_of_funds: Defaults to the sender's own Paga account.
            transfer_reference: An alternative reconciliation reference.
            suppress_recipient_message: Whether to suppress the recipient's
                message. Defaults to ``False``.
            alternate_sender_name: An alternate sender name, at most 16
                characters. Only when the sender principal is absent.
            locale: Optional IETF language tag.

        Returns:
            The parsed :class:`MoneyTransferResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "currency": currency,
            "destinationAccount": destination_account,
            "sendWithdrawalCode": send_withdrawal_code,
            "suppressRecipientMessage": suppress_recipient_message,
        }
        if destination_bank is not None:
            payload["destinationBank"] = destination_bank
        if source_of_funds is not None:
            payload["sourceOfFunds"] = source_of_funds
        if transfer_reference is not None:
            payload["transferReference"] = transfer_reference
        if alternate_sender_name is not None:
            payload["alternateSenderName"] = alternate_sender_name
        if locale is not None:
            payload["locale"] = locale

        response = await self._request(
            "POST",
            "/moneyTransfer",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=PAGA_WALLET_TRANSFER_HASH_FIELDS,
            raise_on_error=False,
        )
        return MoneyTransferResponse.model_validate(response.model_dump())

    async def validate_money_transfer(
        self,
        *,
        reference_number: str,
        amount: float,
        destination_account: str,
        currency: str = "NGN",
    ) -> ValidateMoneyTransferResponse:
        """Validate a Paga wallet transfer before sending it.

        Operation: Business API - Validate a money transfer.

        Confirms the recipient exists and returns their name, registration
        status, KYC level and the fee, before any money moves.

        Args:
            reference_number: Your unique reference for this request.
            amount: The amount you intend to send.
            destination_account: The recipient's phone number, nickname or
                account number.
            currency: Transaction currency. Defaults to ``"NGN"``.

        Returns:
            The parsed :class:`ValidateMoneyTransferResponse`.
        """
        response = await self._request(
            "POST",
            "/validateMoneyTransfer",
            {
                "referenceNumber": reference_number,
                "amount": amount,
                "currency": currency,
                "destinationAccount": destination_account,
            },
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=VALIDATE_MONEY_TRANSFER_HASH_FIELDS,
            raise_on_error=False,
        )
        return ValidateMoneyTransferResponse.model_validate(response.model_dump())

    async def send_bulk_money_transfer(
        self,
        *,
        items: List[Dict[str, Any]],
        bulk_reference_number: Optional[str] = None,
    ) -> BulkMoneyTransferResponse:
        """Send up to 300 money transfers in one call.

        Operation: Business API - Bulk money transfer.

        Each item needs a ``referenceNumber``, an ``amount`` and a
        ``destinationAccount``; ``currency``, ``destinationBank``,
        ``transferReference`` and ``suppressRecipientMessage`` are optional.
        Sending more than 300 items is rejected with response code ``-3``.

        Paga hashes the **first item's** reference number, amount and
        destination account, followed by the total number of items — the SDK
        does that for you.

        Args:
            items: The transfers to send.
            bulk_reference_number: Your reference for the batch as a whole.

        Returns:
            The parsed :class:`BulkMoneyTransferResponse`. Check every entry
            in ``results`` — a bulk transfer can partially succeed.
        """
        if not items:
            raise ValueError("items must not be empty")
        if len(items) > 300:
            raise ValueError("a bulk money transfer may contain at most 300 items")

        payload: Dict[str, Any] = {"items": [dict(item) for item in items]}
        if bulk_reference_number is not None:
            payload["bulkReferenceNumber"] = bulk_reference_number

        first = items[0]
        hash_payload = {
            "referenceNumber": first.get("referenceNumber"),
            "amount": first.get("amount"),
            "destinationAccount": first.get("destinationAccount"),
            "itemCount": len(items),
        }
        response = await self._request(
            "POST",
            "/moneyTransferBulk",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=MONEY_TRANSFER_BULK_HASH_FIELDS,
            hash_payload=hash_payload,
            raise_on_error=False,
        )
        return BulkMoneyTransferResponse.model_validate(response.model_dump())

    # ----------------------------------------------------------------- #
    # Operations, merchants and cash
    # ----------------------------------------------------------------- #

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
