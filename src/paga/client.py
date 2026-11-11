"""Async client for the Paga Engine API."""

from __future__ import annotations

from typing import Any, Dict, List, Mapping, Optional

import httpx

from .auth import (
    ACCOUNT_BALANCE_HASH_FIELDS,
    AIRTIME_HASH_FIELDS,
    BILL_PAYMENT_HASH_FIELDS,
    DEFAULT_HASH_ALGORITHM,
    MONEY_TRANSFER_HASH_FIELDS,
    PAYMENT_REQUEST_HASH_FIELDS,
    PAYMENT_STATUS_HASH_FIELDS,
    REFUND_HASH_FIELDS,
    SUBSIDIARY_ACCOUNT_HASH_FIELDS,
    TRANSACTION_HISTORY_HASH_FIELDS,
    PagaAuth,
    generate_hash,
)
from .exceptions import PagaAPIError, PagaAuthenticationError, PagaRateLimitError
from .models import (
    AccountBalanceResponse,
    CheckoutVerifyChargeResponse,
    CollectPaymentRequestResponse,
    DepositToBankResponse,
    MerchantPaymentResponse,
    PagaResponse,
    PaymentStatusResponse,
    PurchaseResponse,
    RefundResponse,
    SubsidiaryAccountResponse,
    TransactionHistoryResponse,
)

DEFAULT_COLLECT_TEST_BASE_URL = "https://beta-collect.paga.com"
DEFAULT_COLLECT_LIVE_BASE_URL = "https://collect.paga.com"
DEFAULT_CHECKOUT_TEST_BASE_URL = "https://beta-checkout.paga.com"
DEFAULT_CHECKOUT_LIVE_BASE_URL = "https://checkout.paga.com"
DEFAULT_BUSINESS_TEST_BASE_URL = "https://beta.mypaga.com/paga-webservices/business-rest/secured"
DEFAULT_BUSINESS_LIVE_BASE_URL = "https://www.mypaga.com/paga-webservices/business-rest/secured"


