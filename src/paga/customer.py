"""Customer registration and KYC operations for the Paga Engine API.

Registering a customer on the Business API is how you open an account for
someone. The plain registration takes the customer's details; the KYC
variants additionally take photographs, and are sent as
``multipart/form-data``.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .auth import (
    CUSTOMER_ACCOUNT_PHOTO_HASH_FIELDS,
    CUSTOMER_HASH_FIELDS,
    CUSTOMER_IDENTIFICATION_HASH_FIELDS,
)
from .models import CustomerResponse

__all__ = ["CustomerMixin"]


class CustomerMixin:
    """Customer registration and KYC operations."""

    async def register_customer(
        self,
        *,
        reference_number: str,
        customer_phone_number: str,
        customer_first_name: str,
        customer_last_name: str,
        customer_email: str,
        customer_date_of_birth: str,
        customer_address: Optional[Dict[str, Any]] = None,
        customer_reference: Optional[str] = None,
    ) -> CustomerResponse:
        """Register a customer.

        Operation: Business API - Register a customer.

        Args:
            reference_number: Your unique reference for this request.
            customer_phone_number: The customer's phone number. It must not
                already belong to a registered customer.
            customer_first_name: The customer's first name.
            customer_last_name: The customer's last name.
            customer_email: The customer's email address.
            customer_date_of_birth: The customer's date of birth, as
                ``YYYY-MM-DD``.
            customer_address: Optional address, as an object.
            customer_reference: Optional reference you hold for the customer.

        Returns:
            The parsed :class:`CustomerResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "customerPhoneNumber": customer_phone_number,
            "customerFirstName": customer_first_name,
            "customerLastName": customer_last_name,
            "customerEmail": customer_email,
            "customerDateOfBirth": customer_date_of_birth,
        }
        if customer_address is not None:
            payload["customerAddress"] = customer_address
        if customer_reference is not None:
            payload["customerReference"] = customer_reference

        response = await self._request(
            "POST",
            "/registerCustomer",
            payload,
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=CUSTOMER_HASH_FIELDS,
        )
        return CustomerResponse.model_validate(response.model_dump())

    async def register_customer_with_kyc(
        self,
        *,
        reference_number: str,
        customer_phone_number: str,
        customer_email: str,
        customer_first_name: str,
        customer_last_name: str,
        customer_date_of_birth: str,
        customer_gender: str,
        customer_account_photo: bytes,
        customer_id_photo: bytes,
        customer_address: Optional[Dict[str, Any]] = None,
        customer_marital_status: Optional[str] = None,
        customer_preferred_language_iso_code: Optional[str] = None,
        customer_id_type: Optional[str] = None,
        customer_id_number: Optional[str] = None,
        customer_id_expiration_date: Optional[str] = None,
        optin_for_wallet_savings: Optional[bool] = None,
        customer_reference: Optional[str] = None,
        account_photo_filename: str = "account-photo.jpg",
        account_photo_content_type: str = "image/jpeg",
        id_photo_filename: str = "id-photo.jpg",
        id_photo_content_type: str = "image/jpeg",
    ) -> CustomerResponse:
        """Register a customer with KYC photographs.

        Operation: Business API - Register a customer with KYC.

        Sent as ``multipart/form-data``: a ``customer`` JSON part, plus
        ``customerAccountPhoto`` and ``customerIdPhoto`` image parts. Each
        photograph must be a JPEG of at most 500 KB.

        Args:
            reference_number: Your unique reference for this request.
            customer_phone_number: The customer's phone number.
            customer_email: The customer's email address.
            customer_first_name: The customer's first name.
            customer_last_name: The customer's last name.
            customer_date_of_birth: The customer's date of birth, as
                ``YYYY-MM-DD``.
            customer_gender: ``"FEMALE"`` or ``"MALE"``.
            customer_account_photo: The account photograph's bytes.
            customer_id_photo: The identification photograph's bytes.
            customer_address: Optional address object.
            customer_marital_status: Optional marital status.
            customer_preferred_language_iso_code: Optional ISO 639-1 code.
            customer_id_type: Optional identification type.
            customer_id_number: Optional identification number.
            customer_id_expiration_date: Optional identification expiry date.
            optin_for_wallet_savings: Optional wallet savings opt-in.
            customer_reference: Optional reference you hold for the customer.
            account_photo_filename: Filename for the account photograph.
            account_photo_content_type: Content type of the account photograph.
            id_photo_filename: Filename for the identification photograph.
            id_photo_content_type: Content type of the identification photograph.

        Returns:
            The parsed :class:`CustomerResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "customerPhoneNumber": customer_phone_number,
            "customerEmail": customer_email,
            "customerFirstName": customer_first_name,
            "customerLastName": customer_last_name,
            "customerDateOfBirth": customer_date_of_birth,
            "customerGender": customer_gender,
        }
        if customer_address is not None:
            payload["customerAddress"] = customer_address
        if customer_marital_status is not None:
            payload["customerMaritalStatus"] = customer_marital_status
        if customer_preferred_language_iso_code is not None:
            payload["customerPreferredLanguageISOCode"] = customer_preferred_language_iso_code
        if customer_id_type is not None:
            payload["customerIdType"] = customer_id_type
        if customer_id_number is not None:
            payload["customerIdNumber"] = customer_id_number
        if customer_id_expiration_date is not None:
            payload["customerIdExpirationDate"] = customer_id_expiration_date
        if optin_for_wallet_savings is not None:
            payload["optinForWalletSavings"] = optin_for_wallet_savings
        if customer_reference is not None:
            payload["customerReference"] = customer_reference

        response = await self._multipart_request(
            "POST",
            "/registerCustomerWithKYC",
            {
                "customer": payload,
                "customerAccountPhoto": (
                    account_photo_filename,
                    bytes(customer_account_photo),
                    account_photo_content_type,
                ),
                "customerIdPhoto": (
                    id_photo_filename,
                    bytes(customer_id_photo),
                    id_photo_content_type,
                ),
            },
            hash_payload=payload,
            hash_fields=CUSTOMER_HASH_FIELDS,
        )
        return CustomerResponse.model_validate(response.model_dump())

    async def register_customer_account_photo(
        self,
        *,
        reference_number: str,
        customer_phone_number: str,
        customer_account_photo: bytes,
        photo_filename: str = "account-photo.jpg",
        photo_content_type: str = "image/jpeg",
    ) -> CustomerResponse:
        """Upload a customer's account photograph.

        Operation: Business API - Register a customer account photo.

        Sent as ``multipart/form-data``: a ``customer`` JSON part plus a
        ``customerAccountPhoto`` image part.

        Args:
            reference_number: Your unique reference for this request.
            customer_phone_number: The customer's phone number.
            customer_account_photo: The account photograph's bytes.
            photo_filename: Filename for the photograph.
            photo_content_type: Content type of the photograph.

        Returns:
            The parsed :class:`CustomerResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "customerPhoneNumber": customer_phone_number,
        }
        response = await self._multipart_request(
            "POST",
            "/registerCustomerAccountPhoto",
            {
                "customer": payload,
                "customerAccountPhoto": (
                    photo_filename,
                    bytes(customer_account_photo),
                    photo_content_type,
                ),
            },
            hash_payload=payload,
            hash_fields=CUSTOMER_ACCOUNT_PHOTO_HASH_FIELDS,
        )
        return CustomerResponse.model_validate(response.model_dump())

    async def register_customer_identification(
        self,
        *,
        reference_number: str,
        customer_phone_number: str,
        customer_id_type: str,
        customer_id_number: str,
        customer_id_expiration_date: str,
        customer_id_photo: bytes,
        photo_filename: str = "id-photo.jpg",
        photo_content_type: str = "image/jpeg",
    ) -> CustomerResponse:
        """Upload a customer's identification.

        Operation: Business API - Register a customer identification.

        Sent as ``multipart/form-data``: a ``customer`` JSON part plus a
        ``customerIdPhoto`` image part.

        Args:
            reference_number: Your unique reference for this request.
            customer_phone_number: The customer's phone number.
            customer_id_type: The identification type, e.g. ``"BVN"``.
            customer_id_number: The identification number.
            customer_id_expiration_date: When the identification expires.
            customer_id_photo: The identification photograph's bytes.
            photo_filename: Filename for the photograph.
            photo_content_type: Content type of the photograph.

        Returns:
            The parsed :class:`CustomerResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "customerPhoneNumber": customer_phone_number,
            "customerIdType": customer_id_type,
            "customerIdNumber": customer_id_number,
            "customerIdExpirationDate": customer_id_expiration_date,
        }
        response = await self._multipart_request(
            "POST",
            "/registerCustomerIdentification",
            {
                "customer": payload,
                "customerIdPhoto": (
                    photo_filename,
                    bytes(customer_id_photo),
                    photo_content_type,
                ),
            },
            hash_payload=payload,
            hash_fields=CUSTOMER_IDENTIFICATION_HASH_FIELDS,
        )
        return CustomerResponse.model_validate(response.model_dump())
