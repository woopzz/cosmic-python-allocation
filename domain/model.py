import datetime as dt
from typing import Optional, List, Set, Any
from dataclasses import dataclass

from . import events, commands


@dataclass(unsafe_hash=True)
class OrderLine:
    orderid: str
    sku: str
    qty: int


class Batch:

    def __init__(self, ref: str, sku: str, qty: int, eta: Optional[dt.date]):
        self.reference = ref
        self.sku = sku
        self.eta = eta
        self._purchased_quantity = qty
        self._allocations: Set[OrderLine] = set()

    @property
    def allocated_qty(self) -> int:
        return sum(line.qty for line in self._allocations)

    @property
    def available_quantity(self) -> int:
        return self._purchased_quantity - self.allocated_qty

    def can_allocate(self, line: OrderLine):
        return (
            self.sku == line.sku and
            self.available_quantity >= line.qty
        )

    def allocate(self, line: OrderLine):
        if self.can_allocate(line):
            self._allocations.add(line)

    def deallocate(self, line: OrderLine):
        if line in self._allocations:
            self._allocations.remove(line)

    def deallocate_one(self) -> OrderLine:
        return self._allocations.pop()

    def __hash__(self):
        return hash(self.reference)

    def __eq__(self, other: Any):
        if not isinstance(other, Batch):
            return False
        return other.reference == self.reference

    def __gt__(self, other: Any):
        if self.eta is None:
            return False
        if other.eta is None:
            return True
        return self.eta > other.eta


class Product:

    def __init__(self, sku: str, batches: List[Batch], version_number: int = 0):
        self.sku = sku
        self.batches = batches
        self.version_number = version_number
        self.events = []

    def allocate(self, line: OrderLine) -> str | None:
        try:
            batch = next(x for x in sorted(self.batches) if x.can_allocate(line))
        except StopIteration:
            self.events.append(events.OutOfStock(line.sku))
            return None

        batch.allocate(line)
        self.version_number += 1
        return batch.reference

    def change_batch_quantity(self, ref: str, qty: int):
        batch = next(x for x in self.batches if x.reference == ref)
        batch._purchased_quantity = qty
        while batch.available_quantity < 0:
            line = batch.deallocate_one()
            self.events.append(commands.Allocate(line.orderid, line.sku, line.qty))
