import logging
from typing import Union, List

from domain import events, commands
from . import handlers, unit_of_work

Message = Union[events.Event, commands.Command]

logger = logging.getLogger(__name__)

def handle(message: Message, uow: unit_of_work.AbstractUnitOfWork):
    queue = [message]
    while queue:
        message = queue.pop(0)
        if isinstance(message, events.Event):
            handle_event(message, queue, uow)
        elif isinstance(message, commands.Command):
            handle_command(message, queue, uow)
        else:
            raise Exception(f'{message} was not an Event or Command')

def handle_event(event: events.Event, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
    for handler in EVENT_HANDLERS[type(event)]:
        try:
            logger.debug('Handling event %s with handler %s', event, handler)
            handler(event, uow)
            queue.extend(uow.collect_new_events())
        except Exception:
            logger.exception('Exception handling event %s', event)

def handle_command(command: commands.Command, queue: List[Message], uow: unit_of_work.AbstractUnitOfWork):
    logger.debug('Handling command %s', command)
    try:
        handler = COMMAND_HANDLERS[type(command)]
        handler(command, uow)
        queue.extend(uow.collect_new_events())
    except Exception:
        logger.exception('Exception handling command %s', command)
        raise

EVENT_HANDLERS = {
    events.OutOfStock: [handlers.send_out_of_stock_notification],
    events.Allocated: [
        handlers.publish_allocated_event,
        handlers.add_allocation_to_read_model,
    ],
    events.Deallocated: [
        handlers.remove_allocation_from_read_model,
        handlers.reallocate,
    ],
}

COMMAND_HANDLERS = {
    commands.Allocate: handlers.allocate,
    commands.CreateBatch: handlers.add_batch,
    commands.ChangeBatchQuantity: handlers.change_batch_quantity,
}
