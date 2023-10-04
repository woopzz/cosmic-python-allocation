import inspect
from typing import Callable

from allocation.service_layer import unit_of_work, messagebus, handlers
from allocation.adapters import redis_event_publisher, orm

def bootstrap(
    start_orm: bool = True,
    uow: unit_of_work.AbstractUnitOfWork = unit_of_work.SqlAlchemyUnitOfWork(),
    publish: Callable = redis_event_publisher,
) -> messagebus.MessageBus:
    if start_orm:
        orm.start_mappers()

    deps = {
        'uow': uow,
        'publish': publish,
    }
    injected_event_handlers = {
        event_type: [inject_dependencies(x, deps) for x in event_handlers]
        for event_type, event_handlers in handlers.EVENT_HANDLERS.items()
    }
    injected_command_handlers = {
        command_type: inject_dependencies(command_handler, deps)
        for command_type, command_handler in handlers.COMMAND_HANDLERS.items()
    }

    return messagebus.MessageBus(
        uow=uow,
        event_handlers=injected_event_handlers,
        command_handlers=injected_command_handlers,
    )

def inject_dependencies(handler, all_dependencies):
    params = inspect.signature(handler).parameters
    dependencies = {name: dep for name, dep in all_dependencies.items() if name in params}
    return lambda message: handler(message, **dependencies)
