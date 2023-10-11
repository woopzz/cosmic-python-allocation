import json
import logging

import redis

from allocation import config, bootstrap
from allocation.domain import commands
from allocation.entrypoints import validation

r = redis.Redis(**config.get_redis_host_and_port())

def main():
    logging.info('Redis pub/sub starting')
    bus = bootstrap.bootstrap()
    pubsub = r.pubsub(ignore_subscribe_messages=True)
    pubsub.subscribe('change_batch_quantity')

    for m in pubsub.listen():
        handle_change_batch_quantity(m, bus)

def handle_change_batch_quantity(m, bus):
    logging.debug('Handling %s', m)

    try:
        data = json.loads(m['data'])
    except json.JSONDecodeError:
        logging.error('%s cannot be decoded', m)
        return

    try:
        change_batch_quantity_request = validation.ChangeBatchQuantity(**data)
    except validation.ValidationError as exc:
        logging.error(exc.errors())
        return

    bus.handle(commands.ChangeBatchQuantity(
        ref=change_batch_quantity_request.batchref,
        qty=change_batch_quantity_request.qty,
    ))

if __name__ == '__main__':
    main()
