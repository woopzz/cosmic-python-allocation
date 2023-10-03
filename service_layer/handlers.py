from adapters import email
from domain import model, events, commands
from . import unit_of_work


class InvalidSku(Exception):
    pass

def is_valid_sku(sku, batches):
    return sku in {b.sku for b in batches}

def add_batch(command: commands.CreateBatch, uow: unit_of_work.AbstractUnitOfWork) -> None:
    with uow:
        product = uow.products.get(command.sku)
        if product is None:
            product = model.Product(command.sku, batches=[])
            uow.products.add(product)

        product.batches.append(model.Batch(command.ref, command.sku, command.qty, command.eta))
        uow.commit()

def change_batch_quantity(command: commands.ChangeBatchQuantity, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get_by_batchref(batchref=command.ref)
        product.change_batch_quantity(ref=command.ref, qty=command.qty)
        uow.commit()

def allocate(command: commands.Allocate, uow: unit_of_work.AbstractUnitOfWork) -> str:
    line = model.OrderLine(command.orderid, command.sku, command.qty)
    with uow:
        product = uow.products.get(command.sku)
        if product is None:
            raise InvalidSku(f'Invalid sku {line.sku}')

        batchref = product.allocate(line)
        uow.commit()
        return batchref

def send_out_of_stock_notification(event: events.OutOfStock, uow: unit_of_work.AbstractUnitOfWork):
    email.send_mail(f'Out of stock for {event.sku}')
