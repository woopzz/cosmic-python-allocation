import datetime as dt
from typing import Optional
from dataclasses import dataclass


class Event:
    pass


@dataclass
class OutOfStock(Event):
    sku: str
