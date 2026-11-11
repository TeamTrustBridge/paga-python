"""Response and payload models for the Paga Engine API."""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, model_validator


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


class AccountBalanceResponse(BaseModel):
    """Response returned when checking the business account balance."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    totalBalance: Optional[str] = None
    availableBalance: Optional[float] = None
    currency: Optional[str] = None


class SubsidiaryAccountResponse(BaseModel):
    """Response returned when creating a subsidiary account."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    accountNumber: Optional[str] = None
    accountReference: Optional[str] = None
    status: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None


class SubsidiaryMoneyResponse(BaseModel):
    """Response returned when charging or topping up a subsidiary account."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    transactionId: Optional[str] = None
    newBalance: Optional[float] = None


class SubsidiaryTransferResponse(BaseModel):
    """Response returned when transferring between subsidiary accounts."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    transactionId: Optional[str] = None
    source: Optional[Dict[str, Any]] = None
    destination: Optional[Dict[str, Any]] = None


class SubsidiaryBalanceResponse(BaseModel):
    """Response returned when getting a subsidiary account balance."""

    model_config = ConfigDict(extra="allow")

    statusCode: Optional[str] = None
    accountReference: Optional[str] = None
    accountNumber: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None
    timeStamp: Optional[str] = None


class SubsidiaryHistoryResponse(BaseModel):
    """Response returned when getting a subsidiary account history."""

    model_config = ConfigDict(extra="allow")

    statusCode: Optional[str] = None
    itemCount: Optional[int] = None
    totalItems: Optional[int] = None
    totalPages: Optional[int] = None
    currentPage: Optional[int] = None
    transactions: List[TransactionItem] = Field(default_factory=list)


class TransactionItem(BaseModel):
    """A single transaction in a business transaction history."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    status: Optional[str] = None
    amount: Optional[float] = None
    fee: Optional[float] = None
    balance: Optional[float] = None
    dateUTC: Optional[int] = None


class TransactionHistoryResponse(BaseModel):
    """Response returned when fetching the business transaction history."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    items: List[TransactionItem] = Field(default_factory=list)


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


# --------------------------------------------------------------------------- #
# Directory lookups (banks, operators, bundles, billers)
# --------------------------------------------------------------------------- #


class CollectBank(BaseModel):
    """A bank a customer can pay from, as listed by the Collect API."""

    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    uuid: Optional[str] = None


class CollectBanksResponse(BaseModel):
    """Response returned when listing the banks available to a customer."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    banks: List[CollectBank] = Field(default_factory=list)


class Bank(BaseModel):
    """An institution that can be paid, as listed by the Business API."""

    model_config = ConfigDict(extra="allow")

    uuid: Optional[str] = None
    name: Optional[str] = None
    interInstitutionCode: Optional[str] = None
    sortCode: Optional[str] = None


class BanksResponse(BaseModel):
    """Response returned when listing payable institutions.

    ``uuid`` is what you send as ``destinationBankUUID``. Paga's own UUID is
    ``AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA`` (send to a Paga wallet).
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    banks: List[Bank] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def _accept_singular_bank_key(cls, data: Any) -> Any:
        """Accept the singular ``bank`` key Paga's legacy docs show.

        The current Business API returns ``banks``; the legacy operations
        page documents ``bank``. Read both.
        """
        if isinstance(data, dict) and not data.get("banks") and data.get("bank"):
            data = dict(data)
            data["banks"] = data.pop("bank")
        return data


class MobileOperator(BaseModel):
    """A mobile network that can be topped up."""

    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    mobileOperatorCode: Optional[str] = None


class MobileOperatorsResponse(BaseModel):
    """Response returned when listing mobile operators.

    ``mobileOperatorCode`` is what you send as ``mobileOperatorPublicId`` when
    buying airtime, and as ``operatorPublicId`` when listing data bundles.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    mobileOperator: List[MobileOperator] = Field(default_factory=list)


class DataBundle(BaseModel):
    """A data bundle offered by a mobile operator."""

    model_config = ConfigDict(extra="allow")

    serviceId: Optional[str] = None
    serviceName: Optional[str] = None
    servicePrice: Optional[float] = None
    validityPeriod: Optional[str] = None
    dataValue: Optional[str] = None


class DataBundlesResponse(BaseModel):
    """Response returned when listing an operator's data bundles.

    Send ``serviceId`` as ``mobileOperatorServiceId`` and **exactly**
    ``servicePrice`` as ``amount``.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    mobileOperatorServices: List[DataBundle] = Field(default_factory=list)