class PagaClient:
    """Async-first client for the Paga Engine API.

    The client is intended to be used as an async context manager::

        async with PagaClient(
            public_id="...",
            credentials="...",
            hash_key="...",
        ) as client:
            payment = await client.create_payment({...})
            verified = await client.verify_charge({...})

    All operations return typed responses on success and raise
    :class:`PagaAPIError` (or subclasses) when Paga reports a failure.
    """

    def __init__(
        self,
        public_id: str,
        credentials: str,
        hash_key: str,
        *,
        environment: str = "test",
        base_url: Optional[str] = None,
        checkout_base_url: Optional[str] = None,
        business_base_url: Optional[str] = None,
        timeout: float = 30.0,
    ) -> None:
        if environment not in {"test", "live"}:
            raise ValueError("environment must be either 'test' or 'live'")

        self.public_id = public_id
        self.credentials = credentials
        self.hash_key = hash_key
        self.environment = environment
        self.base_url = base_url or (
            DEFAULT_COLLECT_TEST_BASE_URL if environment == "test" else DEFAULT_COLLECT_LIVE_BASE_URL
        )
        self.checkout_base_url = checkout_base_url or (
            DEFAULT_CHECKOUT_TEST_BASE_URL if environment == "test" else DEFAULT_CHECKOUT_LIVE_BASE_URL
        )
        self.business_base_url = business_base_url or (
            DEFAULT_BUSINESS_TEST_BASE_URL if environment == "test" else DEFAULT_BUSINESS_LIVE_BASE_URL
        )
        self.timeout = httpx.Timeout(timeout)
        self.auth = PagaAuth(public_id=public_id, credentials=credentials, hash_key=hash_key)
        self._http: Optional[httpx.AsyncClient] = None

    @property
    def baseUrl(self) -> str:
        """Base URL of the targeted Paga (collect) environment."""
        return self.base_url

    @property
    def checkoutBaseUrl(self) -> str:
        """Base URL of the targeted Paga (checkout) environment."""
        return self.checkout_base_url

    async def __aenter__(self) -> "PagaClient":
        self._http = httpx.AsyncClient(timeout=self.timeout)
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:  # noqa: ANN001, ANN002
        if self._http is not None:
            await self._http.aclose()
            self._http = None

    async def _ensure_client(self) -> httpx.AsyncClient:
        if self._http is None:
            self._http = httpx.AsyncClient(timeout=self.timeout)
        return self._http

    async def _request(
        self,
        method: str,
        path: str,
        payload: Optional[Mapping[str, Any]] = None,
        *,
        use_hash: bool = True,
        use_basic: bool = False,
        base_url: Optional[str] = None,
        hash_fields: Optional[tuple] = None,
        raise_on_error: bool = True,
    ) -> PagaResponse:
        """Execute a request against the Paga Engine API.

        Args:
            method: HTTP method (e.g. ``"POST"``, ``"GET"``).
            path: Endpoint path relative to the base URL
                (e.g. ``/paymentRequest``, ``/checkout/transaction/verify``).
            payload: Optional JSON request body.
            use_hash: Use Paga hash-based auth headers. Defaults to ``True``.
            use_basic: Use HTTP Basic auth (public key / secret key) instead of
                the header based auth. Defaults to ``False``.
            base_url: Override the target base URL. Defaults to the collect base URL.
            hash_fields: Ordered hash field paths used when computing the hash.

        Returns:
            The parsed :class:`PagaResponse`.

        Raises:
            PagaAuthenticationError: If Paga rejects the credentials.
            PagaAPIError: If the API responds with a failure.
        """
        target_base = (base_url or self.base_url).rstrip("/")
        url = f"{target_base}{path}"
        http = await self._ensure_client()

        auth = self.auth.basic_auth() if use_basic else None
        headers: Optional[Dict[str, str]] = None
        if use_basic:
            if use_hash and payload is not None:
                headers = {
                    "hash": generate_hash(
                        payload,
                        self.hash_key,
                        algorithm=DEFAULT_HASH_ALGORITHM,
                        fields=hash_fields or PAYMENT_REQUEST_HASH_FIELDS,
                    ),
                }
        elif use_hash and payload is not None:
            headers = self.auth.build_headers(payload, hash_fields=hash_fields)

        response = await http.request(
            method=method.upper(),
            url=url,
            json=dict(payload) if payload is not None else None,
            headers=headers,
            auth=auth,
        )

        if response.status_code in (401, 403):
            raise PagaAuthenticationError(
                f"Paga authentication failed with status {response.status_code}"
            )
        if response.status_code >= 400:
            raise self._to_api_error(response)

        body: Any = response.json() if response.content else {}
        result = PagaResponse.model_validate(body)
        if raise_on_error and not result.is_success:
            raise PagaAPIError(
                message=result.message or "Paga request failed",
                response_code=result.responseCode,
                payload=result,
            )
        return result

    def _to_api_error(self, response: httpx.Response) -> PagaAPIError:
        try:
            body: Any = response.json()
        except Exception:  # noqa: BLE001 - response may not be JSON
            body = {}

        message = body.get("message") if isinstance(body, dict) else None
        response_code = body.get("responseCode") if isinstance(body, dict) else None

        if response.status_code == 429:
            return PagaRateLimitError(
                message=message or "Paga rate limit exceeded",
                response_code=response_code if isinstance(response_code, int) else None,
                status_code=response.status_code,
                payload=body,
            )

        return PagaAPIError(
            message=message or f"Paga API returned status {response.status_code}",
            response_code=response_code if isinstance(response_code, int) else None,
            status_code=response.status_code,
            payload=body,
        )

    async def create_payment(
        self,
        *,
        reference_number: str,
        amount: float,
        payer_name: str,
        payer_phone_number: str,
        payee_name: str,
        currency: str = "NGN",
        payer_email: Optional[str] = None,
        call_back_url: Optional[str] = None,
        payment_methods: Optional[List[str]] = None,
        expiry_date_time_utc: Optional[str] = None,
        is_suppress_messages: bool = False,
        payer_collection_fee_share: float = 1,
        payee_collection_fee_share: float = 0,
    ) -> CollectPaymentRequestResponse:
        """Create a Paga payment request.

        Operation: Dynamic virtual account - Create a payment request.

        The customer pays via the payment methods supplied (e.g. bank transfer
        with a one-time Paga virtual account number). Paga sends a callback to
        the configured ``callBackUrl`` when the payment completes.

        Args:
            reference_number: Your unique payment request reference.
            amount: Amount to request, in the major currency unit.
            payer_name: Customer's name.
            payer_phone_number: Customer's phone number.
            payee_name: Your business name, shown to the customer.
            currency: Currency of the transaction. Defaults to ``"NGN"``.
            payer_email: Customer's email address. Optional.
            call_back_url: Where Paga sends the callback. Optional.
            payment_methods: Payment methods to accept. Defaults to
                ``["BANK_TRANSFER"]``.
            expiry_date_time_utc: When the request expires, in UTC. Optional.
            is_suppress_messages: Whether Paga should suppress emails/SMS. Defaults
                to ``False``.
            payer_collection_fee_share: Share of the fee the customer pays. Defaults
                to ``1``.
            payee_collection_fee_share: Share of the fee the business pays. Defaults
                to ``0``.

        Returns:
            The parsed :class:`CollectPaymentRequestResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "amount": amount,
            "currency": currency,
            "payer": {
                "name": payer_name,
                "phoneNumber": payer_phone_number,
            },
            "payee": {"name": payee_name},
            "payerCollectionFeeShare": payer_collection_fee_share,
            "payeeCollectionFeeShare": payee_collection_fee_share,
            "paymentMethods": payment_methods or ["BANK_TRANSFER"],
        }
        if payer_email is not None:
            payload["payer"]["email"] = payer_email
        if call_back_url is not None:
            payload["callBackUrl"] = call_back_url
        if expiry_date_time_utc is not None:
            payload["expiryDateTimeUTC"] = expiry_date_time_utc
        if is_suppress_messages:
            payload["isSuppressMessages"] = True

        response = await self._request(
            "POST",
            "/paymentRequest",
            payload,
            use_hash=True,
            use_basic=True,
        )
        return CollectPaymentRequestResponse.model_validate(response.model_dump())

    async def get_payment_status(self, *, reference_number: str) -> PaymentStatusResponse:
        """Check the status of a payment request.

        Operation: Dynamic virtual account - Check payment status.

        The outer ``statusCode`` only says whether the status request worked;
        the payment's own status is in ``data.statusCode``.

        Args:
            reference_number: The ``referenceNumber`` of the payment request.

        Returns:
            The parsed :class:`PaymentStatusResponse`.
        """
        response = await self._request(
            "POST",
            "/status",
            {"referenceNumber": reference_number},
            use_hash=True,
            use_basic=True,
            hash_fields=PAYMENT_STATUS_HASH_FIELDS,
        )
        return PaymentStatusResponse.model_validate(response.model_dump())

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
    ) -> TransactionHistoryResponse:
        """Get the business transaction history.

        Operation: Your business account - Get your transaction history.

        Returns every transaction on the business account between two dates:
        money in, money out and fees, up to 10,000 at a time.

        Args:
            reference_number: Your unique history reference.
            start_date_utc: Start of the range, in UTC.
            end_date_utc: End of the range, in UTC.

        Returns:
            The parsed :class:`TransactionHistoryResponse`.
        """
        response = await self._request(
            "POST",
            "/transactionHistory",
            {
                "referenceNumber": reference_number,
                "startDateUTC": start_date_utc,
                "endDateUTC": end_date_utc,
            },
            use_hash=True,
            use_basic=False,
            base_url=self.business_base_url,
            hash_fields=TRANSACTION_HISTORY_HASH_FIELDS,
        )
        return TransactionHistoryResponse.model_validate(response.model_dump())

    async def verify_charge(
        self,
        *,
        payment_reference: str,
        public_key: str,
        amount: float,
        currency: str = "NGN",
    ) -> CheckoutVerifyChargeResponse:
        """Verify a checkout charge.

        Confirms a Checkout payment from your server at any time using its
        ``paymentReference``. Uses HTTP Basic auth only.

        - ``status_code`` of ``0`` means paid.
        - ``status_code`` of ``2`` means pending.

        Args:
            payment_reference: The ``paymentReference`` of the charge to verify.
            public_key: The public key used for the checkout.
            amount: The amount to verify.
            currency: The currency of the charge. Defaults to ``"NGN"``.

        Returns:
            The parsed :class:`CheckoutVerifyChargeResponse`.
        """
        payload = {
            "paymentReference": payment_reference,
            "publicKey": public_key,
            "amount": amount,
            "currency": currency,
        }
        response = await self._request(
            "POST",
            "/checkout/transaction/verify",
            payload,
            use_hash=False,
            use_basic=True,
            base_url=self.checkout_base_url,
        )
        return CheckoutVerifyChargeResponse.model_validate(response.model_dump())

    async def refund_payment(
        self,
        *,
        reference_number: str,
        payment_request_reference: str,
        refund_amount: float,
        currency: str = "NGN",
        reason: Optional[str] = None,
    ) -> RefundResponse:
        """Refund or cancel a payment request.

        Operation: Refunds - Refund or cancel a payment request.

        Refunds a paid payment request in full or in part, or cancels one that
        has not been paid. Send one request per partial refund, each with its
        own ``reference_number``. Reusing a ``reference_number`` returns status
        code ``102`` and never refunds twice.

        Args:
            reference_number: Your unique reference for this refund.
            payment_request_reference: The ``reference_number`` of the original
                payment request.
            refund_amount: Amount to refund.
            currency: Transaction currency. Defaults to ``"NGN"``.
            reason: Optional refund reason.

        Returns:
            The parsed :class:`RefundResponse`.
        """
        payload: Dict[str, Any] = {
            "referenceNumber": reference_number,
            "paymentRequestReference": payment_request_reference,
            "refundAmount": refund_amount,
            "currency": currency,
        }
        if reason is not None:
            payload["reason"] = reason
        response = await self._request(
            "POST",
            "/refund/v2",
            payload,
            use_hash=True,
            use_basic=True,
            hash_fields=REFUND_HASH_FIELDS,
        )
        return RefundResponse.model_validate(response.model_dump())

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
    ) -> DepositToBankResponse:
        """Send money from the business balance to a bank account or Paga wallet.

        Operation: Money transfer - Send the money.

        Sends money from the business balance to a bank account, or to a Paga
        wallet (using Paga's UUID ``AAAAAAAA-AAAA-AAAA-AAAA-AAAAAAAAAAAA``).

        Args:
            reference_number: Your unique transfer reference.
            amount: Amount to send (e.g. ``"5000.00"``).
            destination_bank_uuid: The bank's UUID from get banks, or Paga's UUID
                for a wallet.
            destination_bank_account_number: Destination bank account number.
            currency: Transaction currency. Defaults to ``"NGN"``.
            remarks: Optional transfer remarks.
            status_callback_url: Where Paga notifies once the transfer is processed. Optional.

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
    ) -> MerchantPaymentResponse:
        """Pay a bill from the business balance.

        Operation: Bill payment - Pay the bill.

        Pays a bill from the business balance. There is no callback: decide on
        ``responseCode``. ``integrationStatus`` is for information only.

        Args:
            reference_number: Your unique bill payment reference.
            amount: Bill amount.
            merchant_account: The biller's UUID. From the biller lookup.
            merchant_reference_number: The customer's account / meter /
                smart card / account number at the biller.
            merchant_service: Optional chosen service code. Leave out for
                billers with no services.
            currency: Transaction currency. Defaults to ``"NGN"``.
            payment_channel: Optional payment channel.
            locale: Optional locale.

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
