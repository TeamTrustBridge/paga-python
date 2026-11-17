"""Persistent Payment Account operations for the Paga Engine API.

A persistent payment account is a standing instruction that lets a customer
pay you repeatedly from the same account, without a fresh payment request
each time.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .auth import (
    DELETE_PERSISTENT_ACCOUNT_HASH_FIELDS,
    GET_PERSISTENT_ACCOUNT_HASH_FIELDS,
    REGISTER_PERSISTENT_ACCOUNT_HASH_FIELDS,
    UPDATE_PERSISTENT_ACCOUNT_HASH_FIELDS,
)
from .models import PagaResponse, PersistentPaymentAccountResponse

__all__ = ["PersistentPaymentAccountMixin"]


class PersistentPaymentAccountMixin:
    """Persistent payment account operations, plus payment request history."""

    async def register_persistent_payment_account(
        self,
        *,
        reference_number: str,
        account_reference: str,
        financial_identification_number: str,
        credit_bank_id: str,
        credit_bank_account_number: str,
        callback_url: str,
        account_name: str,
        first_name: str,
        last_name: str,
        phone_number: Optional[str] = None,
        email: Optional[str] = None,
        funding_transaction_limit: Optional[float] = None,
    ) -> PersistentPaymentAccountResponse:
        """Register a persistent payment account.

        Operation: Collect API - Register a persistent payment account.

        ``account_reference`` must be 11 to 30 characters. Paga calls your
        ``callback_url`` whenever the account is funded.

        Args:
            reference_number: Your unique reference for this request.
            account_reference: Your permanent ID for the account. Between 11
                and 30 characters.
            financial_identification_number: The customer's BVN or NIN.
            credit_bank_id: The credit bank's UUID. From :meth:`get_collect_banks`.
            credit_bank_account_number: The credit account number.
            callback_url: Where Paga sends the funding callback.
            account_name: The customer's full name, as registered with the
                credit bank (for example ``"Bellview Walker"``).
            first_name: The customer's first name.
            last_name: The customer's last name.
            phone_number: The customer's phone number. Paga requires it when
                no email is supplied.
            email: The customer's email address. Paga requires it when no
                phone number is supplied.
            funding_transaction_limit: Optional maximum amount that may be
                transferred to the persistent account.

        Returns:
            The parsed :class:`PersistentPaymentAccountResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "accountReference": account_reference,
            "financialIdentificationNumber": financial_identification_number,
            "creditBankId": credit_bank_id,
            "creditBankAccountNumber": credit_bank_account_number,
            "callbackUrl": callback_url,
            "accountName": account_name,
            "firstName": first_name,
            "lastName": last_name,
        }
        if phone_number is not None:
            payload["phoneNumber"] = phone_number
        if email is not None:
            payload["email"] = email
        if funding_transaction_limit is not None:
            payload["fundingTransactionLimit"] = funding_transaction_limit
        response = await self._request(
            "POST",
            "/registerPersistentPaymentAccount",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=REGISTER_PERSISTENT_ACCOUNT_HASH_FIELDS,
        )
        return PersistentPaymentAccountResponse.model_validate(response.model_dump())

    async def delete_persistent_payment_account(
        self,
        *,
        reference_number: str,
        account_identifier: str,
        reason: Optional[str] = None,
    ) -> PagaResponse:
        """Delete a persistent payment account.

        Operation: Collect API - Delete a persistent payment account.

        Args:
            reference_number: Your unique reference for this request.
            account_identifier: The account's NUBAN **or** its
                ``accountReference``.
            reason: Optional reason for the deletion.

        Returns:
            The parsed :class:`PagaResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "accountIdentifier": account_identifier,
        }
        if reason is not None:
            payload["reason"] = reason
        response = await self._request(
            "POST",
            "/deletePersistentPaymentAccount",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=DELETE_PERSISTENT_ACCOUNT_HASH_FIELDS,
        )
        return response

    async def update_persistent_payment_account(
        self,
        *,
        reference_number: str,
        account_identifier: str,
        financial_identification_number: Optional[str] = None,
        credit_bank_id: Optional[str] = None,
        credit_bank_account_number: Optional[str] = None,
        callback_url: Optional[str] = None,
        account_name: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        phone_number: Optional[str] = None,
    ) -> PersistentPaymentAccountResponse:
        """Update a persistent payment account.

        Operation: Collect API - Update a persistent payment account.

        Send only what you want to change. Every field takes part in the
        hash, so send the current value of the ones you are not changing.

        Args:
            reference_number: Your unique reference for this request.
            account_identifier: The account's NUBAN **or** its
                ``accountReference``.
            financial_identification_number: Optional new BVN or NIN.
            credit_bank_id: Optional new credit bank UUID.
            credit_bank_account_number: Optional new credit account number.
            callback_url: Optional new callback URL.
            account_name: Optional new full customer name.
            first_name: Optional new customer first name.
            last_name: Optional new customer last name.
            phone_number: Optional new customer phone number.

        Returns:
            The parsed :class:`PersistentPaymentAccountResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "accountIdentifier": account_identifier,
        }
        if financial_identification_number is not None:
            payload["financialIdentificationNumber"] = financial_identification_number
        if credit_bank_id is not None:
            payload["creditBankId"] = credit_bank_id
        if credit_bank_account_number is not None:
            payload["creditBankAccountNumber"] = credit_bank_account_number
        if callback_url is not None:
            payload["callbackUrl"] = callback_url
        if account_name is not None:
            payload["accountName"] = account_name
        if first_name is not None:
            payload["firstName"] = first_name
        if last_name is not None:
            payload["lastName"] = last_name
        if phone_number is not None:
            payload["phoneNumber"] = phone_number

        response = await self._request(
            "POST",
            "/updatePersistentPaymentAccount",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=UPDATE_PERSISTENT_ACCOUNT_HASH_FIELDS,
        )
        return PersistentPaymentAccountResponse.model_validate(response.model_dump())

    async def get_persistent_payment_account(
        self,
        *,
        reference_number: str,
        account_identifier: str,
    ) -> PersistentPaymentAccountResponse:
        """Get a persistent payment account.

        Operation: Collect API - Get a persistent payment account.

        Args:
            reference_number: Your unique reference for this request.
            account_identifier: The account's NUBAN **or** its
                ``accountReference``.

        Returns:
            The parsed :class:`PersistentPaymentAccountResponse`.
        """
        response = await self._request(
            "POST",
            "/getPersistentPaymentAccount",
            {
                "referenceNumber": reference_number,
                "accountIdentifier": account_identifier,
            },
            use_hash=True,
            use_basic=True,
            hash_fields=GET_PERSISTENT_ACCOUNT_HASH_FIELDS,
        )
        return PersistentPaymentAccountResponse.model_validate(response.model_dump())