class Merchant(BaseModel):
    """A biller that can be paid."""

    model_config = ConfigDict(extra="allow")

    displayName: Optional[str] = None
    name: Optional[str] = None
    description: Optional[str] = None
    uuid: Optional[str] = None


class MerchantsResponse(BaseModel):
    """Response returned when listing billers.

    ``uuid`` is what you send as ``merchantAccount``.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    merchants: List[Merchant] = Field(default_factory=list)


class MerchantService(BaseModel):
    """Something a biller can be paid for."""

    model_config = ConfigDict(extra="allow")

    name: Optional[str] = None
    code: Optional[str] = None
    price: Optional[float] = None
    shortCode: Optional[str] = None


class MerchantServicesResponse(BaseModel):
    """Response returned when listing a biller's services.

    An empty ``services`` list means any amount is allowed. A ``price`` of
    ``0.0`` means the customer chooses the amount. Otherwise pay the
    service's ``price``.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    services: List[MerchantService] = Field(default_factory=list)


class MerchantAccountDetailsResponse(BaseModel):
    """Response returned when validating a customer's account at a biller.

    ``details`` varies per biller, so it is left as a free-form mapping.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    customerName: Optional[str] = None
    phoneNumber: Optional[str] = None
    accountNumber: Optional[str] = None
    address: Optional[str] = None
    details: Optional[Dict[str, Any]] = None


class ValidateDepositToBankResponse(BaseModel):
    """Response returned when validating a destination bank account.

    ``fee`` and ``vat`` quote what the transfer will cost, before you send it.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    responseCategoryCode: Optional[int] = None
    message: Optional[str] = None
    destinationAccountHolderNameAtBank: Optional[str] = None
    fee: Optional[float] = None
    vat: Optional[float] = None


# --------------------------------------------------------------------------- #
# Status lookups
# --------------------------------------------------------------------------- #


class TransactionStatusResponse(BaseModel):
    """Response returned when checking a transaction's status.

    Covers the last 48 hours only. ``status`` is human-readable and may be
    reworded at any time — branch on ``responseCode``, never on ``status``.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    responseCategoryCode: Optional[int] = None
    message: Optional[str] = None
    status: Optional[str] = None
    transactionId: Optional[str] = None
    transactionReference: Optional[str] = None
    transactionType: Optional[str] = None
    dateUTC: Optional[int] = None
    amount: Optional[float] = None
    currency: Optional[str] = None
    merchantTransactionReference: Optional[str] = None
    additionalProperties: Optional[Dict[str, Any]] = None
    reversalId: Optional[str] = None
    exchangeRate: Optional[float] = None
    fee: Optional[float] = None
    integrationStatus: Optional[str] = None
    commissionEarned: Optional[float] = None


class RecentTransaction(BaseModel):
    """A single transaction on the business account."""

    model_config = ConfigDict(extra="allow")

    itemNumber: Optional[int] = None
    dateUTC: Optional[int] = None
    description: Optional[str] = None
    amount: Optional[float] = None
    status: Optional[str] = None
    transactionId: Optional[str] = None
    referenceNumber: Optional[str] = None
    currency: Optional[str] = None
    exchangeRate: Optional[float] = None


class RecentTransactionsResponse(BaseModel):
    """Response returned when listing the five most recent transactions."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    recordCount: Optional[int] = None
    currency: Optional[str] = None
    items: List[RecentTransaction] = Field(default_factory=list)


