"""Compatibility shim for the old, section-less layout.

The operations that used to live here are now split by the section of Paga's
documentation they belong to:

- :mod:`paga.money_transfer` — Money Transfer
- :mod:`paga.airtime` — Airtime and data
- :mod:`paga.bill_payment` — Bill payment (VAS)
- :mod:`paga.refunds` — Refunds
- :mod:`paga.status` — Check the transaction status

This module re-exports them so that ``from paga.actions import ...`` keeps
working. It will be removed in a future release.
"""

from __future__ import annotations

from .airtime import AirtimeMixin
from .bill_payment import BillPaymentMixin
from .money_transfer import MoneyTransferMixin
from .refunds import RefundsMixin
from .status import StatusMixin

__all__ = [
    "AirtimeMixin",
    "BillPaymentMixin",
    "MoneyTransferMixin",
    "RefundsMixin",
    "StatusMixin",
]
