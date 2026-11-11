"""Money transfer operations for the Paga Engine API.

Covers the **Make payments → Money Transfer** section of Paga's documentation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .auth import (
    BANKS_HASH_FIELDS,
    MONEY_TRANSFER_BULK_HASH_FIELDS,
    MONEY_TRANSFER_HASH_FIELDS,
    PAGA_WALLET_TRANSFER_HASH_FIELDS,
    TRANSACTION_STATUS_HASH_FIELDS,
    VALIDATE_DEPOSIT_TO_BANK_HASH_FIELDS,
    VALIDATE_MONEY_TRANSFER_HASH_FIELDS,
)
from .models import (
    BanksResponse,
    BulkMoneyTransferResponse,
    DepositToBankResponse,
    MoneyTransferResponse,
    TransactionStatusResponse,
    ValidateDepositToBankResponse,
    ValidateMoneyTransferResponse,
)

__all__ = ["MoneyTransferMixin"]


class MoneyTransferMixin:
    """Money transfer operations."""

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
        recipient_name: Optional[str] = None,
        recipient_phone_number: Optional[str] = None,
        recipient_mobile_operator_code: Optional[str] = None,
        recipient_email: Optional[str] = None,
        transfer_reference: Optional[str] = None,
        suppress_recipient_message: bool = False,
        alternate_sender_name: Optional[str] = None,
    ) -> DepositToBankResponse:
        """Send money from the business balance to a bank account or Paga wallet.

        Operation: Money transfer - Send the money.

        Sends money from the business balance to a bank account, or to a Paga
        wallet (using Paga's UUID ``AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA``).

        Send ``amount`` as a string (e.g. ``"5000.00"``): it is signed
        verbatim, so ``"5000.00"`` and ``"5000"`` are different.

        Args:
            reference_number: Your unique transfer reference.
            amount: Amount to send, as a string.
            destination_bank_uuid: The bank's UUID from :meth:`get_banks`, or
                Paga's UUID for a wallet.
            destination_bank_account_number: Destination bank account number.
            currency: Transaction currency. Defaults to ``"NGN"``.
            remarks: Optional transfer remarks.
            status_callback_url: Where Paga notifies once the transfer is processed. Optional.
            recipient_name: Optional recipient name.
            recipient_phone_number: Optional recipient phone number.
            recipient_mobile_operator_code: Optional recipient network code.
            recipient_email: Optional recipient email address.
            transfer_reference: Optional alternative reconciliation reference.
            suppress_recipient_message: Whether to suppress the recipient's
                message. Defaults to ``False``.
            alternate_sender_name: Optional alternate sender name, at most 16
                characters.

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
        if recipient_name is not None:
            payload["recipientName"] = recipient_name
        if recipient_phone_number is not None:
            payload["recipientPhoneNumber"] = recipient_phone_number
        if recipient_mobile_operator_code is not None:
            payload["recipientMobileOperatorCode"] = recipient_mobile_operator_code
        if recipient_email is not None:
            payload["recipientEmail"] = recipient_email
        if transfer_reference is not None:
            payload["transferReference"] = transfer_reference
        if suppress_recipient_message:
            payload["suppressRecipientMessage"] = True
        if alternate_sender_name is not None:
            payload["alternateSenderName"] = alternate_sender_name

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
        their phone number, nickname or account number.

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
                characters.
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