class RefundStatusResponse(BaseModel):
    """Response returned when checking whether a payment request was refunded.

    Call with the **original payment request's** ``referenceNumber``.
    ``data.refundStatus`` becomes ``"refunded"`` once the refund is made.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    data: Optional[PaymentStatusData] = None

    @property
    def refundStatus(self) -> Optional[str]:
        """The refund status of the underlying payment request."""
        return self.data.refundStatus if self.data is not None else None

    @property
    def isRefunded(self) -> bool:
        """Whether the payment request has been refunded."""
        return (self.refundStatus or "").strip().lower() == "refunded"


# --------------------------------------------------------------------------- #
# Callback payloads
# --------------------------------------------------------------------------- #


class MoneyTransferNotification(BaseModel):
    """Notification Paga sends when a money transfer is processed.

    Operation: Money transfer - Handle the notification.

    Sent to your ``statusCallbackUrl`` once a transfer is processed. Paga
    retries until you answer HTTP 200 with ``{"status": "SUCCESS"}``, so
    de-duplicate on ``referenceNumber``.
    """

    model_config = ConfigDict(extra="allow")

    responseCode: Optional[int] = None
    responseCategoryCode: Optional[int] = None
    message: Optional[str] = None
    referenceNumber: Optional[str] = None
    transactionId: Optional[str] = None
    transactionReference: Optional[str] = None
    transactionType: Optional[str] = None
    transactionDate: Optional[str] = None
    amount: Optional[str] = None
    currency: Optional[str] = None
    fee: Optional[float] = None
    vat: Optional[float] = None
    sessionId: Optional[str] = None
    destinationAccountHolderNameAtBank: Optional[str] = None
    reversalId: Optional[str] = None
    exchangeRate: Optional[float] = None
    integrationStatus: Optional[str] = None


class UsdPaymentWebhook(BaseModel):
    """Webhook Paga sends for a USD (ACH, Wire, Swift) payment.

    Operation: Bank transfer (ACH, Wire and Swift) - Handle the webhook.

    This webhook carries **no signature** — there is no hash to verify.
    Authenticate it at the transport layer (TLS plus, ideally, an allow-listed
    source IP) and de-duplicate on ``referenceNumber`` + ``paymentId``.
    """

    model_config = ConfigDict(extra="allow")

    event: Optional[str] = None
    referenceNumber: Optional[str] = None
    paymentId: Optional[str] = None
    paymentStatus: Optional[str] = None
    receivedAmounts: Optional[Dict[str, Any]] = None
    serviceDetails: Optional[Dict[str, Any]] = None
    errorCode: Optional[str] = None
    errorMessage: Optional[Dict[str, Any]] = None

    @property
    def isCaptured(self) -> bool:
        """Whether the dollar payment cleared."""
        return (self.event or "").strip().upper() == "CAPTURED"

    @property
    def isFundingFailed(self) -> bool:
        """Whether the dollar payment failed to clear."""
        return (self.event or "").strip().upper() == "FUNDING_FAILED"


# --------------------------------------------------------------------------- #
# Direct Debit (Open Banking)
# --------------------------------------------------------------------------- #


class DirectDebitSessionMetadata(BaseModel):
    """Metadata describing a hosted Direct Debit set-up session."""

    model_config = ConfigDict(extra="allow")

    amountLimit: Optional[float] = None
    authorizationAmount: Optional[float] = None
    currency: Optional[str] = None
    accountReference: Optional[str] = None
    allowPartialPayment: Optional[bool] = None
    allowMultipleUse: Optional[bool] = None


class DirectDebitSessionData(BaseModel):
    """The set-up session Paga created for you to redirect the customer to."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    sessionKey: Optional[str] = None
    status: Optional[str] = None
    checkoutUrl: Optional[str] = None
    redirectUrl: Optional[str] = None
    callbackUrl: Optional[str] = None
    enabledPaymentMethods: List[str] = Field(default_factory=list)
    initiatedAt: Optional[str] = None
    sessionExpiresAt: Optional[str] = None
    paymentExpiresAt: Optional[str] = None
    metadata: Optional[DirectDebitSessionMetadata] = None


