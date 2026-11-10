"""Response and payload models for the Paga Engine API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class PagaResponse(BaseModel):
    """Normalized envelope returned by Paga Engine API operations."""

    model_config = ConfigDict(extra="allow")

    responseCode: int = Field(default=0, description="Status code of the response. 0 indicates success.")
    responseCategoryCode: Optional[int] = Field(default=None)
    message: Optional[str] = Field(default=None)
    referenceNumber: Optional[str] = Field(default=None)
    transactionId: Optional[str] = Field(default=None)
    withdrawalCode: Optional[str] = Field(default=None)
    reversalId: Optional[str] = Field(default=None)
    currency: Optional[str] = Field(default=None)
    exchangeRate: Optional[float] = Field(default=None)
    fee: Optional[float] = Field(default=None)
    receiverRegistrationStatus: Optional[str] = Field(default=None)
    recipientAccountHolderName: Optional[str] = Field(default=None)

    @property
    def is_success(self) -> bool:
        """Return True when the operation completed successfully."""
        return self.responseCode == 0


class CollectPaymentMethodResult(BaseModel):
    """Payment method details returned as part of a payment request."""

    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)


class CollectPaymentRequestResponse(BaseModel):
    """Response returned when creating a Paga payment request."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    requestAmount: Optional[float] = None
    totalPaymentAmount: Optional[float] = None
    paymentMethods: List[CollectPaymentMethodResult] = Field(default_factory=list)
    expiryDateTimeUTC: Optional[str] = None
    isPayerPagaAccountHolder: Optional[bool] = None
    bankName: Optional[str] = None


class CheckoutVerifyChargeResponse(BaseModel):
    """Response returned when verifying a checkout charge."""

    model_config = ConfigDict(extra="allow")

    status_code: Optional[int] = None
    status_message: Optional[str] = None
    chargeId: Optional[str] = None
    amount: Optional[float] = None
    currency: Optional[str] = None


class MerchantPaymentResponse(BaseModel):
    """Response returned when paying a bill."""

    model_config = ConfigDict(extra="allow")

    responseCode: Optional[int] = None
    responseCategoryCode: Optional[int] = None
    message: Optional[str] = None
    referenceNumber: Optional[str] = None
    merchantTransactionReference: Optional[str] = None
    transactionId: Optional[str] = None
    reversalId: Optional[str] = None
    currency: Optional[str] = None
    exchangeRate: Optional[float] = None
    fee: Optional[float] = None
    integrationStatus: Optional[str] = None
    additionalProperties: Optional[Dict[str, Any]] = None


class PurchaseResponse(BaseModel):
    """Response returned when buying airtime or data."""

    model_config = ConfigDict(extra="allow")

    responseCode: Optional[int] = None
    responseCategoryCode: Optional[int] = None
    message: Optional[str] = None
    referenceNumber: Optional[str] = None
    transactionId: Optional[str] = None
    reversalId: Optional[str] = None
    currency: Optional[str] = None
    exchangeRate: Optional[float] = None
    integrationStatus: Optional[str] = None
    fee: Optional[float] = None


class PaymentStatusData(BaseModel):
    """Payment status details nested in a payment status response."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    requestAmount: Optional[float] = None
    totalPaymentAmount: Optional[float] = None
    expiryDateTimeUTC: Optional[str] = None
    additionalData: Optional[Dict[str, Any]] = None
    refundStatus: Optional[str] = None


class PaymentStatusResponse(BaseModel):
    """Response returned when checking the status of a payment request."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    data: Optional[PaymentStatusData] = None


class DepositToBankResponse(BaseModel):
    """Response returned when sending money to a bank account or Paga wallet."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    transactionId: Optional[str] = None
    destinationAccountHolderNameAtBank: Optional[str] = None
    fee: Optional[float] = None
    vat: Optional[float] = None
    currency: Optional[str] = None
    exchangeRate: Optional[float] = None
    sessionId: Optional[str] = None


class RefundResponse(BaseModel):
    """Response returned when refunding or cancelling a payment request."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    refundAmount: Optional[float] = None
    currency: Optional[str] = None
    refundDestination: Optional[str] = None


class PagaPaymentCallback(BaseModel):
    """Normalized payment callback (notification) payload sent by Paga."""

    model_config = ConfigDict(extra="allow")

    event: Optional[str] = None
    notificationId: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    externalReferenceNumber: Optional[str] = None
    state: Optional[str] = None
    outstandingBalance: Optional[float] = None
    paymentAmount: Optional[float] = None
    cumulativePaymentAmount: Optional[float] = None
    collectionFee: Optional[float] = None
    fundingDetails: Optional[Dict[str, Any]] = None
    hash: Optional[str] = None
