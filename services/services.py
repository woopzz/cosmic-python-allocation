import datetime as dt
from typing import Optional

from domain import model
from services import unit_of_work


class InvalidSku(Exception):
    pass

def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}

def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[dt.date],
    uow: unit_of_work.AbstractUnitOfWork,
) -> None:
    with uow:
        uow.batches.add(model.Batch(ref, sku, qty, eta))
        uow.commit()

def allocate(
    orderid: str, sku: str, qty: int,
    uow: unit_of_work.AbstractUnitOfWork,
) -> str:
    line = model.OrderLine(orderid, sku, qty)
    with uow:
        batches = uow.batches.list()

        if not is_valid_sku(line.sku, batches):
            raise InvalidSku(f'Invalid sku {line.sku}')

        batchref = model.allocate(line, batches)
        uow.commit()
        return batchref