class DirectDebitSessionResponse(BaseModel):
    """Response returned when starting a hosted Direct Debit set-up session."""

    model_config = ConfigDict(extra="allow")

    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    data: Optional[DirectDebitSessionData] = None

    @property
    def checkoutUrl(self) -> Optional[str]:
        """Where to redirect the customer to complete the mandate set-up."""
        return self.data.checkoutUrl if self.data is not None else None


class MandateProcess(BaseModel):
    """A single mandate in a mandate status response."""

    model_config = ConfigDict(extra="allow")

    ProcessStatusId: Optional[str] = None
    AccountReference: Optional[str] = None
    StatusMessage: Optional[str] = None
    CreatedDateTimeUTC: Optional[str] = None


class MandateAdditionalData(BaseModel):
    """The ``additionalData`` block of a mandate status response."""

    model_config = ConfigDict(extra="allow")

    mandate: List[MandateProcess] = Field(default_factory=list)


class MandateStatusData(BaseModel):
    """The ``data`` block of a mandate status response."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    requestAmount: Optional[float] = None
    totalPaymentAmount: Optional[float] = None
    paymentMethods: List[CollectPaymentMethodResult] = Field(default_factory=list)
    expiryDateTimeUTC: Optional[str] = None
    isPayerPagaAccountHolder: Optional[bool] = None
    additionalData: Optional[MandateAdditionalData] = None


class MandateStatusResponse(BaseModel):
    """Response returned when checking a mandate's status.

    ``data.statusCode`` stays ``"1"`` / ``"pending"`` forever, so it tells
    you nothing. Read ``data.additionalData.mandate[].ProcessStatusId``
    instead — ``PENDING``, ``VERIFIED``, ``APPROVED`` or ``REJECTED``. Charge
    only when it is ``APPROVED``.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    data: Optional[MandateStatusData] = None

    @property
    def mandateStatus(self) -> Optional[str]:
        """The mandate's ``ProcessStatusId``, if Paga reported one."""
        data = self.data
        if data is None or data.additionalData is None:
            return None
        mandates = data.additionalData.mandate
        if not mandates:
            return None
        return mandates[0].ProcessStatusId

    @property
    def isApproved(self) -> bool:
        """Whether the mandate may be charged."""
        return (self.mandateStatus or "").strip().upper() == "APPROVED"


class ChargeMandateResponse(BaseModel):
    """Response returned when charging a mandate.

    A success here means the charge was **accepted**, not completed. Fulfil
    only once the charge callback confirms it.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None


class ChargeMandateStatusData(BaseModel):
    """The ``data`` block of a charge status response.

    Paga capitalises these keys, so they are kept verbatim.
    """

    model_config = ConfigDict(extra="allow")

    statusCode: Optional[int] = None
    ReferenceNumber: Optional[str] = None
    Amount: Optional[float] = None
    ProcessStatusId: Optional[str] = None


class ChargeMandateStatusResponse(BaseModel):
    """Response returned when checking a mandate charge's status.

    ``data.statusCode`` is ``0`` charged, ``1`` pending, ``-1`` invalid (wrong
    details, expired, or limit exceeded) and ``-4`` unknown.
    """

    model_config = ConfigDict(extra="allow")

    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    data: Optional[ChargeMandateStatusData] = None

    @property
    def chargeStatus(self) -> Optional[int]:
        """The charge's own status code, when Paga reported one."""
        return self.data.statusCode if self.data is not None else None


class DisableMandateResponse(BaseModel):
    """Response returned when disabling a mandate.

    Afterwards the mandate's ``ProcessStatusId`` becomes ``REJECTED`` and it
    can never be charged again.
    """

    model_config = ConfigDict(extra="allow")

    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    referenceNumber: Optional[str] = None
    data: Optional[Any] = None


# --------------------------------------------------------------------------- #
# Persistent payment accounts and customers
# --------------------------------------------------------------------------- #


