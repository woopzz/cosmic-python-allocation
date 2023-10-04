from sqlalchemy.sql import text

from allocation.adapters import email, redis_event_publisher
from allocation.domain import model, events, commands
from allocation.service_layer import unit_of_work


class InvalidSku(Exception):
    pass

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

def reallocate(event: events.Deallocated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        product = uow.products.get(sku=event.sku)
        product.events.append(commands.Allocate(orderid=event.orderid, sku=event.sku, qty=event.qty))
        uow.commit()

def send_out_of_stock_notification(event: events.OutOfStock, uow: unit_of_work.AbstractUnitOfWork):
    email.send_mail(f'Out of stock for {event.sku}')

def publish_allocated_event(event: events.Allocated, uow: unit_of_work.AbstractUnitOfWork):
    redis_event_publisher.publish('line_allocated', event)

def add_allocation_to_read_model(event: events.Allocated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        sqlquery = '''
            INSERT INTO allocations_view (orderid, sku, batchref)
            VALUES (:orderid, :sku, :batchref)
        '''
        uow.session.execute(text(sqlquery), dict(orderid=event.orderid, sku=event.sku, batchref=event.batchref))
        uow.commit()

def remove_allocation_from_read_model(event: events.Deallocated, uow: unit_of_work.AbstractUnitOfWork):
    with uow:
        uow.session.execute(
            text('DELETE FROM allocations_view WHERE orderid = :orderid AND sku = :sku'),
            dict(orderid=event.orderid, sku=event.sku),
        )
        uow.commit()

EVENT_HANDLERS = {
    events.OutOfStock: [send_out_of_stock_notification],
    events.Allocated: [
        publish_allocated_event,
        add_allocation_to_read_model,
    ],
    events.Deallocated: [
        remove_allocation_from_read_model,
        reallocate,
    ],
}

COMMAND_HANDLERS = {
    commands.Allocate: allocate,
    commands.CreateBatch: add_batch,
    commands.ChangeBatchQuantity: change_batch_quantity,
}
