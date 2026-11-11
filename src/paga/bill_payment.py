"""Bill payment operations for the Paga Engine API.

Covers the **Make payments → Bill payment (VAS)** section of Paga's
documentation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from .auth import (
    BILL_PAYMENT_HASH_FIELDS,
    MERCHANT_ACCOUNT_DETAILS_HASH_FIELDS,
    MERCHANT_SERVICES_HASH_FIELDS,
    MERCHANTS_HASH_FIELDS,
)
from .models import (
    MerchantAccountDetailsResponse,
    MerchantPaymentResponse,
    MerchantsResponse,
    MerchantServicesResponse,
)

__all__ = ["BillPaymentMixin"]


class BillPaymentMixin:
    """Bill payment operations."""

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
            merchant_account: The biller's UUID. From :meth:`get_merchants`.
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
