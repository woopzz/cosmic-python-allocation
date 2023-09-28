import datetime as dt
from typing import Optional, List, Set, Any
from dataclasses import dataclass


class OutOfStock(Exception):
    pass


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

def allocate(line: OrderLine, batches: List[Batch]) -> str:
    try:
        batch = next(x for x in sorted(batches) if x.can_allocate(line))
    except StopIteration:
        raise OutOfStock(f'SKU {line.sku} is out of stock')

    batch.allocate(line)
    return batch.reference
