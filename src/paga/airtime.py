"""Airtime and data purchase operations for the Paga Engine API.

Covers the **Make payments → Airtime and data** section of Paga's
documentation.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .auth import AIRTIME_HASH_FIELDS, DATA_BUNDLE_HASH_FIELDS, MOBILE_OPERATORS_HASH_FIELDS
from .models import DataBundlesResponse, MobileOperatorsResponse, PurchaseResponse

__all__ = ["AirtimeMixin"]


class AirtimeMixin:
    """Airtime and data operations."""

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
