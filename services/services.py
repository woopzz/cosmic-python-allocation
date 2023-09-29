import datetime as dt
from typing import Optional

from sqlalchemy.orm import Session

from domain import model
from adapters import repository


class InvalidSku(Exception):
    pass

def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}

def add_batch(
    ref: str, sku: str, qty: int, eta: Optional[dt.date],
    repo: repository.AbstractRepository, session: Session,
) -> None:
    repo.add(model.Batch(ref, sku, qty, eta))
    session.commit()

def allocate(
    orderid: str, sku: str, qty: int,
    repo: repository.AbstractRepository, session: Session,
):
    line = model.OrderLine(orderid, sku, qty)
    batches = repo.list()

    if not is_valid_sku(line.sku, batches):
        raise InvalidSku(f'Invalid sku {line.sku}')

    batchref = model.allocate(line, batches)
    session.commit()
    return batchref
