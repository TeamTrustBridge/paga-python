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
    HISTORY_HASH_FIELDS,
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
        }
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
    ) -> PagaResponse:
        """Delete a persistent payment account.

        Operation: Collect API - Delete a persistent payment account.

        Args:
            reference_number: Your unique reference for this request.
            account_identifier: The account's NUBAN **or** its
                ``accountReference``.

        Returns:
            The parsed :class:`PagaResponse`.
        """
        response = await self._request(
            "POST",
            "/deletePersistentPaymentAccount",
            {
                "referenceNumber": reference_number,
                "accountIdentifier": account_identifier,
            },
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

    async def get_payment_request_history(
        self,
        *,
        reference_number: str,
    ) -> PagaResponse:
        """Get the history of your payment requests.

        Operation: Collect API - Payment request history.

        Args:
            reference_number: Your unique reference for this request.

        Returns:
            The parsed :class:`PagaResponse`.
        """
        response = await self._request(
            "POST",
            "/history",
            {"referenceNumber": reference_number},
            use_hash=True,
            use_basic=True,
            hash_fields=HISTORY_HASH_FIELDS,
            raise_on_error=False,
        )
        return response
