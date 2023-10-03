import datetime as dt
from typing import Optional
from dataclasses import dataclass


class Event:
    pass


@dataclass
class OutOfStock(Event):
    sku: str


@dataclass
class BatchCreated(Event):
    ref: str
    sku: str
    qty: int
    eta: Optional[dt.date] = None


@dataclass
class BatchQuantityChanged(Event):
    ref: str
    qty: int


@dataclass
class AllocationRequired(Event):
    orderid: str
    sku: str
    qty: int
