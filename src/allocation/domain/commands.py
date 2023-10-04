import datetime as dt
from typing import Optional
from dataclasses import dataclass


class Command:
    pass


@dataclass
class Allocate(Command):
    orderid: str
    sku: str
    qty: int


@dataclass
class CreateBatch(Command):
    ref: str
    sku: str
    qty: int
    eta: Optional[dt.date] = None


@dataclass
class ChangeBatchQuantity(Command):
    ref: str
    qty: int
