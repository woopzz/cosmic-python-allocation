from adapters import email
from domain import model, events
from . import unit_of_work


class InvalidSku(Exception):
    pass

def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}

def add_batch(event: events.BatchCreated, uow: unit_of_work.AbstractUnitOfWork) -> None:
    with uow:
        product = uow.products.get(event.sku)
        if product is None:
            product = model.Product(event.sku, batches=[])
            uow.products.add(product)

        product.batches.append(model.Batch(event.ref, event.sku, event.qty, event.eta))
        uow.commit()

def change_batch_quantity(event: events.BatchQuantityChanged, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batchref(batchref=event.ref)
        product.change_batch_quantity(ref=event.ref, qty=event.qty)
        uow.commit()

def allocate(event: events.AllocationRequired, uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = model.OrderLine(event.orderid, event.sku, event.qty)
    with uow:
        product = uow.products.get(event.sku)
        if product is None:
            raise InvalidSku(f'Invalid sku {line.sku}')

        batchref = product.allocate(line)
        uow.commit()
        return batchref

def send_out_of_stock_notification(event: events.OutOfStock, uow: unit_of_work.AbstractUnitOfWork):
    email.send_mail(f'Out of stock for {event.sku}')