class PersistentPaymentAccountResponse(BaseModel):
    """Response returned for a persistent payment account operation."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    statusCode: Optional[str] = None
    statusMessage: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    accountNumber: Optional[str] = None
    accountReference: Optional[str] = None
    financialIdentificationNumber: Optional[str] = None
    creditBankId: Optional[str] = None
    creditBankAccountNumber: Optional[str] = None
    callbackUrl: Optional[str] = None
    status: Optional[str] = None
    balance: Optional[float] = None
    currency: Optional[str] = None


class CustomerResponse(BaseModel):
    """Response returned when registering a customer."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    responseCategoryCode: Optional[int] = None
    message: Optional[str] = None
    customerReference: Optional[str] = None
    customerPhoneNumber: Optional[str] = None
    customerFirstName: Optional[str] = None
    customerLastName: Optional[str] = None
    customerEmail: Optional[str] = None
    customerDateOfBirth: Optional[str] = None
    customerAddress: Optional[str] = None
    status: Optional[str] = None


class MoneyTransferItem(BaseModel):
    """One item in a bulk money transfer."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    amount: Optional[str] = None
    destinationAccount: Optional[str] = None
    remarks: Optional[str] = None
    currency: Optional[str] = None


class BulkTransferResult(BaseModel):
    """The outcome of one item in a bulk money transfer."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    transactionId: Optional[str] = None
    withdrawalCode: Optional[str] = None
    exchangeRate: Optional[float] = None
    fee: Optional[float] = None
    currency: Optional[str] = None
    receiverRegistrationStatus: Optional[str] = None


class BulkMoneyTransferResponse(BaseModel):
    """Response returned when sending a bulk money transfer.

    ``responseCode`` ``1`` means the bulk partially succeeded: some items
    moved and some did not. Check each entry in ``results``.
    """

    model_config = ConfigDict(extra="allow")

    bulkReferenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    results: List[BulkTransferResult] = Field(default_factory=list)


class MoneyTransferResponse(BaseModel):
    """Response returned when sending money to a Paga wallet."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    responseCategoryCode: Optional[int] = None
    message: Optional[str] = None
    withdrawalCode: Optional[str] = None
    transactionId: Optional[str] = None
    reversalId: Optional[str] = None
    currency: Optional[str] = None
    exchangeRate: Optional[float] = None
    fee: Optional[float] = None
    receiverRegistrationStatus: Optional[str] = None
    recipientAccountHolderName: Optional[str] = None


class ValidateMoneyTransferResponse(BaseModel):
    """Response returned when validating a money transfer to a Paga wallet."""

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[int] = None
    message: Optional[str] = None
    fee: Optional[float] = None
    vat: Optional[float] = None
    recipientAccountHolderName: Optional[str] = None
    recipientRegistrationStatus: Optional[str] = None
    recipientKYCLevel: Optional[str] = None


class OperationStatusResponse(BaseModel):
    """Response returned when checking an operation's status.

    Note the field is ``transactionStatus``, not ``status``.
    """

    model_config = ConfigDict(extra="allow")

    referenceNumber: Optional[str] = None
    responseCode: Optional[Union[int, str]] = None
    transactionStatus: Optional[str] = None
    message: Optional[str] = None
    transactionId: Optional[str] = None
    fee: Optional[float] = None


class OnboardMerchantCredentials(BaseModel):
    """The credentials Paga issues for an onboarded merchant."""

    model_config = ConfigDict(extra="allow")

    merchantPublicId: Optional[str] = None
    merchantSecretKey: Optional[str] = None
    merchantHmac: Optional[str] = None


class OnboardMerchantUpdate(BaseModel):
    """The onboarding outcome for a merchant."""

    model_config = ConfigDict(extra="allow")

    status: Optional[str] = None
    credentials: Optional[OnboardMerchantCredentials] = None


class OnboardMerchantResponse(BaseModel):
    """Response returned when onboarding a merchant.

    Aggregators only.
    """

    model_config = ConfigDict(extra="allow")

    responseCode: Optional[int] = None
    message: Optional[str] = None
    onboardingUpdate: Optional[OnboardMerchantUpdate] = None


class DispenseCashResponse(BaseModel):
    """Response returned when dispensing cash against a withdrawal code."""

    model_config = ConfigDict(extra="allow")

    responseCode: Optional[int] = None
    message: Optional[str] = None
    transactionId: Optional[str] = None
    agentCommission: Optional[float] = None
    customerName: Optional[str] = None
